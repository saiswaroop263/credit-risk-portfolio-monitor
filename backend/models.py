"""
MongoDB Models for Credit Risk Portfolio Monitor
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============== Loan Raw ==============
class LoanRaw(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    loan_id: str
    customer_id: str
    loan_amount: float
    interest_rate: float
    loan_term: int
    employment_length: Optional[float] = None
    home_ownership: Optional[str] = None
    annual_income: Optional[float] = None
    purpose: Optional[str] = None
    dti_ratio: Optional[float] = None
    delinq_2yrs: Optional[int] = None
    open_accounts: Optional[int] = None
    total_accounts: Optional[int] = None
    credit_history_length: Optional[int] = None
    loan_status: Optional[str] = None  # Target: 0=good, 1=default
    created_at: datetime = Field(default_factory=utc_now)


# ============== Customer ==============
class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    customer_id: str
    annual_income: Optional[float] = None
    employment_length: Optional[float] = None
    home_ownership: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


# ============== Loan Features ==============
class LoanFeatures(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    loan_id: str
    customer_id: str
    
    # Original features
    loan_amount: float
    interest_rate: float
    loan_term: int
    annual_income: float
    dti_ratio: float
    delinq_2yrs: int
    open_accounts: int
    total_accounts: int
    credit_history_length: int
    employment_length: float
    
    # Engineered features
    income_to_loan_ratio: float
    monthly_payment: float
    payment_to_income_ratio: float
    account_utilization: float
    
    # Encoded categoricals
    home_ownership_encoded: int
    purpose_encoded: int
    
    # Target
    target: Optional[int] = None
    created_at: datetime = Field(default_factory=utc_now)


# ============== Model Scores ==============
class ModelScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    loan_id: str
    customer_id: str
    
    logistic_score: float
    boosted_score: float
    ensemble_score: float
    risk_level: RiskLevel
    
    created_at: datetime = Field(default_factory=utc_now)


# ============== Portfolio KPIs ==============
class PortfolioKPIs(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    
    total_loans: int
    total_portfolio_value: float
    avg_loan_amount: float
    avg_interest_rate: float
    avg_risk_score: float
    
    default_rate: float
    predicted_default_rate: float
    
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    
    high_risk_exposure: float
    medium_risk_exposure: float
    low_risk_exposure: float
    
    created_at: datetime = Field(default_factory=utc_now)


# ============== DQ Audit ==============
class DQRuleResult(BaseModel):
    rule_id: str
    rule_name: str
    rule_description: str
    passed: bool
    total_records: int
    failed_records: int
    pass_rate: float
    failed_examples: List[Dict[str, Any]] = []


class DQAudit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    
    total_rules: int
    passed_rules: int
    failed_rules: int
    overall_pass_rate: float
    
    rules: List[DQRuleResult]
    
    created_at: datetime = Field(default_factory=utc_now)


# ============== Drift Report ==============
class FeatureDrift(BaseModel):
    feature_name: str
    psi_score: float
    drift_detected: bool
    baseline_distribution: List[float]
    current_distribution: List[float]


class DriftReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    
    total_features: int
    drifted_features: int
    overall_drift_detected: bool
    
    features: List[FeatureDrift]
    
    created_at: datetime = Field(default_factory=utc_now)


# ============== Model Metadata ==============
class ModelMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str
    model_type: str  # logistic, boosted
    model_version: str
    
    # Metrics
    auc_roc: float
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    
    # Feature importance
    feature_importance: Dict[str, float]
    
    # Model path
    model_path: str
    
    created_at: datetime = Field(default_factory=utc_now)


# ============== Pipeline Runs ==============
class RunStep(BaseModel):
    step_name: str
    status: RunStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PipelineRun(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_id)
    run_id: str = Field(default_factory=generate_id)
    
    status: RunStatus = RunStatus.PENDING
    
    # Counts
    raw_records: int = 0
    processed_records: int = 0
    
    # Steps
    steps: List[RunStep] = []
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Flags
    dq_passed: bool = False
    drift_detected: bool = False
    
    created_at: datetime = Field(default_factory=utc_now)


# ============== Request/Response Models ==============
class UploadResponse(BaseModel):
    run_id: str
    records_uploaded: int
    message: str


class ExecuteResponse(BaseModel):
    run_id: str
    status: str
    message: str


class DemoResponse(BaseModel):
    run_id: str
    message: str
    records_generated: int
