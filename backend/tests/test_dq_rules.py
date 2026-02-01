"""
Unit Tests for Data Quality Rules
"""
import pytest
import pandas as pd
import numpy as np
from dq_rules import DataQualityChecker, run_data_quality_checks


@pytest.fixture
def valid_df():
    """Create a valid test DataFrame"""
    return pd.DataFrame({
        'loan_id': ['L001', 'L002', 'L003', 'L004', 'L005'],
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'loan_amount': [10000, 25000, 50000, 75000, 100000],
        'interest_rate': [5.5, 8.0, 12.5, 15.0, 18.5],
        'loan_term': [36, 60, 36, 60, 84],
        'annual_income': [50000, 75000, 100000, 125000, 150000],
        'employment_length': [2.0, 5.0, 10.0, 15.0, 20.0],
        'home_ownership': ['RENT', 'OWN', 'MORTGAGE', 'RENT', 'OWN'],
        'dti_ratio': [15.0, 20.0, 25.0, 30.0, 35.0],
        'delinq_2yrs': [0, 0, 1, 0, 2],
        'open_accounts': [3, 5, 7, 4, 6],
        'total_accounts': [5, 8, 10, 6, 9]
    })


@pytest.fixture
def invalid_df():
    """Create a DataFrame with various issues"""
    return pd.DataFrame({
        'loan_id': ['L001', 'L001', None, 'L004', 'L005'],  # Duplicate and null
        'customer_id': ['C001', 'C002', 'C003', None, 'C005'],  # Null
        'loan_amount': [50, 25000, 2000000, 75000, None],  # Out of range
        'interest_rate': [0.05, 8.0, 55.0, 15.0, None],  # Out of range
        'loan_term': [36, 60, 45, 60, 84],  # Invalid term (45)
        'annual_income': [-5000, 75000, 100000, 0, 150000],  # Negative and zero
        'employment_length': [2.0, 5.0, 10.0, 15.0, 20.0],
        'home_ownership': ['RENT', 'INVALID', 'MORTGAGE', 'RENT', 'OWN'],
        'dti_ratio': [-10.0, 20.0, 150.0, 30.0, 35.0],  # Negative and > 100
        'delinq_2yrs': [0, -1, 1, 0, 2],  # Negative
        'open_accounts': [3, 5, 15, 4, 6],  # open > total
        'total_accounts': [5, 8, 10, 6, 9]
    })


