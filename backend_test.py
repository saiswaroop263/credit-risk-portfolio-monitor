#!/usr/bin/env python3
"""
Credit Risk Portfolio Monitor - Backend API Testing
Tests all API endpoints for functionality and data integrity
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CreditRiskAPITester:
    def __init__(self, base_url: str = "https://creditrisk-monitor.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.demo_run_id = None
        self.session = requests.Session()
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {details}")
        else:
            print(f"❌ {name}: FAILED {details}")
        return success
    
    def test_health_check(self) -> bool:
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data.get('status', 'unknown')}"
            return self.log_test("Health Check", success, details)
        except Exception as e:
            return self.log_test("Health Check", False, f"Error: {str(e)}")
    
    def test_root_endpoint(self) -> bool:
        """Test root API endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'N/A')}"
            return self.log_test("Root Endpoint", success, details)
        except Exception as e:
            return self.log_test("Root Endpoint", False, f"Error: {str(e)}")
    
    def test_demo_endpoint(self) -> bool:
        """Test demo data generation and pipeline execution"""
        try:
            print("🔄 Running demo pipeline (this may take 30-60 seconds)...")
            response = self.session.post(f"{self.base_url}/api/demo", timeout=120)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                self.demo_run_id = data.get('run_id')
                details += f", Run ID: {self.demo_run_id[:8]}..., Records: {data.get('records_generated', 0)}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
                    
            return self.log_test("Demo Pipeline", success, details)
        except Exception as e:
            return self.log_test("Demo Pipeline", False, f"Error: {str(e)}")
    
    def test_kpis_endpoint(self) -> bool:
        """Test KPIs endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/kpis", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if 'message' in data:
                    details += f", Message: {data['message']}"
                else:
                    # Check for expected KPI fields
                    expected_fields = ['total_loans', 'total_portfolio_value', 'avg_risk_score', 'high_risk_count']
                    found_fields = [field for field in expected_fields if field in data]
                    details += f", KPI fields found: {len(found_fields)}/{len(expected_fields)}"
                    if len(found_fields) == len(expected_fields):
                        details += f", Total loans: {data.get('total_loans', 0)}"
                        
            return self.log_test("KPIs Endpoint", success, details)
        except Exception as e:
            return self.log_test("KPIs Endpoint", False, f"Error: {str(e)}")
    
    def test_dq_endpoint(self) -> bool:
        """Test Data Quality endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/dq", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if 'message' in data:
                    details += f", Message: {data['message']}"
                else:
                    # Check for DQ report structure
                    total_rules = data.get('total_rules', 0)
                    passed_rules = data.get('passed_rules', 0)
                    details += f", Rules: {total_rules}, Passed: {passed_rules}"
                    if total_rules >= 10:  # Should have 10 DQ rules
                        details += " ✓"
                        
            return self.log_test("Data Quality Endpoint", success, details)
        except Exception as e:
            return self.log_test("Data Quality Endpoint", False, f"Error: {str(e)}")
    
    def test_drift_endpoint(self) -> bool:
        """Test Drift Detection endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/drift", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if 'message' in data:
                    details += f", Message: {data['message']}"
                else:
                    # Check for drift report structure
                    total_features = data.get('total_features', 0)
                    drifted_features = data.get('drifted_features', 0)
                    drift_detected = data.get('overall_drift_detected', False)
                    details += f", Features: {total_features}, Drifted: {drifted_features}, Overall drift: {drift_detected}"
                    
            return self.log_test("Drift Detection Endpoint", success, details)
        except Exception as e:
            return self.log_test("Drift Detection Endpoint", False, f"Error: {str(e)}")
    
    def test_models_endpoint(self) -> bool:
        """Test Models metadata endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/models", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                models = data.get('models', [])
                details += f", Models found: {len(models)}"
                
                # Check for expected model types
                model_types = [model.get('model_type') for model in models]
                if 'logistic' in model_types and 'boosted' in model_types:
                    details += " (Logistic + Boosted) ✓"
                    
                    # Check AUC scores
                    for model in models:
                        if model.get('model_type') == 'logistic':
                            auc = model.get('auc_roc', 0)
                            details += f", Logistic AUC: {auc:.3f}"
                        elif model.get('model_type') == 'boosted':
                            auc = model.get('auc_roc', 0)
                            details += f", Boosted AUC: {auc:.3f}"
                            
            return self.log_test("Models Endpoint", success, details)
        except Exception as e:
            return self.log_test("Models Endpoint", False, f"Error: {str(e)}")
    
    def test_runs_endpoint(self) -> bool:
        """Test Runs history endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/runs", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                runs = data.get('runs', [])
                details += f", Runs found: {len(runs)}"
                
                if runs:
                    latest_run = runs[0]
                    status = latest_run.get('status', 'unknown')
                    details += f", Latest status: {status}"
                    
            return self.log_test("Runs Endpoint", success, details)
        except Exception as e:
            return self.log_test("Runs Endpoint", False, f"Error: {str(e)}")
    
    def test_scores_endpoint(self) -> bool:
        """Test Scores endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/scores?limit=10", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                scores = data.get('scores', [])
                details += f", Scores found: {len(scores)}"
                
                if scores:
                    # Check score structure
                    sample_score = scores[0]
                    required_fields = ['loan_id', 'logistic_score', 'boosted_score', 'ensemble_score', 'risk_level']
                    found_fields = [field for field in required_fields if field in sample_score]
                    details += f", Score fields: {len(found_fields)}/{len(required_fields)}"
                    
            return self.log_test("Scores Endpoint", success, details)
        except Exception as e:
            return self.log_test("Scores Endpoint", False, f"Error: {str(e)}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print("🚀 Starting Credit Risk Portfolio Monitor Backend Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        self.test_health_check()
        self.test_root_endpoint()
        
        # Core functionality test
        demo_success = self.test_demo_endpoint()
        
        # Data retrieval tests (only if demo worked)
        if demo_success:
            print("\n📊 Testing data retrieval endpoints...")
            self.test_kpis_endpoint()
            self.test_dq_endpoint()
            self.test_drift_endpoint()
            self.test_models_endpoint()
            self.test_runs_endpoint()
            self.test_scores_endpoint()
        else:
            print("\n⚠️  Skipping data tests due to demo failure")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📈 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "demo_run_id": self.demo_run_id,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main test execution"""
    tester = CreditRiskAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["success_rate"] >= 80:
        print("\n✅ Backend tests completed successfully!")
        return 0
    else:
        print("\n❌ Backend tests failed - multiple issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())