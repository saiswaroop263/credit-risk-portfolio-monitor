# Credit Risk Portfolio Monitor - PRD

## Original Problem Statement
Build a full-stack web app called "Credit Risk Portfolio Monitor" for uploading CSV of loan applications, computing risk scores + portfolio KPIs, and showing dashboards + alerts.

## User Personas
1. **Data Analyst** - Reviews DQ reports, monitors drift, validates data quality
2. **Risk Manager** - Monitors portfolio KPIs, risk segments, makes credit decisions
3. **Data Engineer** - Manages ETL pipelines, model training, run history

## Core Requirements (Static)
- CSV upload for loan data
- ETL pipeline with data cleaning and feature engineering
- ML models (Logistic Regression + XGBoost) for credit risk scoring
- 10 Data Quality rules with pass/fail reporting
- PSI-based drift detection
- Dashboard with KPIs, charts, and risk segments
- Run history tracking

## What's Been Implemented (Feb 1, 2026)

### Backend
- [x] FastAPI server with MongoDB integration
- [x] 8 API endpoints: upload, demo, execute, runs, kpis, scores, dq, drift, models
- [x] ETL pipeline (etl.py) - clean, transform, feature engineering
- [x] 10 DQ rules (dq_rules.py) with unit tests
- [x] ML models (ml_models.py) - Logistic Regression + XGBoost
- [x] PSI drift detection (drift_detection.py)
- [x] Demo data generator (demo_data.py) - 1000 synthetic loans
- [x] MongoDB indexes for performance

### Frontend
- [x] Dashboard with 4 KPI cards, pie chart, bar chart
- [x] Risk Segments page with distribution and scores table
- [x] Model Performance page with metrics, radar chart, feature importance
- [x] DQ & Drift page with 10 rules table and PSI chart
- [x] Run History page with run details
- [x] Upload page with drag-drop interface
- [x] One-click Demo button

### Model Metrics (Honest - from training)
| Model | AUC-ROC | Precision | Recall | Accuracy |
|-------|---------|-----------|--------|----------|
| Logistic | 0.833 | 0.438 | 0.700 | 0.820 |
| Boosted | 0.779 | 0.625 | 0.167 | 0.860 |

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Core dashboard with KPIs
- [x] ETL + DQ pipeline
- [x] ML training and scoring
- [x] Demo functionality

### P1 (High Priority) - Future
- [ ] CSV upload flow E2E testing
- [ ] Model explainability (SHAP values)
- [ ] Alerting system for drift/DQ failures
- [ ] Date range filters

### P2 (Medium Priority) - Future
- [ ] Authentication and multi-tenant
- [ ] Real-time streaming for large uploads
- [ ] A/B testing framework
- [ ] Export reports to PDF

## Next Tasks
1. Test CSV upload with real data files
2. Add date range filters to dashboard
3. Implement alert notifications for drift detection
4. Add model comparison features
