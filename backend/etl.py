"""
ETL Pipeline for Credit Risk Portfolio Monitor
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL Pipeline for processing loan data"""
    
    # Encoding maps
    HOME_OWNERSHIP_MAP = {
        'RENT': 0, 'OWN': 1, 'MORTGAGE': 2, 'OTHER': 3
    }
    
    PURPOSE_MAP = {
        'debt_consolidation': 0, 'credit_card': 1, 'home_improvement': 2,
        'major_purchase': 3, 'small_business': 4, 'car': 5, 'medical': 6,
        'moving': 7, 'vacation': 8, 'house': 9, 'wedding': 10, 'other': 11
    }
    
    REQUIRED_COLUMNS = [
        'loan_id', 'customer_id', 'loan_amount', 'interest_rate', 'loan_term'
    ]
    
    def __init__(self):
        self.stats = {}
    
    def validate_csv(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate that CSV has required columns"""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            return False, f"Missing required columns: {missing}"
        return True, "Validation passed"
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data"""
        df = df.copy()
        
        # Convert numeric columns
        numeric_cols = ['loan_amount', 'interest_rate', 'loan_term', 'annual_income',
                       'dti_ratio', 'delinq_2yrs', 'open_accounts', 'total_accounts',
                       'credit_history_length', 'employment_length']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Standardize categorical columns
        if 'home_ownership' in df.columns:
            df['home_ownership'] = df['home_ownership'].str.upper().str.strip()
        
        if 'purpose' in df.columns:
            df['purpose'] = df['purpose'].str.lower().str.strip()
        
        # Fill missing values with sensible defaults
        default_values = {
            'annual_income': df['annual_income'].median() if 'annual_income' in df.columns else 50000,
            'employment_length': 5.0,
            'dti_ratio': 15.0,
            'delinq_2yrs': 0,
            'open_accounts': 5,
            'total_accounts': 10,
            'credit_history_length': 120,
            'home_ownership': 'OTHER',
            'purpose': 'other'
        }
        
        for col, default in default_values.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)
        
        return df
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for ML model"""
        df = df.copy()
        
        # Income to loan ratio
        df['income_to_loan_ratio'] = np.where(
            df['loan_amount'] > 0,
            df['annual_income'] / df['loan_amount'],
            0
        )
        
        # Monthly payment (simplified amortization)
        monthly_rate = df['interest_rate'] / 100 / 12
        n_payments = df['loan_term']
        df['monthly_payment'] = np.where(
            monthly_rate > 0,
            df['loan_amount'] * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1),
            df['loan_amount'] / n_payments
        )
        
        # Payment to income ratio (annual)
        df['payment_to_income_ratio'] = np.where(
            df['annual_income'] > 0,
            (df['monthly_payment'] * 12) / df['annual_income'],
            0
        )
        
        # Account utilization
        df['account_utilization'] = np.where(
            df['total_accounts'] > 0,
            df['open_accounts'] / df['total_accounts'],
            0
        )
        
        # Encode categoricals
        df['home_ownership_encoded'] = df['home_ownership'].map(self.HOME_OWNERSHIP_MAP).fillna(3).astype(int)
        df['purpose_encoded'] = df['purpose'].map(self.PURPOSE_MAP).fillna(11).astype(int)
        
        # Clip extreme values
        df['income_to_loan_ratio'] = df['income_to_loan_ratio'].clip(0, 100)
        df['payment_to_income_ratio'] = df['payment_to_income_ratio'].clip(0, 1)
        df['account_utilization'] = df['account_utilization'].clip(0, 1)
        
        return df
    
    def extract_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract unique customer records"""
        customer_cols = ['customer_id', 'annual_income', 'employment_length', 'home_ownership']
        existing_cols = [col for col in customer_cols if col in df.columns]
        
        customers = df[existing_cols].drop_duplicates(subset=['customer_id'])
        return customers
    
    def prepare_for_training(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare feature matrix and target for ML"""
        feature_cols = [
            'loan_amount', 'interest_rate', 'loan_term', 'annual_income',
            'dti_ratio', 'delinq_2yrs', 'open_accounts', 'total_accounts',
            'credit_history_length', 'employment_length',
            'income_to_loan_ratio', 'monthly_payment', 'payment_to_income_ratio',
            'account_utilization', 'home_ownership_encoded', 'purpose_encoded'
        ]
        
        X = df[feature_cols].copy()
        
        # Handle any remaining NaN values
        X = X.fillna(X.median())
        
        # Target variable
        if 'loan_status' in df.columns:
            y = df['loan_status'].fillna(0).astype(int)
        else:
            y = pd.Series([0] * len(df))
        
        return X, y
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names used in training"""
        return [
            'loan_amount', 'interest_rate', 'loan_term', 'annual_income',
            'dti_ratio', 'delinq_2yrs', 'open_accounts', 'total_accounts',
            'credit_history_length', 'employment_length',
            'income_to_loan_ratio', 'monthly_payment', 'payment_to_income_ratio',
            'account_utilization', 'home_ownership_encoded', 'purpose_encoded'
        ]
