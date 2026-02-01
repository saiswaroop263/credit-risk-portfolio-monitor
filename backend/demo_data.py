"""
Demo Data Generator for Credit Risk Portfolio Monitor
Generates realistic synthetic loan data based on Home Credit dataset distributions
"""
import numpy as np
import pandas as pd
from typing import List, Dict
import uuid
from datetime import datetime, timezone, timedelta
import random


def generate_demo_data(n_records: int = 1000, default_rate: float = 0.15) -> pd.DataFrame:
    """
    Generate synthetic loan data with realistic distributions.
    Based on Home Credit dataset column structure.
    """
    np.random.seed(42)
    
    # Generate customer and loan IDs
    customer_ids = [f"CUST_{str(uuid.uuid4())[:8].upper()}" for _ in range(int(n_records * 0.7))]
    # Some customers have multiple loans
    customer_ids = random.choices(customer_ids, k=n_records)
    loan_ids = [f"LOAN_{str(uuid.uuid4())[:8].upper()}" for _ in range(n_records)]
    
    # Loan amounts - log-normal distribution centered around $15,000
    loan_amounts = np.random.lognormal(mean=9.6, sigma=0.8, size=n_records)
    loan_amounts = np.clip(loan_amounts, 1000, 500000).round(2)
    
    # Interest rates - normal distribution centered around 12%
    interest_rates = np.random.normal(loc=12, scale=4, size=n_records)
    interest_rates = np.clip(interest_rates, 3, 30).round(2)
    
    # Loan terms - standard terms
    loan_terms = np.random.choice([36, 60, 84, 120, 180], size=n_records, p=[0.35, 0.35, 0.15, 0.1, 0.05])
    
    # Annual income - log-normal distribution
    annual_incomes = np.random.lognormal(mean=10.8, sigma=0.6, size=n_records)
    annual_incomes = np.clip(annual_incomes, 20000, 500000).round(2)
    
    # Employment length - years
    employment_lengths = np.random.exponential(scale=5, size=n_records)
    employment_lengths = np.clip(employment_lengths, 0, 40).round(1)
    
    # Home ownership
    home_ownerships = np.random.choice(
        ['RENT', 'OWN', 'MORTGAGE', 'OTHER'],
        size=n_records,
        p=[0.35, 0.15, 0.45, 0.05]
    )
    
    # Loan purpose
    purposes = np.random.choice(
        ['debt_consolidation', 'credit_card', 'home_improvement', 'major_purchase',
         'small_business', 'car', 'medical', 'moving', 'vacation', 'other'],
        size=n_records,
        p=[0.35, 0.20, 0.15, 0.08, 0.05, 0.05, 0.04, 0.03, 0.02, 0.03]
    )
    
    # DTI ratio - debt-to-income
    dti_ratios = np.random.normal(loc=18, scale=8, size=n_records)
    dti_ratios = np.clip(dti_ratios, 0, 60).round(2)
    
    # Delinquencies in last 2 years
    delinq_2yrs = np.random.poisson(lam=0.3, size=n_records)
    delinq_2yrs = np.clip(delinq_2yrs, 0, 10)
    
    # Credit accounts
    total_accounts = np.random.poisson(lam=12, size=n_records)
    total_accounts = np.clip(total_accounts, 1, 50)
    
    open_accounts = np.array([
        min(np.random.poisson(lam=6), total)
        for total in total_accounts
    ])
    
    # Credit history length in months
    credit_history = np.random.normal(loc=180, scale=60, size=n_records)
    credit_history = np.clip(credit_history, 12, 500).astype(int)
    
    # Generate loan status (target) based on risk factors
    # Higher risk: high DTI, low income, high delinquencies, RENT
    risk_scores = (
        0.15 * (dti_ratios / 60) +
        0.20 * (1 - annual_incomes / 500000) +
        0.25 * (delinq_2yrs / 5) +
        0.15 * (loan_amounts / 500000) +
        0.10 * (interest_rates / 30) +
        0.05 * np.where(home_ownerships == 'RENT', 1, 0) +
        0.10 * (1 - employment_lengths / 40)
    )
    
    # Normalize and add noise
    risk_scores = (risk_scores - risk_scores.min()) / (risk_scores.max() - risk_scores.min())
    risk_scores += np.random.normal(0, 0.1, size=n_records)
    risk_scores = np.clip(risk_scores, 0, 1)
    
    # Determine default based on calibrated threshold
    threshold = np.percentile(risk_scores, 100 * (1 - default_rate))
    loan_status = (risk_scores >= threshold).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'loan_id': loan_ids,
        'customer_id': customer_ids,
        'loan_amount': loan_amounts,
        'interest_rate': interest_rates,
        'loan_term': loan_terms,
        'annual_income': annual_incomes,
        'employment_length': employment_lengths,
        'home_ownership': home_ownerships,
        'purpose': purposes,
        'dti_ratio': dti_ratios,
        'delinq_2yrs': delinq_2yrs,
        'open_accounts': open_accounts,
        'total_accounts': total_accounts,
        'credit_history_length': credit_history,
        'loan_status': loan_status
    })
    
    return df


def generate_drifted_data(n_records: int = 500) -> pd.DataFrame:
    """Generate data with drift for testing drift detection"""
    df = generate_demo_data(n_records, default_rate=0.20)
    
    # Introduce drift in some features
    df['loan_amount'] = df['loan_amount'] * 1.3  # Larger loans
    df['interest_rate'] = df['interest_rate'] + 2  # Higher rates
    df['dti_ratio'] = df['dti_ratio'] * 1.2  # Higher DTI
    
    return df


def get_sample_csv_content() -> str:
    """Get sample CSV content for documentation"""
    df = generate_demo_data(5)
    return df.to_csv(index=False)


if __name__ == "__main__":
    # Test data generation
    df = generate_demo_data(1000)
    print(f"Generated {len(df)} records")
    print(f"Default rate: {df['loan_status'].mean():.2%}")
    print(f"\nColumn types:\n{df.dtypes}")
    print(f"\nSample:\n{df.head()}")
