"""
Drift Detection using Population Stability Index (PSI)
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)


def calculate_psi(baseline: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Population Stability Index (PSI) between baseline and current distributions.
    
    PSI < 0.1: No significant change
    0.1 <= PSI < 0.25: Moderate change, needs monitoring
    PSI >= 0.25: Significant change, action required
    """
    # Handle edge cases
    if len(baseline) == 0 or len(current) == 0:
        return 0.0
    
    # Remove NaN values
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]
    
    if len(baseline) == 0 or len(current) == 0:
        return 0.0
    
    # Create bins from baseline
    try:
        _, bin_edges = np.histogram(baseline, bins=bins)
    except Exception:
        return 0.0
    
    # Calculate percentages in each bin
    baseline_counts = np.histogram(baseline, bins=bin_edges)[0]
    current_counts = np.histogram(current, bins=bin_edges)[0]
    
    # Convert to percentages
    baseline_pct = baseline_counts / len(baseline)
    current_pct = current_counts / len(current)
    
    # Avoid division by zero and log(0)
    eps = 1e-6
    baseline_pct = np.clip(baseline_pct, eps, 1)
    current_pct = np.clip(current_pct, eps, 1)
    
    # Calculate PSI
    psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    
    return round(float(psi), 4)


def get_distribution_buckets(data: np.ndarray, bins: int = 10) -> List[float]:
    """Get distribution percentages for visualization"""
    if len(data) == 0:
        return [0.0] * bins
    
    data = data[~np.isnan(data)]
    if len(data) == 0:
        return [0.0] * bins
    
    counts, _ = np.histogram(data, bins=bins)
    percentages = (counts / len(data) * 100).tolist()
    return [round(p, 2) for p in percentages]


class DriftDetector:
    """Drift detection for credit risk features"""
    
    PSI_THRESHOLD = 0.25  # Significant drift threshold
    PSI_WARNING = 0.1     # Warning threshold
    
    FEATURE_COLUMNS = [
        'loan_amount', 'interest_rate', 'loan_term', 'annual_income',
        'dti_ratio', 'delinq_2yrs', 'open_accounts', 'total_accounts',
        'credit_history_length', 'employment_length'
    ]
    
    def __init__(self, baseline_data: pd.DataFrame = None):
        self.baseline_data = baseline_data
    
    def set_baseline(self, df: pd.DataFrame):
        """Set baseline distribution from data"""
        self.baseline_data = df.copy()
    
    def detect_drift(self, current_df: pd.DataFrame, baseline_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Detect drift between baseline and current data.
        Returns drift report with PSI scores for each feature.
        """
        if baseline_df is None:
            baseline_df = self.baseline_data
        
        if baseline_df is None:
            # If no baseline, use current data split in half for demo
            mid = len(current_df) // 2
            baseline_df = current_df.iloc[:mid]
            current_df = current_df.iloc[mid:]
        
        results = []
        overall_drift = False
        
        for feature in self.FEATURE_COLUMNS:
            if feature not in current_df.columns or feature not in baseline_df.columns:
                continue
            
            baseline_values = baseline_df[feature].values
            current_values = current_df[feature].values
            
            psi_score = calculate_psi(baseline_values, current_values)
            drift_detected = bool(psi_score >= self.PSI_THRESHOLD)
            
            if drift_detected:
                overall_drift = True
            
            results.append({
                "feature_name": feature,
                "psi_score": float(psi_score),
                "drift_detected": drift_detected,
                "baseline_distribution": get_distribution_buckets(baseline_values),
                "current_distribution": get_distribution_buckets(current_values),
                "status": "drift" if psi_score >= self.PSI_THRESHOLD else (
                    "warning" if psi_score >= self.PSI_WARNING else "stable"
                )
            })
        
        return {
            "total_features": len(results),
            "drifted_features": sum(1 for r in results if r["drift_detected"]),
            "overall_drift_detected": bool(overall_drift),
            "features": results
        }


def run_drift_detection(current_df: pd.DataFrame, baseline_df: pd.DataFrame = None) -> Dict[str, Any]:
    """Run drift detection and return report"""
    detector = DriftDetector()
    return detector.detect_drift(current_df, baseline_df)
