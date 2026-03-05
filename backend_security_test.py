#!/usr/bin/env python3

import requests
import sys
import json
import logging
import time
import pyotp
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityFeaturesAPITester:
    def __init__(self, base_url="https://agency-andre-dev.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_id = None
        self.twofa_secret = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }

    def log_test(self, test_name: str, success: bool, message: str = "", response_data: Dict = None):
        """Log test result"""
        self.test_results["total_tests"] += 1
        
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - {message}")
        else:
            self.test_results["failed_tests"].append({
                "test": test_name,
                "message": message,
                "response": response_data
            })
            logger.error(f"❌ {test_name} - {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, expected_status: int = 200, form_data: Dict = None) -> Dict:
        """Make HTTP request and return response data"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('http') else endpoint
        if not endpoint.startswith('/api/') and not endpoint.startswith('http'):
            url = f"{self.base_url}/api/{endpoint}"
        
        request_headers = {}
        if not form_data:
            request_headers['Content-Type'] = 'application/json'
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == 'POST':
                if form_data:
                    response = requests.post(url, data=form_data, headers=request_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return {"error": f"Unsupported method: {method}"}

            result = {
                "status_code": response.status_code,
                "success": response.status_code == expected_status,
                "response": {}
            }
            
            try:
                result["response"] = response.json()
            except:
                result["response"] = {"text": response.text[:500]}
                
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response": {}
            }

    def test_api_health_check(self):
        """Test API health check - GET /api/"""
        result = self.make_request('GET', '', expected_status=200)
        
        if result["success"]:
            message = result["response"].get("message", "")
            if "Andre Dev" in message:
                self.log_test("API Health Check", True, f"API responding correctly: {message}")
            else:
                self.log_test("API Health Check", False, f"Unexpected response format: {result['response']}")
        else:
            self.log_test("API Health Check", False, f"API not responding (Status: {result['status_code']})", result)

    def authenticate_test_user(self):
        """Authenticate with the provided test user"""
        login_data = {
            "email": "teste.stripe@example.com",
            "password": "teste123"
        }
        
        result = self.make_request('POST', 'auth/login', data=login_data, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "access_token" in response_data:
                self.token = response_data["access_token"]
                self.user_id = response_data["user"]["id"]
                self.log_test("Test User Authentication", True, f"Authenticated as {login_data['email']}")
                return True
            elif "requires_2fa" in response_data:
                # User has 2FA enabled, we'll handle this separately
                self.user_id = response_data["user_id"]
                self.log_test("Test User Authentication", True, "User has 2FA enabled (will test separately)")
                return "2fa_required"
            else:
                self.log_test("Test User Authentication", False, f"Invalid login response: {response_data}")
        else:
            self.log_test("Test User Authentication", False, f"Authentication failed (Status: {result['status_code']})", result)
        return False

    def test_rate_limiting_login(self):
        """Test rate limiting on login endpoint (10/minute)"""
        test_data = {
            "email": "teste.stripe@example.com",
            "password": "wrongpassword"  # Use wrong password to avoid successful logins
        }
        
        # Make multiple rapid requests to test rate limiting
        success_count = 0
        rate_limited_count = 0
        
        for i in range(12):  # Try 12 requests (should exceed 10/minute limit)
            result = self.make_request('POST', 'auth/login', data=test_data, expected_status=401)
            
            if result["status_code"] == 401:
                success_count += 1
            elif result["status_code"] == 429:  # Rate limited
                rate_limited_count += 1
                break
            
            time.sleep(0.1)  # Small delay
        
        if rate_limited_count > 0:
            self.log_test("Rate Limiting Login", True, f"Rate limiting triggered after {success_count} requests")
            return True
        else:
            self.log_test("Rate Limiting Login", False, f"Rate limiting not triggered after {success_count} requests")
            return False

    def test_rate_limiting_register(self):
        """Test rate limiting on register endpoint (5/minute)"""
        
        # Make multiple rapid registration attempts
        success_count = 0
        rate_limited_count = 0
        
        for i in range(7):  # Try 7 requests (should exceed 5/minute limit)
            test_data = {
                "name": f"Rate Test User {i}",
                "email": f"ratetest{i}_{int(time.time())}@example.com",
                "password": "TestPassword123!"
            }
            
            result = self.make_request('POST', 'auth/register', data=test_data, expected_status=200)
            
            if result["status_code"] == 200:
                success_count += 1
            elif result["status_code"] == 429:  # Rate limited
                rate_limited_count += 1
                break
            
            time.sleep(0.1)  # Small delay
        
        if rate_limited_count > 0:
            self.log_test("Rate Limiting Register", True, f"Rate limiting triggered after {success_count} registrations")
            return True
        else:
            self.log_test("Rate Limiting Register", False, f"Rate limiting not triggered after {success_count} registrations")
            return False

    def test_rate_limiting_forgot_password(self):
        """Test rate limiting on forgot password endpoint (3/minute)"""
        test_data = {
            "email": "teste.stripe@example.com"
        }
        
        # Make multiple rapid requests to test rate limiting
        success_count = 0
        rate_limited_count = 0
        
        for i in range(5):  # Try 5 requests (should exceed 3/minute limit)
            result = self.make_request('POST', 'auth/forgot-password', data=test_data, expected_status=200)
            
            if result["status_code"] == 200:
                success_count += 1
            elif result["status_code"] == 429:  # Rate limited
                rate_limited_count += 1
                break
            
            time.sleep(0.1)  # Small delay
        
        if rate_limited_count > 0:
            self.log_test("Rate Limiting Forgot Password", True, f"Rate limiting triggered after {success_count} requests")
            return True
        else:
            self.log_test("Rate Limiting Forgot Password", False, f"Rate limiting not triggered after {success_count} requests")
            return False

    def test_2fa_status(self):
        """Test 2FA status endpoint"""
        if not self.token:
            self.log_test("2FA Status Check", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        result = self.make_request('GET', 'auth/2fa/status', headers=headers, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "enabled" in response_data and "email" in response_data:
                enabled = response_data["enabled"]
                email = response_data["email"]
                self.log_test("2FA Status Check", True, f"2FA status: {enabled}, Email: {email}")
                return enabled
            else:
                self.log_test("2FA Status Check", False, f"Invalid 2FA status response: {response_data}")
        else:
            self.log_test("2FA Status Check", False, f"2FA status failed (Status: {result['status_code']})", result)
        return None

    def test_2fa_setup(self):
        """Test 2FA setup endpoint"""
        if not self.token:
            self.log_test("2FA Setup", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        result = self.make_request('POST', 'auth/2fa/setup', data={}, headers=headers, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "secret" in response_data and "qr_code" in response_data:
                self.twofa_secret = response_data["secret"]
                qr_code = response_data["qr_code"]
                self.log_test("2FA Setup", True, f"2FA setup successful, secret generated")
                return True
            else:
                self.log_test("2FA Setup", False, f"Invalid 2FA setup response: {response_data}")
        else:
            self.log_test("2FA Setup", False, f"2FA setup failed (Status: {result['status_code']})", result)
        return False

    def test_2fa_verify_setup(self):
        """Test 2FA verification setup endpoint"""
        if not self.token or not self.twofa_secret:
            self.log_test("2FA Verify Setup", False, "No authentication token or 2FA secret available")
            return False
            
        # Generate TOTP code
        totp = pyotp.TOTP(self.twofa_secret)
        code = totp.now()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        form_data = {"code": code}
        
        result = self.make_request('POST', 'auth/2fa/verify-setup', headers=headers, expected_status=200, form_data=form_data)
        
        if result["success"]:
            response_data = result["response"]
            if "enabled" in response_data:
                enabled = response_data["enabled"]
                self.log_test("2FA Verify Setup", True, f"2FA verification successful, enabled: {enabled}")
                return True
            else:
                self.log_test("2FA Verify Setup", False, f"Invalid 2FA verify response: {response_data}")
        else:
            self.log_test("2FA Verify Setup", False, f"2FA verification failed (Status: {result['status_code']})", result)
        return False

    def test_2fa_disable(self):
        """Test 2FA disable endpoint"""
        if not self.token or not self.twofa_secret:
            self.log_test("2FA Disable", False, "No authentication token or 2FA secret available")
            return False
            
        # Generate TOTP code
        totp = pyotp.TOTP(self.twofa_secret)
        code = totp.now()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        form_data = {"code": code}
        
        result = self.make_request('POST', 'auth/2fa/disable', headers=headers, expected_status=200, form_data=form_data)
        
        if result["success"]:
            response_data = result["response"]
            if "enabled" in response_data:
                enabled = response_data["enabled"]
                self.log_test("2FA Disable", True, f"2FA disabled successfully, enabled: {enabled}")
                return True
            else:
                self.log_test("2FA Disable", False, f"Invalid 2FA disable response: {response_data}")
        else:
            self.log_test("2FA Disable", False, f"2FA disable failed (Status: {result['status_code']})", result)
        return False

    def test_audit_log_file(self):
        """Test audit log file existence and format"""
        import os
        
        audit_log_path = "/var/log/supervisor/audit.log"
        
        if os.path.exists(audit_log_path):
            try:
                with open(audit_log_path, 'r') as f:
                    lines = f.readlines()
                
                if len(lines) > 0:
                    # Check if log format matches expected pattern
                    sample_line = lines[-1]  # Get last line
                    if "|" in sample_line and any(word in sample_line for word in ["LOGIN", "REGISTER", "2FA"]):
                        self.log_test("Audit Log File", True, f"Audit log file exists with {len(lines)} entries")
                        return True
                    else:
                        self.log_test("Audit Log File", False, f"Audit log format invalid: {sample_line}")
                else:
                    self.log_test("Audit Log File", True, "Audit log file exists but is empty (normal for fresh install)")
                    return True
            except Exception as e:
                self.log_test("Audit Log File", False, f"Error reading audit log: {str(e)}")
        else:
            self.log_test("Audit Log File", False, "Audit log file does not exist")
        return False

    def test_admin_security_stats(self):
        """Test admin security stats endpoint"""
        # First try with non-admin token (should fail)
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            result = self.make_request('GET', 'admin/security-stats', headers=headers, expected_status=403)
            
            if result["status_code"] == 403:
                self.log_test("Admin Security Stats (Non-Admin)", True, "Correctly denied access for non-admin user")
            else:
                self.log_test("Admin Security Stats (Non-Admin)", False, f"Expected 403 for non-admin, got {result['status_code']}")
        
        # Try to create admin for testing (will likely fail if admin exists)
        admin_data = {
            "name": "Security Test Admin",
            "email": f"securityadmin_{int(time.time())}@example.com",
            "password": "AdminPassword123!"
        }
        
        admin_setup = self.make_request('POST', 'admin/setup', data=admin_data, expected_status=200)
        
        if admin_setup["success"]:
            admin_response = admin_setup["response"]
            if "access_token" in admin_response:
                admin_headers = {"Authorization": f"Bearer {admin_response['access_token']}"}
                
                # Test security stats endpoint with admin token
                stats_result = self.make_request('GET', 'admin/security-stats', headers=admin_headers, expected_status=200)
                
                if stats_result["success"]:
                    stats_data = stats_result["response"]
                    expected_fields = ["login_success_24h", "login_failed_24h", "registrations_7d", "users_with_2fa", "total_users", "two_factor_adoption"]
                    
                    if all(field in stats_data for field in expected_fields):
                        self.log_test("Admin Security Stats", True, f"Security stats retrieved successfully")
                        return True
                    else:
                        missing_fields = [f for f in expected_fields if f not in stats_data]
                        self.log_test("Admin Security Stats", False, f"Missing fields in stats response: {missing_fields}")
                else:
                    self.log_test("Admin Security Stats", False, f"Security stats failed (Status: {stats_result['status_code']})", stats_result)
            else:
                self.log_test("Admin Security Stats", False, f"Admin setup response missing token: {admin_response}")
        else:
            # Admin setup failed, probably admin already exists
            self.log_test("Admin Security Stats", False, f"Cannot create test admin (Status: {admin_setup['status_code']}) - Admin probably already exists. Cannot test security stats endpoint without admin credentials.")
        
        return False

    def test_admin_audit_logs(self):
        """Test admin audit logs endpoint"""
        # First try with non-admin token (should fail)
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            result = self.make_request('GET', 'admin/audit-logs', headers=headers, expected_status=403)
            
            if result["status_code"] == 403:
                self.log_test("Admin Audit Logs (Non-Admin)", True, "Correctly denied access for non-admin user")
            else:
                self.log_test("Admin Audit Logs (Non-Admin)", False, f"Expected 403 for non-admin, got {result['status_code']}")
        
        # Note: We cannot test admin access without admin credentials
        self.log_test("Admin Audit Logs", False, "Cannot test admin audit logs endpoint without admin credentials")
        return False

    def run_security_tests(self):
        """Run all security-related tests"""
        logger.info("🔐 Starting Security Features API Testing...")
        logger.info(f"Testing endpoint: {self.base_url}")
        
        # Basic health check
        self.test_api_health_check()
        
        # Authenticate test user
        auth_result = self.authenticate_test_user()
        if auth_result == "2fa_required":
            logger.info("Test user has 2FA enabled - will test 2FA verification separately")
        
        # Rate Limiting Tests
        logger.info("\n🚦 Testing Rate Limiting...")
        self.test_rate_limiting_login()
        time.sleep(2)  # Wait between rate limit tests
        self.test_rate_limiting_register()
        time.sleep(2)
        self.test_rate_limiting_forgot_password()
        
        # 2FA Tests (only if we have authentication)
        if self.token:
            logger.info("\n🔐 Testing 2FA Features...")
            current_2fa_status = self.test_2fa_status()
            
            if not current_2fa_status:  # If 2FA is not enabled
                self.test_2fa_setup()
                if self.twofa_secret:
                    time.sleep(2)  # Wait for TOTP time window
                    self.test_2fa_verify_setup()
                    time.sleep(2)
                    self.test_2fa_disable()
        
        # Audit Logs Tests
        logger.info("\n📋 Testing Audit Logs...")
        self.test_audit_log_file()
        
        # Admin Security Features
        logger.info("\n👑 Testing Admin Security Features...")
        self.test_admin_security_stats()
        self.test_admin_audit_logs()
        
        # Print summary
        self.print_summary()
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = len(self.test_results["failed_tests"])
        
        logger.info("\n" + "="*50)
        logger.info("🔐 SECURITY TESTS SUMMARY")
        logger.info("="*50)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed} ✅")
        logger.info(f"Failed: {failed} ❌")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")
        
        if self.test_results["failed_tests"]:
            logger.info("\n❌ FAILED TESTS:")
            for failure in self.test_results["failed_tests"]:
                logger.error(f"  • {failure['test']}: {failure['message']}")
        
        if self.test_results["warnings"]:
            logger.info("\n⚠️ WARNINGS:")
            for warning in self.test_results["warnings"]:
                logger.warning(f"  • {warning}")

def main():
    """Main function to run security tests"""
    tester = SecurityFeaturesAPITester()
    
    try:
        results = tester.run_security_tests()
        
        # Save results to file
        with open("/app/security_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Return exit code based on success
        if results["passed_tests"] >= results["total_tests"] * 0.8:  # 80% success rate acceptable
            logger.info("🎉 Security tests completed successfully!")
            return 0
        else:
            logger.error(f"💥 Too many security tests failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Security test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())