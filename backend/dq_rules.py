"""
Data Quality Rules for Credit Risk Portfolio Monitor
10 DQ rules covering nulls, ranges, duplicates, referential integrity, etc.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DQRuleResult:
    rule_id: str
    rule_name: str
    rule_description: str
    passed: bool
    total_records: int
    failed_records: int
    pass_rate: float
    failed_examples: List[Dict[str, Any]]


class DataQualityChecker:
    """Data Quality Checker with 10 rules"""
    
    def __init__(self, max_examples: int = 5):
        self.max_examples = max_examples
    
    def run_all_rules(self, df: pd.DataFrame) -> List[DQRuleResult]:
        """Run all DQ rules and return results"""
        rules = [
            self.rule_1_null_critical_fields,
            self.rule_2_loan_amount_range,
            self.rule_3_interest_rate_range,
            self.rule_4_duplicate_loan_ids,
            self.rule_5_valid_loan_term,
            self.rule_6_valid_home_ownership,
            self.rule_7_positive_income,
            self.rule_8_valid_dti_ratio,
            self.rule_9_valid_delinquency,
            self.rule_10_referential_integrity,
        ]
        
        results = []
        for rule_func in rules:
            try:
                result = rule_func(df)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running rule {rule_func.__name__}: {e}")
                results.append(DQRuleResult(
                    rule_id=rule_func.__name__,
                    rule_name="Error",
                    rule_description=str(e),
                    passed=False,
                    total_records=len(df),
                    failed_records=len(df),
                    pass_rate=0.0,
                    failed_examples=[]
                ))
        
        return results
    
    def _get_failed_examples(self, df: pd.DataFrame, mask: pd.Series) -> List[Dict[str, Any]]:
        """Get sample of failed records"""
        failed_df = df[mask].head(self.max_examples)
        # Convert to dict and handle any non-serializable types
        examples = []
        for _, row in failed_df.iterrows():
            example = {}
            for col in ['loan_id', 'customer_id', 'loan_amount', 'interest_rate']:
                if col in row.index:
                    val = row[col]
                    if pd.isna(val):
                        example[col] = None
                    elif isinstance(val, (np.integer, np.floating)):
                        example[col] = float(val)
                    else:
                        example[col] = str(val)
            examples.append(example)
        return examples
    
    # ============== Rule 1: Null Critical Fields ==============
    def rule_1_null_critical_fields(self, df: pd.DataFrame) -> DQRuleResult:
        """Check for null values in critical fields"""
        critical_fields = ['loan_id', 'customer_id', 'loan_amount', 'interest_rate', 'loan_term']
        
        mask = pd.Series([False] * len(df), index=df.index)
        for field in critical_fields:
            if field in df.columns:
                mask = mask | df[field].isna()
        
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ001",
            rule_name="Null Critical Fields",
            rule_description="Critical fields (loan_id, customer_id, loan_amount, interest_rate, loan_term) must not be null",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 2: Loan Amount Range ==============
    def rule_2_loan_amount_range(self, df: pd.DataFrame) -> DQRuleResult:
        """Check loan amount is within valid range (100 - 1,000,000)"""
        if 'loan_amount' not in df.columns:
            return DQRuleResult(
                rule_id="DQ002", rule_name="Loan Amount Range",
                rule_description="Loan amount must be between $100 and $1,000,000",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = (df['loan_amount'] < 100) | (df['loan_amount'] > 1000000) | df['loan_amount'].isna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ002",
            rule_name="Loan Amount Range",
            rule_description="Loan amount must be between $100 and $1,000,000",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 3: Interest Rate Range ==============
    def rule_3_interest_rate_range(self, df: pd.DataFrame) -> DQRuleResult:
        """Check interest rate is within valid range (0.1% - 50%)"""
        if 'interest_rate' not in df.columns:
            return DQRuleResult(
                rule_id="DQ003", rule_name="Interest Rate Range",
                rule_description="Interest rate must be between 0.1% and 50%",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = (df['interest_rate'] < 0.1) | (df['interest_rate'] > 50) | df['interest_rate'].isna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ003",
            rule_name="Interest Rate Range",
            rule_description="Interest rate must be between 0.1% and 50%",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 4: Duplicate Loan IDs ==============
    def rule_4_duplicate_loan_ids(self, df: pd.DataFrame) -> DQRuleResult:
        """Check for duplicate loan IDs"""
        if 'loan_id' not in df.columns:
            return DQRuleResult(
                rule_id="DQ004", rule_name="Duplicate Loan IDs",
                rule_description="Loan IDs must be unique",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        duplicates = df['loan_id'].duplicated(keep=False)
        failed_count = duplicates.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ004",
            rule_name="Duplicate Loan IDs",
            rule_description="Loan IDs must be unique",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, duplicates)
        )
    
    # ============== Rule 5: Valid Loan Term ==============
    def rule_5_valid_loan_term(self, df: pd.DataFrame) -> DQRuleResult:
        """Check loan term is valid (12, 24, 36, 48, 60, 72, 84 months)"""
        valid_terms = [12, 24, 36, 48, 60, 72, 84, 120, 180, 240, 360]
        
        if 'loan_term' not in df.columns:
            return DQRuleResult(
                rule_id="DQ005", rule_name="Valid Loan Term",
                rule_description="Loan term must be a standard term (12-360 months)",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = ~df['loan_term'].isin(valid_terms) & df['loan_term'].notna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ005",
            rule_name="Valid Loan Term",
            rule_description="Loan term must be a standard term (12-360 months)",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 6: Valid Home Ownership ==============
    def rule_6_valid_home_ownership(self, df: pd.DataFrame) -> DQRuleResult:
        """Check home ownership has valid values"""
        valid_values = ['RENT', 'OWN', 'MORTGAGE', 'OTHER', 'NONE']
        
        if 'home_ownership' not in df.columns:
            return DQRuleResult(
                rule_id="DQ006", rule_name="Valid Home Ownership",
                rule_description="Home ownership must be RENT, OWN, MORTGAGE, or OTHER",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = ~df['home_ownership'].str.upper().isin(valid_values) & df['home_ownership'].notna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ006",
            rule_name="Valid Home Ownership",
            rule_description="Home ownership must be RENT, OWN, MORTGAGE, or OTHER",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 7: Positive Income ==============
    def rule_7_positive_income(self, df: pd.DataFrame) -> DQRuleResult:
        """Check annual income is positive"""
        if 'annual_income' not in df.columns:
            return DQRuleResult(
                rule_id="DQ007", rule_name="Positive Income",
                rule_description="Annual income must be positive",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = (df['annual_income'] <= 0) & df['annual_income'].notna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ007",
            rule_name="Positive Income",
            rule_description="Annual income must be positive",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 8: Valid DTI Ratio ==============
    def rule_8_valid_dti_ratio(self, df: pd.DataFrame) -> DQRuleResult:
        """Check DTI ratio is within valid range (0-100%)"""
        if 'dti_ratio' not in df.columns:
            return DQRuleResult(
                rule_id="DQ008", rule_name="Valid DTI Ratio",
                rule_description="DTI ratio must be between 0% and 100%",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = ((df['dti_ratio'] < 0) | (df['dti_ratio'] > 100)) & df['dti_ratio'].notna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ008",
            rule_name="Valid DTI Ratio",
            rule_description="DTI ratio must be between 0% and 100%",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 9: Valid Delinquency ==============
    def rule_9_valid_delinquency(self, df: pd.DataFrame) -> DQRuleResult:
        """Check delinquency count is non-negative"""
        if 'delinq_2yrs' not in df.columns:
            return DQRuleResult(
                rule_id="DQ009", rule_name="Valid Delinquency",
                rule_description="Delinquency count must be non-negative",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = (df['delinq_2yrs'] < 0) & df['delinq_2yrs'].notna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ009",
            rule_name="Valid Delinquency",
            rule_description="Delinquency count must be non-negative",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )
    
    # ============== Rule 10: Referential Integrity ==============
    def rule_10_referential_integrity(self, df: pd.DataFrame) -> DQRuleResult:
        """Check open_accounts <= total_accounts"""
        if 'open_accounts' not in df.columns or 'total_accounts' not in df.columns:
            return DQRuleResult(
                rule_id="DQ010", rule_name="Referential Integrity",
                rule_description="Open accounts must not exceed total accounts",
                passed=True, total_records=len(df), failed_records=0,
                pass_rate=100.0, failed_examples=[]
            )
        
        mask = (df['open_accounts'] > df['total_accounts']) & df['open_accounts'].notna() & df['total_accounts'].notna()
        failed_count = mask.sum()
        total = len(df)
        pass_rate = ((total - failed_count) / total * 100) if total > 0 else 100.0
        
        return DQRuleResult(
            rule_id="DQ010",
            rule_name="Referential Integrity",
            rule_description="Open accounts must not exceed total accounts",
            passed=failed_count == 0,
            total_records=total,
            failed_records=int(failed_count),
            pass_rate=round(pass_rate, 2),
            failed_examples=self._get_failed_examples(df, mask)
        )


def run_data_quality_checks(df: pd.DataFrame) -> Tuple[List[DQRuleResult], bool]:
    """Run all DQ checks and return results with overall pass status"""
    checker = DataQualityChecker()
    results = checker.run_all_rules(df)
    
    # Overall pass if all critical rules pass
    critical_rules = ['DQ001', 'DQ002', 'DQ003', 'DQ004']
    overall_pass = all(
        r.passed for r in results if r.rule_id in critical_rules
    )
    
    return results, overall_pass
