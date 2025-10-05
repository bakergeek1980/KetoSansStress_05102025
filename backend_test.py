#!/usr/bin/env python3
"""
Backend API Testing for KetoSansStress User Preferences
Tests all User Preferences CRUD operations and helper endpoints
Focus: Comprehensive testing of the newly implemented preferences API
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://ketotrackerapp-1.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"test_prefs_{uuid.uuid4().hex[:8]}@ketosansstress.com"
TEST_USER_PASSWORD = "TestPassword123!"

class PreferencesAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def register_and_login_user(self) -> bool:
        """Register a new test user and login to get JWT token"""
        try:
            # Register new user
            register_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Test Preferences User"
            }
            
            register_response = self.session.post(
                f"{self.base_url}/auth/register",
                json=register_data,
                timeout=30
            )
            
            if register_response.status_code not in [200, 201]:
                self.log_test(
                    "User Registration", 
                    False, 
                    f"Registration failed with status {register_response.status_code}: {register_response.text}"
                )
                return False
            
            self.log_test("User Registration", True, f"User registered successfully: {TEST_USER_EMAIL}")
            
            # Login to get access token
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            login_response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                timeout=30
            )
            
            if login_response.status_code != 200:
                self.log_test(
                    "User Login", 
                    False, 
                    f"Login failed with status {login_response.status_code}: {login_response.text}"
                )
                return False
            
            login_result = login_response.json()
            self.access_token = login_result.get("access_token")
            
            if not self.access_token:
                self.log_test("User Login", False, "No access token received")
                return False
            
            # Set authorization header for all future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })
            
            # Get user info to extract user_id
            me_response = self.session.get(f"{self.base_url}/auth/me", timeout=30)
            if me_response.status_code == 200:
                user_info = me_response.json()
                self.user_id = user_info.get("id")
                self.log_test("User Login", True, f"Login successful, user_id: {self.user_id}")
                return True
            else:
                self.log_test("User Login", False, f"Failed to get user info: {me_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Setup", False, f"Exception during auth: {str(e)}")
            return False
    
    def test_helper_endpoints(self):
        """Test helper endpoints that don't require authentication"""
        
        # Test GET /api/preferences/regions
        try:
            regions_response = self.session.get(f"{self.base_url}/preferences/regions", timeout=30)
            
            if regions_response.status_code == 200:
                regions_data = regions_response.json()
                regions = regions_data.get("regions", [])
                
                expected_regions = ["FR", "BE", "CH", "CA", "OTHER"]
                found_regions = [r.get("code") for r in regions]
                
                if all(region in found_regions for region in expected_regions):
                    self.log_test(
                        "GET /api/preferences/regions", 
                        True, 
                        f"All expected regions found: {found_regions}",
                        regions_data
                    )
                else:
                    self.log_test(
                        "GET /api/preferences/regions", 
                        False, 
                        f"Missing regions. Expected: {expected_regions}, Found: {found_regions}"
                    )
            else:
                self.log_test(
                    "GET /api/preferences/regions", 
                    False, 
                    f"Status {regions_response.status_code}: {regions_response.text}"
                )
                
        except Exception as e:
            self.log_test("GET /api/preferences/regions", False, f"Exception: {str(e)}")
        
        # Test GET /api/preferences/units
        try:
            units_response = self.session.get(f"{self.base_url}/preferences/units", timeout=30)
            
            if units_response.status_code == 200:
                units_data = units_response.json()
                
                required_unit_types = ["weight_units", "height_units", "liquid_units", "temperature_units"]
                found_unit_types = list(units_data.keys())
                
                if all(unit_type in found_unit_types for unit_type in required_unit_types):
                    self.log_test(
                        "GET /api/preferences/units", 
                        True, 
                        f"All unit types found: {found_unit_types}",
                        units_data
                    )
                else:
                    self.log_test(
                        "GET /api/preferences/units", 
                        False, 
                        f"Missing unit types. Expected: {required_unit_types}, Found: {found_unit_types}"
                    )
            else:
                self.log_test(
                    "GET /api/preferences/units", 
                    False, 
                    f"Status {units_response.status_code}: {units_response.text}"
                )
                
        except Exception as e:
            self.log_test("GET /api/preferences/units", False, f"Exception: {str(e)}")
    
    def test_get_user_preferences_with_defaults(self):
        """Test GET /api/user-preferences/{user_id} - should create defaults if none exist"""
        try:
            response = self.session.get(
                f"{self.base_url}/user-preferences/{self.user_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                prefs_data = response.json()
                
                # Check that default preferences are returned
                expected_defaults = {
                    "user_id": self.user_id,
                    "count_net_carbs": True,
                    "region": "FR",
                    "unit_system": "metric",
                    "dark_mode": False,
                    "theme_preference": "system",
                    "language": "fr"
                }
                
                all_defaults_correct = True
                missing_fields = []
                
                for key, expected_value in expected_defaults.items():
                    if prefs_data.get(key) != expected_value:
                        all_defaults_correct = False
                        missing_fields.append(f"{key}: expected {expected_value}, got {prefs_data.get(key)}")
                
                if all_defaults_correct:
                    self.log_test(
                        "GET /api/user-preferences/{user_id} (defaults)", 
                        True, 
                        "Default preferences created and returned correctly",
                        prefs_data
                    )
                else:
                    self.log_test(
                        "GET /api/user-preferences/{user_id} (defaults)", 
                        False, 
                        f"Default preferences incorrect: {missing_fields}"
                    )
            else:
                self.log_test(
                    "GET /api/user-preferences/{user_id} (defaults)", 
                    False, 
                    f"Status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("GET /api/user-preferences/{user_id} (defaults)", False, f"Exception: {str(e)}")
    
    def test_create_user_preferences(self):
        """Test POST /api/user-preferences - create new preferences"""
        try:
            # First delete existing preferences to test creation
            delete_response = self.session.delete(
                f"{self.base_url}/user-preferences/{self.user_id}",
                timeout=30
            )
            
            # Create new preferences
            new_preferences = {
                "user_id": self.user_id,
                "count_net_carbs": False,
                "region": "CA",
                "unit_system": "imperial",
                "dark_mode": True,
                "theme_preference": "dark",
                "health_sync_enabled": True,
                "notifications_enabled": False,
                "language": "en",
                "timezone": "America/Montreal",
                "weight_unit": "lb",
                "height_unit": "ft",
                "liquid_unit": "fl_oz",
                "temperature_unit": "fahrenheit"
            }
            
            response = self.session.post(
                f"{self.base_url}/user-preferences",
                json=new_preferences,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                created_prefs = response.json()
                
                # Verify the created preferences match what we sent
                all_correct = True
                incorrect_fields = []
                
                for key, expected_value in new_preferences.items():
                    if created_prefs.get(key) != expected_value:
                        all_correct = False
                        incorrect_fields.append(f"{key}: expected {expected_value}, got {created_prefs.get(key)}")
                
                if all_correct:
                    self.log_test(
                        "POST /api/user-preferences", 
                        True, 
                        "User preferences created successfully",
                        created_prefs
                    )
                else:
                    self.log_test(
                        "POST /api/user-preferences", 
                        False, 
                        f"Created preferences don't match: {incorrect_fields}"
                    )
            else:
                self.log_test(
                    "POST /api/user-preferences", 
                    False, 
                    f"Status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("POST /api/user-preferences", False, f"Exception: {str(e)}")
    
    def test_update_user_preferences_patch(self):
        """Test PATCH /api/user-preferences/{user_id} - partial update"""
        try:
            # Update only specific fields
            updates = {
                "dark_mode": False,
                "region": "BE",
                "notifications_enabled": True,
                "language": "fr"
            }
            
            response = self.session.patch(
                f"{self.base_url}/user-preferences/{self.user_id}",
                json=updates,
                timeout=30
            )
            
            if response.status_code == 200:
                updated_prefs = response.json()
                
                # Verify the updates were applied
                all_correct = True
                incorrect_fields = []
                
                for key, expected_value in updates.items():
                    if updated_prefs.get(key) != expected_value:
                        all_correct = False
                        incorrect_fields.append(f"{key}: expected {expected_value}, got {updated_prefs.get(key)}")
                
                # Also verify that other fields weren't changed (should still be from previous test)
                if updated_prefs.get("unit_system") != "imperial":
                    all_correct = False
                    incorrect_fields.append("unit_system should remain 'imperial'")
                
                if all_correct:
                    self.log_test(
                        "PATCH /api/user-preferences/{user_id}", 
                        True, 
                        "User preferences updated successfully",
                        updated_prefs
                    )
                else:
                    self.log_test(
                        "PATCH /api/user-preferences/{user_id}", 
                        False, 
                        f"Updates not applied correctly: {incorrect_fields}"
                    )
            else:
                self.log_test(
                    "PATCH /api/user-preferences/{user_id}", 
                    False, 
                    f"Status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("PATCH /api/user-preferences/{user_id}", False, f"Exception: {str(e)}")
    
    def test_replace_user_preferences_put(self):
        """Test PUT /api/user-preferences/{user_id} - complete replacement"""
        try:
            # Replace all preferences
            replacement_preferences = {
                "user_id": self.user_id,
                "count_net_carbs": True,
                "region": "CH",
                "unit_system": "metric",
                "dark_mode": True,
                "theme_preference": "light",
                "health_sync_enabled": False,
                "health_sync_permissions": {"steps": True, "weight": False},
                "notifications_enabled": True,
                "auto_sync": False,
                "data_saver_mode": True,
                "biometric_lock": True,
                "language": "de",
                "timezone": "Europe/Zurich",
                "date_format": "DD.MM.YYYY",
                "time_format": "24h",
                "weight_unit": "kg",
                "height_unit": "cm",
                "liquid_unit": "ml",
                "temperature_unit": "celsius"
            }
            
            response = self.session.put(
                f"{self.base_url}/user-preferences/{self.user_id}",
                json=replacement_preferences,
                timeout=30
            )
            
            if response.status_code == 200:
                replaced_prefs = response.json()
                
                # Verify the replacement was complete
                all_correct = True
                incorrect_fields = []
                
                for key, expected_value in replacement_preferences.items():
                    actual_value = replaced_prefs.get(key)
                    if actual_value != expected_value:
                        all_correct = False
                        incorrect_fields.append(f"{key}: expected {expected_value}, got {actual_value}")
                
                if all_correct:
                    self.log_test(
                        "PUT /api/user-preferences/{user_id}", 
                        True, 
                        "User preferences replaced successfully",
                        replaced_prefs
                    )
                else:
                    self.log_test(
                        "PUT /api/user-preferences/{user_id}", 
                        False, 
                        f"Replacement not applied correctly: {incorrect_fields}"
                    )
            else:
                self.log_test(
                    "PUT /api/user-preferences/{user_id}", 
                    False, 
                    f"Status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("PUT /api/user-preferences/{user_id}", False, f"Exception: {str(e)}")
    
    def test_get_user_preferences_after_updates(self):
        """Test GET /api/user-preferences/{user_id} after updates"""
        try:
            response = self.session.get(
                f"{self.base_url}/user-preferences/{self.user_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                prefs_data = response.json()
                
                # Verify that the preferences match the last PUT operation
                expected_values = {
                    "region": "CH",
                    "unit_system": "metric",
                    "dark_mode": True,
                    "language": "de",
                    "timezone": "Europe/Zurich",
                    "biometric_lock": True
                }
                
                all_correct = True
                incorrect_fields = []
                
                for key, expected_value in expected_values.items():
                    if prefs_data.get(key) != expected_value:
                        all_correct = False
                        incorrect_fields.append(f"{key}: expected {expected_value}, got {prefs_data.get(key)}")
                
                if all_correct:
                    self.log_test(
                        "GET /api/user-preferences/{user_id} (after updates)", 
                        True, 
                        "Retrieved preferences match last update",
                        prefs_data
                    )
                else:
                    self.log_test(
                        "GET /api/user-preferences/{user_id} (after updates)", 
                        False, 
                        f"Retrieved preferences don't match: {incorrect_fields}"
                    )
            else:
                self.log_test(
                    "GET /api/user-preferences/{user_id} (after updates)", 
                    False, 
                    f"Status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("GET /api/user-preferences/{user_id} (after updates)", False, f"Exception: {str(e)}")
    
    def test_authentication_security(self):
        """Test that endpoints properly require authentication"""
        
        # Create a session without authentication
        unauth_session = requests.Session()
        
        # Test GET without auth
        try:
            response = unauth_session.get(
                f"{self.base_url}/user-preferences/{self.user_id}",
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Authentication Security (GET)", 
                    True, 
                    "Properly rejected unauthenticated GET request"
                )
            else:
                self.log_test(
                    "Authentication Security (GET)", 
                    False, 
                    f"Should return 401, got {response.status_code}"
                )
        except Exception as e:
            self.log_test("Authentication Security (GET)", False, f"Exception: {str(e)}")
        
        # Test POST without auth
        try:
            test_prefs = {"user_id": self.user_id, "dark_mode": True}
            response = unauth_session.post(
                f"{self.base_url}/user-preferences",
                json=test_prefs,
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Authentication Security (POST)", 
                    True, 
                    "Properly rejected unauthenticated POST request"
                )
            else:
                self.log_test(
                    "Authentication Security (POST)", 
                    False, 
                    f"Should return 401, got {response.status_code}"
                )
        except Exception as e:
            self.log_test("Authentication Security (POST)", False, f"Exception: {str(e)}")
        
        # Test access to other user's preferences
        try:
            fake_user_id = str(uuid.uuid4())
            response = self.session.get(
                f"{self.base_url}/user-preferences/{fake_user_id}",
                timeout=30
            )
            
            if response.status_code == 403:
                self.log_test(
                    "Authorization Security", 
                    True, 
                    "Properly rejected access to other user's preferences"
                )
            else:
                self.log_test(
                    "Authorization Security", 
                    False, 
                    f"Should return 403, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_test("Authorization Security", False, f"Exception: {str(e)}")
    
    def test_delete_user_preferences(self):
        """Test DELETE /api/user-preferences/{user_id}"""
        try:
            response = self.session.delete(
                f"{self.base_url}/user-preferences/{self.user_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "message" in result and "supprimées" in result["message"]:
                    self.log_test(
                        "DELETE /api/user-preferences/{user_id}", 
                        True, 
                        "User preferences deleted successfully",
                        result
                    )
                    
                    # Verify deletion by trying to get preferences (should create new defaults)
                    get_response = self.session.get(
                        f"{self.base_url}/user-preferences/{self.user_id}",
                        timeout=30
                    )
                    
                    if get_response.status_code == 200:
                        new_prefs = get_response.json()
                        # Should be back to defaults
                        if new_prefs.get("region") == "FR" and new_prefs.get("dark_mode") == False:
                            self.log_test(
                                "DELETE verification", 
                                True, 
                                "Preferences reset to defaults after deletion"
                            )
                        else:
                            self.log_test(
                                "DELETE verification", 
                                False, 
                                "Preferences not reset to defaults after deletion"
                            )
                else:
                    self.log_test(
                        "DELETE /api/user-preferences/{user_id}", 
                        False, 
                        f"Unexpected response format: {result}"
                    )
            else:
                self.log_test(
                    "DELETE /api/user-preferences/{user_id}", 
                    False, 
                    f"Status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("DELETE /api/user-preferences/{user_id}", False, f"Exception: {str(e)}")
    
    def test_data_validation(self):
        """Test data validation and error handling"""
        
        # Test invalid region
        try:
            invalid_prefs = {
                "user_id": self.user_id,
                "region": "INVALID_REGION",
                "unit_system": "metric"
            }
            
            response = self.session.post(
                f"{self.base_url}/user-preferences",
                json=invalid_prefs,
                timeout=30
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test(
                    "Data Validation (invalid region)", 
                    True, 
                    "Properly rejected invalid region value"
                )
            else:
                self.log_test(
                    "Data Validation (invalid region)", 
                    False, 
                    f"Should return 422, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_test("Data Validation (invalid region)", False, f"Exception: {str(e)}")
        
        # Test invalid unit system
        try:
            invalid_prefs = {
                "user_id": self.user_id,
                "region": "FR",
                "unit_system": "invalid_units"
            }
            
            response = self.session.post(
                f"{self.base_url}/user-preferences",
                json=invalid_prefs,
                timeout=30
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test(
                    "Data Validation (invalid units)", 
                    True, 
                    "Properly rejected invalid unit system value"
                )
            else:
                self.log_test(
                    "Data Validation (invalid units)", 
                    False, 
                    f"Should return 422, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_test("Data Validation (invalid units)", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests."""
        print("🚀 CRITICAL VALIDATION: KetoSansStress Backend Testing After GLOBAL RESET")
        print("Expected: 100% success rate (was 73.3% before)")
        print("=" * 80)
        
        # Core system tests
        self.test_health_check()
        
        # Authentication system tests
        self.test_user_registration()
        self.test_user_login()
        self.test_jwt_validation()
        
        # NEW SUPABASE MEALS API TESTS (PRIORITY VALIDATION)
        print("\n" + "="*50)
        print("🎯 PRIORITY VALIDATION TESTS - NEW SUPABASE MEALS API")
        print("="*50)
        self.test_new_meals_api_create()  # THE MAIN BLOCKER
        self.test_new_meals_api_list()
        self.test_new_meals_api_today()
        
        # Database schema validation
        self.test_database_schema_validation()
        
        # Legacy endpoints tests
        print("\n" + "="*40)
        print("🔄 LEGACY ENDPOINTS VALIDATION")
        print("="*40)
        self.test_legacy_meal_analysis()
        self.test_legacy_food_search()
        self.test_legacy_daily_summary()
        
        # OpenFoodFacts integration
        self.test_openfoodfacts_keto_friendly()
        
        # Print final results
        self.print_final_results()

    def print_final_results(self):
        """Print comprehensive test results."""
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE TEST RESULTS - GLOBAL RESET VALIDATION")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests})")
        print(f"📈 Previous Success Rate: 73.3%")
        
        if success_rate == 100.0:
            print("🎉 PERFECT SCORE! GLOBAL RESET SQL SCRIPT WORKED!")
            print("✅ All database schema issues resolved!")
            print("✅ 'brand' column issue completely fixed!")
        elif success_rate >= 90.0:
            print("🎯 EXCELLENT! Nearly perfect - minor issues remain")
        elif success_rate >= 80.0:
            print("👍 GOOD! Significant improvement from 73.3%")
        elif success_rate <= 73.3:
            print("❌ CRITICAL: NO IMPROVEMENT! GLOBAL RESET SQL SCRIPT NOT EXECUTED!")
            print("🚨 The 'brand' column and other schema issues are still present!")
        else:
            print("⚠️  PARTIAL IMPROVEMENT but critical issues remain")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
                
            # Check for specific critical failures
            critical_failures = [t for t in failed_tests if "brand" in t['details'].lower()]
            if critical_failures:
                print(f"\n🚨 CRITICAL FINDING:")
                print("   The 'brand' column error is still present!")
                print("   This proves the GLOBAL RESET SQL script was NOT executed!")
        
        # Show passed tests
        passed_tests = [r for r in self.test_results if r["success"]]
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests:
                print(f"   • {test['test']}")
        
        print("\n" + "=" * 80)
        
        # Final verdict
        if success_rate <= 73.3:
            print("🔴 VERDICT: USER HAS NOT EXECUTED THE GLOBAL RESET SQL SCRIPT!")
            print("   The database schema issues are still present.")
            print("   Expected 100% success rate, got {:.1f}%".format(success_rate))
        elif success_rate == 100.0:
            print("🟢 VERDICT: GLOBAL RESET SQL SCRIPT SUCCESSFULLY EXECUTED!")
            print("   All database schema issues resolved!")
        else:
            print("🟡 VERDICT: PARTIAL SUCCESS - Some improvements made")

if __name__ == "__main__":
    tester = KetoBackendTester()
    tester.run_all_tests()