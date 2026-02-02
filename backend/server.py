"""
Credit Risk Portfolio Monitor - FastAPI Backend
"""
from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import pandas as pd
import io
import uuid

from models import (
    PipelineRun, RunStatus, RunStep, DQAudit, DQRuleResult,
    PortfolioKPIs, ModelScore, ModelMetadata, DriftReport,
    UploadResponse, ExecuteResponse, DemoResponse, RiskLevel
)
from etl import ETLPipeline
from dq_rules import run_data_quality_checks
from ml_models import train_and_score
from drift_detection import run_drift_detection
from demo_data import generate_demo_data

ROOT_DIR = Path(__file__).parent

# Load .env file for local development (won't override existing env vars)
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - read from environment variables
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'credit_risk_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Create the main app
app = FastAPI(title="Credit Risk Portfolio Monitor API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== Helper Functions ==============

def serialize_datetime(obj):
    """Convert datetime to ISO string for MongoDB"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def serialize_document(doc: dict) -> dict:
    """Serialize document for MongoDB storage"""
    result = {}
    for key, value in doc.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [
                serialize_document(item) if isinstance(item, dict) else serialize_datetime(item)
                for item in value
            ]
        elif isinstance(value, dict):
            result[key] = serialize_document(value)
        elif isinstance(value, RiskLevel):
            result[key] = value.value
        else:
            result[key] = value
    return result


async def create_indexes():
    """Create MongoDB indexes for performance"""
    # Runs collection
    await db.runs.create_index("run_id", unique=True)
    await db.runs.create_index("status")
    await db.runs.create_index("created_at")
    
    # Loans raw
    await db.loans_raw.create_index("run_id")
    await db.loans_raw.create_index("loan_id")
    await db.loans_raw.create_index([("run_id", 1), ("loan_id", 1)])
    
    # Customers
    await db.customers.create_index("run_id")
    await db.customers.create_index("customer_id")
    
    # Loan features
    await db.loan_features.create_index("run_id")
    await db.loan_features.create_index("loan_id")
    
    # Model scores
    await db.model_scores.create_index("run_id")
    await db.model_scores.create_index("loan_id")
    await db.model_scores.create_index("risk_level")
    
    # Portfolio KPIs
    await db.portfolio_kpis.create_index("run_id", unique=True)
    
    # DQ Audit
    await db.dq_audit.create_index("run_id", unique=True)
    
    # Drift reports
    await db.drift_reports.create_index("run_id", unique=True)
    
    # Model metadata
    await db.model_metadata.create_index("run_id")
    await db.model_metadata.create_index("model_type")
    
    logger.info("MongoDB indexes created")


@app.on_event("startup")
async def startup_event():
    """Initialize indexes on startup"""
    await create_indexes()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ============== API Endpoints ==============

@api_router.get("/")
async def root():
    return {"message": "Credit Risk Portfolio Monitor API", "version": "1.0.0"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ============== Upload Endpoint ==============

@api_router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """Upload CSV file and store raw loan data"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read CSV
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Validate required columns
        etl = ETLPipeline()
        valid, message = etl.validate_csv(df)
        if not valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Generate run_id
        run_id = str(uuid.uuid4())
        
        # Create run record
        run = PipelineRun(
            run_id=run_id,
            status=RunStatus.PENDING,
            raw_records=len(df),
            created_at=datetime.now(timezone.utc)
        )
        await db.runs.insert_one(serialize_document(run.model_dump()))
        
        # Store raw loans
        loans_raw = []
        for _, row in df.iterrows():
            loan_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    loan_doc[col] = None
                elif isinstance(val, (int, float)):
                    loan_doc[col] = float(val) if isinstance(val, float) else int(val)
                else:
                    loan_doc[col] = str(val)
            loans_raw.append(loan_doc)
        
        await db.loans_raw.insert_many(loans_raw)
        
        # Extract and store customers
        customers_df = etl.extract_customers(df)
        customers = []
        for _, row in customers_df.iterrows():
            customer_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "customer_id": str(row.get('customer_id', '')),
                "annual_income": float(row['annual_income']) if 'annual_income' in row and pd.notna(row['annual_income']) else None,
                "employment_length": float(row['employment_length']) if 'employment_length' in row and pd.notna(row['employment_length']) else None,
                "home_ownership": str(row['home_ownership']) if 'home_ownership' in row and pd.notna(row['home_ownership']) else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            customers.append(customer_doc)
        
        if customers:
            await db.customers.insert_many(customers)
        
        return UploadResponse(
            run_id=run_id,
            records_uploaded=len(df),
            message=f"Successfully uploaded {len(df)} loan records"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Execute Pipeline ==============

async def update_run_step(run_id: str, step_name: str, status: RunStatus, error: str = None):
    """Update run step status"""
    step = {
        "step_name": step_name,
        "status": status.value,
        "started_at": datetime.now(timezone.utc).isoformat() if status == RunStatus.RUNNING else None,
        "completed_at": datetime.now(timezone.utc).isoformat() if status in [RunStatus.COMPLETED, RunStatus.FAILED] else None,
        "error_message": error
    }
    
    await db.runs.update_one(
        {"run_id": run_id},
        {"$push": {"steps": step}}
    )


@api_router.post("/runs/{run_id}/execute", response_model=ExecuteResponse)
async def execute_pipeline(run_id: str):
    """Execute the full pipeline: ETL -> DQ -> Features -> Train -> Score -> KPIs -> Drift"""
    
    # Check run exists
    run = await db.runs.find_one({"run_id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.get("status") == RunStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Pipeline already executed")
    
    try:
        # Update status to running
        await db.runs.update_one(
            {"run_id": run_id},
            {"$set": {"status": RunStatus.RUNNING.value, "started_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Step 1: Load raw data
        await update_run_step(run_id, "load_data", RunStatus.RUNNING)
        raw_loans = await db.loans_raw.find({"run_id": run_id}, {"_id": 0}).to_list(100000)
        df = pd.DataFrame(raw_loans)
        await update_run_step(run_id, "load_data", RunStatus.COMPLETED)
        
        # Step 2: Clean data
        await update_run_step(run_id, "clean_data", RunStatus.RUNNING)
        etl = ETLPipeline()
        df_cleaned = etl.clean_data(df)
        await update_run_step(run_id, "clean_data", RunStatus.COMPLETED)
        
        # Step 3: Run DQ checks
        await update_run_step(run_id, "dq_checks", RunStatus.RUNNING)
        dq_results, dq_passed = run_data_quality_checks(df_cleaned)
        
        dq_audit = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "total_rules": len(dq_results),
            "passed_rules": sum(1 for r in dq_results if r.passed),
            "failed_rules": sum(1 for r in dq_results if not r.passed),
            "overall_pass_rate": round(sum(1 for r in dq_results if r.passed) / len(dq_results) * 100, 2),
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "rule_description": r.rule_description,
                    "passed": bool(r.passed),
                    "total_records": int(r.total_records),
                    "failed_records": int(r.failed_records),
                    "pass_rate": float(r.pass_rate),
                    "failed_examples": r.failed_examples
                }
                for r in dq_results
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.dq_audit.insert_one(dq_audit)
        await update_run_step(run_id, "dq_checks", RunStatus.COMPLETED)
        
        # Step 4: Create features
        await update_run_step(run_id, "create_features", RunStatus.RUNNING)
        df_features = etl.create_features(df_cleaned)
        
        # Store loan features
        features_docs = []
        for _, row in df_features.iterrows():
            feature_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "loan_id": str(row.get('loan_id', '')),
                "customer_id": str(row.get('customer_id', '')),
                "loan_amount": float(row['loan_amount']),
                "interest_rate": float(row['interest_rate']),
                "loan_term": int(row['loan_term']),
                "annual_income": float(row['annual_income']),
                "dti_ratio": float(row['dti_ratio']),
                "delinq_2yrs": int(row['delinq_2yrs']),
                "open_accounts": int(row['open_accounts']),
                "total_accounts": int(row['total_accounts']),
                "credit_history_length": int(row['credit_history_length']),
                "employment_length": float(row['employment_length']),
                "income_to_loan_ratio": float(row['income_to_loan_ratio']),
                "monthly_payment": float(row['monthly_payment']),
                "payment_to_income_ratio": float(row['payment_to_income_ratio']),
                "account_utilization": float(row['account_utilization']),
                "home_ownership_encoded": int(row['home_ownership_encoded']),
                "purpose_encoded": int(row['purpose_encoded']),
                "target": int(row['loan_status']) if 'loan_status' in row and pd.notna(row['loan_status']) else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            features_docs.append(feature_doc)
        
        await db.loan_features.insert_many(features_docs)
        await update_run_step(run_id, "create_features", RunStatus.COMPLETED)
        
        # Step 5: Train models
        await update_run_step(run_id, "train_models", RunStatus.RUNNING)
        X, y = etl.prepare_for_training(df_features)
        model_metrics, scores_df = train_and_score(X, y, run_id)
        
        # Store model metadata
        for model_type in ['logistic', 'boosted']:
            metrics = model_metrics[model_type]
            model_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "model_type": model_type,
                "model_version": "1.0",
                "auc_roc": metrics['auc_roc'],
                "precision": metrics['precision'],
                "recall": metrics['recall'],
                "f1_score": metrics['f1_score'],
                "accuracy": metrics['accuracy'],
                "feature_importance": metrics['feature_importance'],
                "model_path": metrics['model_path'],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.model_metadata.insert_one(model_doc)
        
        await update_run_step(run_id, "train_models", RunStatus.COMPLETED)
        
        # Step 6: Score loans
        await update_run_step(run_id, "score_loans", RunStatus.RUNNING)
        scores_df['loan_id'] = df_features['loan_id'].values
        scores_df['customer_id'] = df_features['customer_id'].values
        
        score_docs = []
        for _, row in scores_df.iterrows():
            score_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "loan_id": str(row['loan_id']),
                "customer_id": str(row['customer_id']),
                "logistic_score": round(float(row['logistic_score']), 4),
                "boosted_score": round(float(row['boosted_score']), 4),
                "ensemble_score": round(float(row['ensemble_score']), 4),
                "risk_level": str(row['risk_level']),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            score_docs.append(score_doc)
        
        await db.model_scores.insert_many(score_docs)
        await update_run_step(run_id, "score_loans", RunStatus.COMPLETED)
        
        # Step 7: Calculate KPIs
        await update_run_step(run_id, "calculate_kpis", RunStatus.RUNNING)
        
        risk_counts = scores_df['risk_level'].value_counts()
        
        kpi_doc = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "total_loans": len(df_features),
            "total_portfolio_value": round(float(df_features['loan_amount'].sum()), 2),
            "avg_loan_amount": round(float(df_features['loan_amount'].mean()), 2),
            "avg_interest_rate": round(float(df_features['interest_rate'].mean()), 2),
            "avg_risk_score": round(float(scores_df['ensemble_score'].mean()), 4),
            "default_rate": round(float(df_features['loan_status'].mean() if 'loan_status' in df_features.columns else 0), 4),
            "predicted_default_rate": round(float((scores_df['risk_level'] == 'high').mean()), 4),
            "high_risk_count": int(risk_counts.get('high', 0)),
            "medium_risk_count": int(risk_counts.get('medium', 0)),
            "low_risk_count": int(risk_counts.get('low', 0)),
            "high_risk_exposure": round(float(df_features.loc[scores_df['risk_level'] == 'high', 'loan_amount'].sum()), 2),
            "medium_risk_exposure": round(float(df_features.loc[scores_df['risk_level'] == 'medium', 'loan_amount'].sum()), 2),
            "low_risk_exposure": round(float(df_features.loc[scores_df['risk_level'] == 'low', 'loan_amount'].sum()), 2),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.portfolio_kpis.insert_one(kpi_doc)
        await update_run_step(run_id, "calculate_kpis", RunStatus.COMPLETED)
        
        # Step 8: Drift detection
        await update_run_step(run_id, "drift_detection", RunStatus.RUNNING)
        drift_result = run_drift_detection(df_features)
        
        drift_doc = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "total_features": drift_result['total_features'],
            "drifted_features": drift_result['drifted_features'],
            "overall_drift_detected": drift_result['overall_drift_detected'],
            "features": drift_result['features'],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.drift_reports.insert_one(drift_doc)
        await update_run_step(run_id, "drift_detection", RunStatus.COMPLETED)
        
        # Update run as completed
        await db.runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": RunStatus.COMPLETED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "processed_records": len(df_features),
                    "dq_passed": bool(dq_passed),
                    "drift_detected": bool(drift_result['overall_drift_detected'])
                }
            }
        )
        
        return ExecuteResponse(
            run_id=run_id,
            status="completed",
            message=f"Pipeline completed. Processed {len(df_features)} loans."
        )
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        await db.runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": RunStatus.FAILED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============== Demo Endpoint ==============

@api_router.post("/demo", response_model=DemoResponse)
async def run_demo():
    """Generate demo data and run the full pipeline"""
    try:
        # Generate demo data
        df = generate_demo_data(1000)
        
        # Create run_id
        run_id = str(uuid.uuid4())
        
        # Create run record
        run = PipelineRun(
            run_id=run_id,
            status=RunStatus.PENDING,
            raw_records=len(df),
            created_at=datetime.now(timezone.utc)
        )
        await db.runs.insert_one(serialize_document(run.model_dump()))
        
        # Store raw loans
        loans_raw = []
        for _, row in df.iterrows():
            loan_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    loan_doc[col] = None
                elif isinstance(val, (int, float)):
                    loan_doc[col] = float(val) if isinstance(val, float) else int(val)
                else:
                    loan_doc[col] = str(val)
            loans_raw.append(loan_doc)
        
        await db.loans_raw.insert_many(loans_raw)
        
        # Extract and store customers
        etl = ETLPipeline()
        customers_df = etl.extract_customers(df)
        customers = []
        for _, row in customers_df.iterrows():
            customer_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "customer_id": str(row.get('customer_id', '')),
                "annual_income": float(row['annual_income']) if 'annual_income' in row and pd.notna(row['annual_income']) else None,
                "employment_length": float(row['employment_length']) if 'employment_length' in row and pd.notna(row['employment_length']) else None,
                "home_ownership": str(row['home_ownership']) if 'home_ownership' in row and pd.notna(row['home_ownership']) else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            customers.append(customer_doc)
        
        if customers:
            await db.customers.insert_many(customers)
        
        # Execute pipeline
        exec_response = await execute_pipeline(run_id)
        
        return DemoResponse(
            run_id=run_id,
            message=f"Demo completed successfully. {exec_response.message}",
            records_generated=len(df)
        )
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== GET Endpoints ==============

@api_router.get("/runs")
async def get_runs(limit: int = 50, status: Optional[str] = None):
    """Get all pipeline runs"""
    query = {}
    if status:
        query["status"] = status
    
    runs = await db.runs.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"runs": runs, "total": len(runs)}


@api_router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get specific run details"""
    run = await db.runs.find_one({"run_id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@api_router.get("/kpis")
async def get_kpis(run_id: Optional[str] = None):
    """Get portfolio KPIs"""
    if run_id:
        kpis = await db.portfolio_kpis.find_one({"run_id": run_id}, {"_id": 0})
        if not kpis:
            raise HTTPException(status_code=404, detail="KPIs not found for this run")
        return kpis
    
    # Get latest KPIs
    kpis = await db.portfolio_kpis.find({}, {"_id": 0}).sort("created_at", -1).to_list(1)
    if not kpis:
        return {"message": "No KPIs available. Run the pipeline first."}
    return kpis[0]


@api_router.get("/scores")
async def get_scores(run_id: Optional[str] = None, risk_level: Optional[str] = None, limit: int = 100):
    """Get model scores"""
    query = {}
    if run_id:
        query["run_id"] = run_id
    if risk_level:
        query["risk_level"] = risk_level
    
    scores = await db.model_scores.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return {"scores": scores, "total": len(scores)}


@api_router.get("/dq")
async def get_dq_report(run_id: Optional[str] = None):
    """Get data quality report"""
    if run_id:
        dq = await db.dq_audit.find_one({"run_id": run_id}, {"_id": 0})
        if not dq:
            raise HTTPException(status_code=404, detail="DQ report not found for this run")
        return dq
    
    # Get latest DQ report
    dq = await db.dq_audit.find({}, {"_id": 0}).sort("created_at", -1).to_list(1)
    if not dq:
        return {"message": "No DQ reports available. Run the pipeline first."}
    return dq[0]


@api_router.get("/drift")
async def get_drift_report(run_id: Optional[str] = None):
    """Get drift detection report"""
    if run_id:
        drift = await db.drift_reports.find_one({"run_id": run_id}, {"_id": 0})
        if not drift:
            raise HTTPException(status_code=404, detail="Drift report not found for this run")
        return drift
    
    # Get latest drift report
    drift = await db.drift_reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(1)
    if not drift:
        return {"message": "No drift reports available. Run the pipeline first."}
    return drift[0]


@api_router.get("/models")
async def get_model_metadata(run_id: Optional[str] = None):
    """Get model metadata and performance metrics"""
    query = {}
    if run_id:
        query["run_id"] = run_id
    
    models = await db.model_metadata.find(query, {"_id": 0}).sort("created_at", -1).to_list(10)
    return {"models": models, "total": len(models)}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