class TestDataQualityChecker:
    """Test suite for DataQualityChecker"""
    
    def test_rule_1_null_critical_fields_pass(self, valid_df):
        """Test null check passes with valid data"""
        checker = DataQualityChecker()
        result = checker.rule_1_null_critical_fields(valid_df)
        
        assert result.passed == True
        assert result.failed_records == 0
        assert result.pass_rate == 100.0
    
    def test_rule_1_null_critical_fields_fail(self, invalid_df):
        """Test null check fails with invalid data"""
        checker = DataQualityChecker()
        result = checker.rule_1_null_critical_fields(invalid_df)
        
        assert result.passed == False
        assert result.failed_records > 0
    
    def test_rule_2_loan_amount_range_pass(self, valid_df):
        """Test loan amount range passes with valid data"""
        checker = DataQualityChecker()
        result = checker.rule_2_loan_amount_range(valid_df)
        
        assert result.passed == True
        assert result.failed_records == 0
    
    def test_rule_2_loan_amount_range_fail(self, invalid_df):
        """Test loan amount range fails with invalid data"""
        checker = DataQualityChecker()
        result = checker.rule_2_loan_amount_range(invalid_df)
        
        assert result.passed == False
        assert result.failed_records >= 2  # $50 too low, $2M too high, null
    
    def test_rule_3_interest_rate_range_pass(self, valid_df):
        """Test interest rate range passes with valid data"""
        checker = DataQualityChecker()
        result = checker.rule_3_interest_rate_range(valid_df)
        
        assert result.passed == True
    
    def test_rule_3_interest_rate_range_fail(self, invalid_df):
        """Test interest rate range fails with invalid data"""
        checker = DataQualityChecker()
        result = checker.rule_3_interest_rate_range(invalid_df)
        
        assert result.passed == False
    
    def test_rule_4_duplicate_loan_ids_pass(self, valid_df):
        """Test duplicate check passes with unique IDs"""
        checker = DataQualityChecker()
        result = checker.rule_4_duplicate_loan_ids(valid_df)
        
        assert result.passed == True
        assert result.failed_records == 0
    
    def test_rule_4_duplicate_loan_ids_fail(self, invalid_df):
        """Test duplicate check fails with duplicate IDs"""
        checker = DataQualityChecker()
        result = checker.rule_4_duplicate_loan_ids(invalid_df)
        
        assert result.passed == False
        assert result.failed_records >= 2  # L001 appears twice
    
    def test_rule_5_valid_loan_term_pass(self, valid_df):
        """Test loan term validation passes"""
        checker = DataQualityChecker()
        result = checker.rule_5_valid_loan_term(valid_df)
        
        assert result.passed == True
    
    def test_rule_5_valid_loan_term_fail(self, invalid_df):
        """Test loan term validation fails with invalid term"""
        checker = DataQualityChecker()
        result = checker.rule_5_valid_loan_term(invalid_df)
        
        assert result.passed == False
        assert result.failed_records >= 1  # 45 months is invalid
    
    def test_rule_6_valid_home_ownership_pass(self, valid_df):
        """Test home ownership validation passes"""
        checker = DataQualityChecker()
        result = checker.rule_6_valid_home_ownership(valid_df)
        
        assert result.passed == True
    
    def test_rule_6_valid_home_ownership_fail(self, invalid_df):
        """Test home ownership validation fails"""
        checker = DataQualityChecker()
        result = checker.rule_6_valid_home_ownership(invalid_df)
        
        assert result.passed == False
    
    def test_rule_7_positive_income_pass(self, valid_df):
        """Test positive income validation passes"""
        checker = DataQualityChecker()
        result = checker.rule_7_positive_income(valid_df)
        
        assert result.passed == True
    
    def test_rule_7_positive_income_fail(self, invalid_df):
        """Test positive income validation fails"""
        checker = DataQualityChecker()
        result = checker.rule_7_positive_income(invalid_df)
        
        assert result.passed == False
    
    def test_rule_8_valid_dti_ratio_pass(self, valid_df):
        """Test DTI ratio validation passes"""
        checker = DataQualityChecker()
        result = checker.rule_8_valid_dti_ratio(valid_df)
        
        assert result.passed == True
    
    def test_rule_8_valid_dti_ratio_fail(self, invalid_df):
        """Test DTI ratio validation fails"""
        checker = DataQualityChecker()
        result = checker.rule_8_valid_dti_ratio(invalid_df)
        
        assert result.passed == False
    
    def test_rule_9_valid_delinquency_pass(self, valid_df):
        """Test delinquency validation passes"""
        checker = DataQualityChecker()
        result = checker.rule_9_valid_delinquency(valid_df)
        
        assert result.passed == True
    
    def test_rule_9_valid_delinquency_fail(self, invalid_df):
        """Test delinquency validation fails"""
        checker = DataQualityChecker()
        result = checker.rule_9_valid_delinquency(invalid_df)
        
        assert result.passed == False
    
    def test_rule_10_referential_integrity_pass(self, valid_df):
        """Test referential integrity passes"""
        checker = DataQualityChecker()
        result = checker.rule_10_referential_integrity(valid_df)
        
        assert result.passed == True
    
    def test_rule_10_referential_integrity_fail(self, invalid_df):
        """Test referential integrity fails"""
        checker = DataQualityChecker()
        result = checker.rule_10_referential_integrity(invalid_df)
        
        assert result.passed == False


class TestRunDataQualityChecks:
    """Test the main DQ check function"""
    
    def test_run_all_checks_valid_data(self, valid_df):
        """Test running all checks on valid data"""
        results, overall_pass = run_data_quality_checks(valid_df)
        
        assert len(results) == 10
        assert overall_pass == True
        assert all(r.passed for r in results)
    
    def test_run_all_checks_invalid_data(self, invalid_df):
        """Test running all checks on invalid data"""
        results, overall_pass = run_data_quality_checks(invalid_df)
        
        assert len(results) == 10
        assert overall_pass == False
        assert any(not r.passed for r in results)
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=['loan_id', 'customer_id', 'loan_amount', 'interest_rate', 'loan_term'])
        results, overall_pass = run_data_quality_checks(empty_df)
        
        assert len(results) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
