"""
ML Models for Credit Risk Scoring
Logistic Regression + XGBoost (fallback to HistGradientBoosting)
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any, List
import logging
import joblib
import os
from pathlib import Path
from datetime import datetime, timezone

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score, accuracy_score
)
from sklearn.preprocessing import StandardScaler

# Try XGBoost, fallback to sklearn HistGradientBoosting
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import HistGradientBoostingClassifier
    XGBOOST_AVAILABLE = False

logger = logging.getLogger(__name__)

# Model storage directory
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)


class CreditRiskModels:
    """Credit Risk Model Training and Scoring"""
    
    def __init__(self):
        self.logistic_model = None
        self.boosted_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def train(self, X: pd.DataFrame, y: pd.Series, run_id: str) -> Dict[str, Any]:
        """Train both models and return metrics"""
        self.feature_names = list(X.columns)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Logistic Regression
        logger.info("Training Logistic Regression...")
        self.logistic_model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        )
        self.logistic_model.fit(X_train, y_train)
        logistic_metrics = self._calculate_metrics(
            self.logistic_model, X_test, y_test, "logistic"
        )
        
        # Train Boosted Model
        logger.info("Training Boosted Model...")
        if XGBOOST_AVAILABLE:
            self.boosted_model = XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        else:
            self.boosted_model = HistGradientBoostingClassifier(
                max_iter=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        self.boosted_model.fit(X_train, y_train)
        boosted_metrics = self._calculate_metrics(
            self.boosted_model, X_test, y_test, "boosted"
        )
        
        # Save models
        model_paths = self._save_models(run_id)
        
        # Calculate feature importance
        logistic_importance = self._get_logistic_importance()
        boosted_importance = self._get_boosted_importance()
        
        return {
            "logistic": {
                **logistic_metrics,
                "feature_importance": logistic_importance,
                "model_path": model_paths["logistic"],
                "model_type": "LogisticRegression"
            },
            "boosted": {
                **boosted_metrics,
                "feature_importance": boosted_importance,
                "model_path": model_paths["boosted"],
                "model_type": "XGBClassifier" if XGBOOST_AVAILABLE else "HistGradientBoostingClassifier"
            }
        }
    
    def _calculate_metrics(self, model, X_test, y_test, model_name: str) -> Dict[str, float]:
        """Calculate model performance metrics"""
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        # Handle edge case where all predictions are same class
        try:
            auc = roc_auc_score(y_test, y_proba)
        except ValueError:
            auc = 0.5
        
        return {
            "auc_roc": round(auc, 4),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
            "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
            "accuracy": round(accuracy_score(y_test, y_pred), 4)
        }
    
    def _get_logistic_importance(self) -> Dict[str, float]:
        """Get feature importance from logistic regression coefficients"""
        if self.logistic_model is None:
            return {}
        
        coefs = np.abs(self.logistic_model.coef_[0])
        importance = coefs / coefs.sum()
        
        return {
            name: round(float(imp), 4)
            for name, imp in zip(self.feature_names, importance)
        }
    
    def _get_boosted_importance(self) -> Dict[str, float]:
        """Get feature importance from boosted model"""
        if self.boosted_model is None:
            return {}
        
        if XGBOOST_AVAILABLE:
            importance = self.boosted_model.feature_importances_
        else:
            importance = self.boosted_model.feature_importances_
        
        return {
            name: round(float(imp), 4)
            for name, imp in zip(self.feature_names, importance)
        }
    
    def _save_models(self, run_id: str) -> Dict[str, str]:
        """Save models to disk"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        logistic_path = str(MODEL_DIR / f"logistic_{run_id}_{timestamp}.joblib")
        boosted_path = str(MODEL_DIR / f"boosted_{run_id}_{timestamp}.joblib")
        scaler_path = str(MODEL_DIR / f"scaler_{run_id}_{timestamp}.joblib")
        
        joblib.dump(self.logistic_model, logistic_path)
        joblib.dump(self.boosted_model, boosted_path)
        joblib.dump(self.scaler, scaler_path)
        
        return {
            "logistic": logistic_path,
            "boosted": boosted_path,
            "scaler": scaler_path
        }
    
    def score(self, X: pd.DataFrame) -> pd.DataFrame:
        """Score loans with both models"""
        if self.logistic_model is None or self.boosted_model is None:
            raise ValueError("Models not trained. Call train() first.")
        
        # Ensure column order matches training
        X = X[self.feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get probabilities
        logistic_proba = self.logistic_model.predict_proba(X_scaled)[:, 1]
        boosted_proba = self.boosted_model.predict_proba(X_scaled)[:, 1]
        
        # Ensemble (average)
        ensemble_proba = (logistic_proba + boosted_proba) / 2
        
        # Create result DataFrame
        scores = pd.DataFrame({
            'logistic_score': logistic_proba,
            'boosted_score': boosted_proba,
            'ensemble_score': ensemble_proba
        })
        
        # Assign risk levels
        scores['risk_level'] = pd.cut(
            scores['ensemble_score'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['low', 'medium', 'high']
        )
        
        return scores
    
    def load_models(self, logistic_path: str, boosted_path: str, scaler_path: str):
        """Load models from disk"""
        self.logistic_model = joblib.load(logistic_path)
        self.boosted_model = joblib.load(boosted_path)
        self.scaler = joblib.load(scaler_path)


def train_and_score(X: pd.DataFrame, y: pd.Series, run_id: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Train models and score the data"""
    models = CreditRiskModels()
    metrics = models.train(X, y, run_id)
    scores = models.score(X)
    return metrics, scores
