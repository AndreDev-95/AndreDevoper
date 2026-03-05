#!/usr/bin/env python3

import requests
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AndreDevelopmentAPITester:
    def __init__(self, base_url="https://agency-andre-dev.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_id = None
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

    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, expected_status: int = 200) -> Dict:
        """Make HTTP request and return response data"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('http') else endpoint
        if not endpoint.startswith('/api/') and not endpoint.startswith('http'):
            url = f"{self.base_url}/api/{endpoint}"
        
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == 'POST':
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

    def test_mongodb_connection(self):
        """Test MongoDB Atlas connection - GET /api/admin/check"""
        result = self.make_request('GET', 'admin/check', expected_status=200)
        
        if result["success"]:
            admin_exists = result["response"].get("admin_exists")
            if admin_exists is not None:
                self.log_test("MongoDB Connection", True, f"MongoDB connected, admin_exists: {admin_exists}")
                return admin_exists
            else:
                self.log_test("MongoDB Connection", False, f"Invalid response format: {result['response']}")
        else:
            self.log_test("MongoDB Connection", False, f"MongoDB connection failed (Status: {result['status_code']})", result)
        return None

    def test_user_registration(self):
        """Test user registration"""
        test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"
        user_data = {
            "name": "Test User",
            "email": test_email,
            "password": "TestPassword123!",
            "company": "Test Company"
        }
        
        result = self.make_request('POST', 'auth/register', data=user_data, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "access_token" in response_data and "user" in response_data:
                self.token = response_data["access_token"]
                self.user_id = response_data["user"]["id"]
                self.log_test("User Registration", True, f"User registered successfully: {test_email}")
                return True
            else:
                self.log_test("User Registration", False, f"Invalid response format: {response_data}")
        else:
            self.log_test("User Registration", False, f"Registration failed (Status: {result['status_code']})", result)
        return False

    def test_user_login(self):
        """Test user login with registered user"""
        if not self.user_id:
            self.log_test("User Login", False, "No registered user available for login test")
            return False
            
        # Create a separate test user for login
        test_email = f"login_test_{datetime.now().strftime('%H%M%S')}@example.com"
        user_data = {
            "name": "Login Test User",
            "email": test_email,
            "password": "TestPassword123!"
        }
        
        # Register the user first
        reg_result = self.make_request('POST', 'auth/register', data=user_data, expected_status=200)
        if not reg_result["success"]:
            self.log_test("User Login", False, "Failed to create test user for login test")
            return False
            
        login_data = {
            "email": test_email,
            "password": "TestPassword123!"
        }
        
        result = self.make_request('POST', 'auth/login', data=login_data, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "access_token" in response_data:
                self.log_test("User Login", True, "Login successful")
                return True
            else:
                self.log_test("User Login", False, f"Invalid login response: {response_data}")
        else:
            self.log_test("User Login", False, f"Login failed (Status: {result['status_code']})", result)
        return False

    def test_protected_route_access(self):
        """Test accessing protected route with authentication"""
        if not self.token:
            self.log_test("Protected Route Access", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        result = self.make_request('GET', 'auth/me', headers=headers, expected_status=200)
        
        if result["success"]:
            user_data = result["response"]
            if "id" in user_data and "email" in user_data:
                self.log_test("Protected Route Access", True, f"User profile retrieved: {user_data.get('name')}")
                return True
            else:
                self.log_test("Protected Route Access", False, f"Invalid user profile format: {user_data}")
        else:
            self.log_test("Protected Route Access", False, f"Protected route access failed (Status: {result['status_code']})", result)
        return False

    def test_project_creation(self):
        """Test creating a new project"""
        if not self.token:
            self.log_test("Project Creation", False, "No authentication token available")
            return False
            
        project_data = {
            "name": "Test Project",
            "description": "This is a test project for API testing",
            "project_type": "web",
            "status": "pending",
            "budget": "€2000"
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        result = self.make_request('POST', 'projects', data=project_data, headers=headers, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "id" in response_data and response_data["name"] == project_data["name"]:
                self.log_test("Project Creation", True, f"Project created successfully: {response_data['id']}")
                return response_data["id"]
            else:
                self.log_test("Project Creation", False, f"Invalid project creation response: {response_data}")
        else:
            self.log_test("Project Creation", False, f"Project creation failed (Status: {result['status_code']})", result)
        return None

    def test_get_user_projects(self):
        """Test retrieving user projects"""
        if not self.token:
            self.log_test("Get User Projects", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        result = self.make_request('GET', 'projects', headers=headers, expected_status=200)
        
        if result["success"]:
            projects = result["response"]
            if isinstance(projects, list):
                self.log_test("Get User Projects", True, f"Retrieved {len(projects)} projects")
                return True
            else:
                self.log_test("Get User Projects", False, f"Invalid projects response format: {projects}")
        else:
            self.log_test("Get User Projects", False, f"Failed to get projects (Status: {result['status_code']})", result)
        return False

    def test_get_portfolio(self):
        """Test public portfolio endpoint"""
        result = self.make_request('GET', 'portfolio', expected_status=200)
        
        if result["success"]:
            portfolio = result["response"]
            if isinstance(portfolio, list):
                self.log_test("Get Portfolio", True, f"Retrieved {len(portfolio)} portfolio items")
                return True
            else:
                self.log_test("Get Portfolio", False, f"Invalid portfolio response format: {portfolio}")
        else:
            self.log_test("Get Portfolio", False, f"Portfolio retrieval failed (Status: {result['status_code']})", result)
        return False

    def test_contact_form_submission(self):
        """Test public contact form submission"""
        contact_data = {
            "name": "Test Contact",
            "email": "test@example.com",
            "phone": "+351123456789",
            "message": "This is a test contact message",
            "service_type": "web"
        }
        
        result = self.make_request('POST', 'contact', data=contact_data, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "id" in response_data and response_data["name"] == contact_data["name"]:
                self.log_test("Contact Form Submission", True, f"Contact submitted successfully: {response_data['id']}")
                return True
            else:
                self.log_test("Contact Form Submission", False, f"Invalid contact response: {response_data}")
        else:
            self.log_test("Contact Form Submission", False, f"Contact submission failed (Status: {result['status_code']})", result)
        return False

    def test_admin_functionality(self):
        """Test admin-related functionality"""
        # Check if admin setup is needed
        admin_check = self.test_mongodb_connection()
        
        if admin_check is False:
            # Try to create admin account
            admin_data = {
                "name": "Test Admin",
                "email": "admin@andredev.pt",
                "password": "AdminPassword123!"
            }
            
            result = self.make_request('POST', 'admin/setup', data=admin_data, expected_status=200)
            
            if result["success"]:
                response_data = result["response"]
                if "access_token" in response_data:
                    self.admin_token = response_data["access_token"]
                    self.admin_id = response_data["user"]["id"]
                    self.log_test("Admin Setup", True, "Admin account created successfully")
                    return True
                else:
                    self.log_test("Admin Setup", False, f"Invalid admin setup response: {response_data}")
            else:
                self.log_test("Admin Setup", False, f"Admin setup failed (Status: {result['status_code']})", result)
        else:
            self.log_test("Admin Check", True, "Admin account already exists")
            return True
        return False

    def test_password_reset_email(self):
        """Test password reset email functionality (Resend integration)"""
        if not self.token:
            self.log_test("Password Reset Email", False, "No user available for password reset test")
            return False
            
        # Use a test email that should exist
        reset_data = {
            "email": "teste.stripe@example.com"
        }
        
        result = self.make_request('POST', 'auth/forgot-password', data=reset_data, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "message" in response_data:
                self.log_test("Password Reset Email", True, "Password reset email sent successfully")
                return True
            else:
                self.log_test("Password Reset Email", False, f"Invalid reset response: {response_data}")
        else:
            self.log_test("Password Reset Email", False, f"Password reset failed (Status: {result['status_code']})", result)
        return False

    def test_notifications_system(self):
        """Test notifications system - GET /api/notifications"""
        if not self.token:
            self.log_test("Notifications System", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        result = self.make_request('GET', 'notifications', headers=headers, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "notifications" in response_data and "unread_count" in response_data:
                notifications = response_data["notifications"]
                unread_count = response_data["unread_count"]
                self.log_test("Notifications System", True, f"Retrieved {len(notifications)} notifications, {unread_count} unread")
                return True
            else:
                self.log_test("Notifications System", False, f"Invalid notifications response format: {response_data}")
        else:
            self.log_test("Notifications System", False, f"Notifications retrieval failed (Status: {result['status_code']})", result)
        return False

    def test_mark_notifications_read(self):
        """Test marking notifications as read - POST /api/notifications/mark-read"""
        if not self.token:
            self.log_test("Mark Notifications Read", False, "No authentication token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # This endpoint expects query params, not body data - send empty body
        try:
            url = f"{self.base_url}/api/notifications/mark-read"
            response = requests.post(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                if "status" in response_data and response_data["status"] == "success":
                    self.log_test("Mark Notifications Read", True, f"Mark all read successful")
                    return True
                else:
                    self.log_test("Mark Notifications Read", False, f"Invalid mark read response: {response_data}")
            else:
                self.log_test("Mark Notifications Read", False, f"Mark notifications read failed (Status: {response.status_code}) - {response.text[:200]}")
        except Exception as e:
            self.log_test("Mark Notifications Read", False, f"Request error: {str(e)}")
        
        return False

    def test_project_chat_messages(self):
        """Test project chat functionality - GET /api/projects/{id}/chat"""
        if not self.token:
            self.log_test("Project Chat Messages", False, "No authentication token available")
            return False
            
        # Use the provided test project ID
        test_project_id = "9e670e52-350a-4e40-8813-808bb1c14e6b"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        result = self.make_request('GET', f'projects/{test_project_id}/chat', headers=headers, expected_status=200)
        
        if result["success"]:
            response_data = result["response"]
            if "messages" in response_data:
                messages = response_data["messages"]
                self.log_test("Project Chat Messages", True, f"Retrieved {len(messages)} chat messages")
                return test_project_id
            else:
                self.log_test("Project Chat Messages", False, f"Invalid chat messages response: {response_data}")
        else:
            # Try with a project we create ourselves if the test project doesn't exist
            project_data = {
                "name": "Chat Test Project",
                "description": "Project for testing chat functionality",
                "project_type": "web",
                "status": "pending",
                "budget": "€1000"
            }
            
            project_result = self.make_request('POST', 'projects', data=project_data, headers=headers, expected_status=200)
            if project_result["success"]:
                new_project_id = project_result["response"]["id"]
                result = self.make_request('GET', f'projects/{new_project_id}/chat', headers=headers, expected_status=200)
                
                if result["success"]:
                    response_data = result["response"]
                    if "messages" in response_data:
                        messages = response_data["messages"]
                        self.log_test("Project Chat Messages", True, f"Retrieved {len(messages)} chat messages from new project")
                        return new_project_id
                    else:
                        self.log_test("Project Chat Messages", False, f"Invalid chat messages response from new project: {response_data}")
                else:
                    self.log_test("Project Chat Messages", False, f"Chat messages failed for new project (Status: {result['status_code']})", result)
            else:
                self.log_test("Project Chat Messages", False, f"Chat messages failed (Status: {result['status_code']})", result)
        return None

    def test_send_chat_message(self):
        """Test sending message to project chat - POST /api/projects/{id}/chat"""
        if not self.token:
            self.log_test("Send Chat Message", False, "No authentication token available")
            return False
            
        # Get a project ID from the chat messages test
        project_id = self.test_project_chat_messages()
        if not project_id:
            self.log_test("Send Chat Message", False, "No project available for chat message test")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Chat endpoint expects form data, not JSON
        try:
            url = f"{self.base_url}/api/projects/{project_id}/chat"
            form_data = {"content": "Test message from API testing"}
            
            response = requests.post(url, data=form_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                if "id" in response_data and "content" in response_data:
                    self.log_test("Send Chat Message", True, f"Message sent successfully: {response_data.get('id', 'unknown ID')}")
                    return True
                else:
                    self.log_test("Send Chat Message", False, f"Invalid send message response: {response_data}")
            else:
                self.log_test("Send Chat Message", False, f"Send chat message failed (Status: {response.status_code}) - {response.text[:200]}")
        except Exception as e:
            self.log_test("Send Chat Message", False, f"Request error: {str(e)}")
        
        return False

    def test_analytics_revenue_admin_only(self):
        """Test analytics revenue endpoint - GET /api/admin/analytics/revenue (admin only)"""
        # First test without admin token - should fail
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        result = self.make_request('GET', 'admin/analytics/revenue', headers=headers, expected_status=403)
        
        if result["status_code"] == 403:
            self.log_test("Analytics Revenue (Non-Admin)", True, "Correctly denied access for non-admin user")
        else:
            self.log_test("Analytics Revenue (Non-Admin)", False, f"Expected 403 for non-admin, got {result['status_code']}")
            
        # Try to create test admin for testing
        admin_data = {
            "name": "Test Admin API",
            "email": f"testadmin_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestAdmin123!"
        }
        
        # Admin setup might fail if admin already exists
        admin_setup = self.make_request('POST', 'admin/setup', data=admin_data, expected_status=200)
        
        if admin_setup["success"]:
            admin_response = admin_setup["response"]
            if "access_token" in admin_response:
                admin_headers = {"Authorization": f"Bearer {admin_response['access_token']}"}
                
                # Test analytics endpoint with admin token
                analytics_result = self.make_request('GET', 'admin/analytics/revenue', headers=admin_headers, expected_status=200)
                
                if analytics_result["success"]:
                    analytics_data = analytics_result["response"]
                    expected_fields = ["total_revenue", "pending_revenue", "paid_projects", "average_project_value"]
                    
                    if any(field in analytics_data for field in expected_fields):
                        self.log_test("Analytics Revenue (Admin)", True, f"Analytics data retrieved successfully with new admin")
                        return True
                    else:
                        self.log_test("Analytics Revenue (Admin)", False, f"Invalid analytics response format: {analytics_data}")
                else:
                    self.log_test("Analytics Revenue (Admin)", False, f"Analytics failed (Status: {analytics_result['status_code']})", analytics_result)
            else:
                self.log_test("Analytics Revenue (Admin)", False, f"Admin setup response missing token: {admin_response}")
        else:
            # Admin setup failed, probably admin already exists
            self.log_test("Analytics Revenue (Admin)", False, f"Cannot create test admin (Status: {admin_setup['status_code']}) - Admin already exists. Cannot test analytics endpoint without admin credentials.")
        
        return False

    def test_stripe_payment_intent_creation(self):
        """Test Stripe Payment Intent creation for project"""
        if not self.token:
            self.log_test("Stripe Payment Intent", False, "No authentication token available")
            return False
        
        # First, create a project and manually set budget status to accepted for testing
        project_data = {
            "name": "Stripe Test Project",
            "description": "Project for testing Stripe payment integration",
            "project_type": "web",
            "status": "pending",
            "budget": "€100"  # Use a valid amount
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        project_result = self.make_request('POST', 'projects', data=project_data, headers=headers, expected_status=200)
        
        if not project_result["success"]:
            self.log_test("Stripe Payment Intent", False, "Failed to create test project for payment")
            return False
            
        project_id = project_result["response"]["id"]
        
        # Try to create payment intent (should fail because budget not approved)
        result = self.make_request('POST', f'projects/{project_id}/create-payment', headers=headers, expected_status=400)
        
        # We expect this to fail with budget not approved - this is correct behavior
        if result["status_code"] == 400:
            error_msg = result.get("response", {}).get("detail", "")
            if "Orçamento não aprovado" in error_msg:
                self.log_test("Stripe Payment Intent", True, "Stripe integration correctly validates budget approval (expected behavior)")
                return True
            else:
                self.log_test("Stripe Payment Intent", False, f"Unexpected error from Stripe: {error_msg}")
        elif result["status_code"] == 500:
            # Check if Stripe is configured
            error_msg = result.get("response", {}).get("detail", "")
            if "Pagamentos não configurados" in error_msg:
                self.log_test("Stripe Payment Intent", False, "Stripe API key not configured properly")
            else:
                self.log_test("Stripe Payment Intent", False, f"Stripe API error: {error_msg}")
        else:
            self.log_test("Stripe Payment Intent", False, f"Payment intent test failed (Status: {result['status_code']})", result)
        return False

    def run_all_tests(self):
        """Run all API tests"""
        logger.info("🚀 Starting Andre Development API Testing...")
        logger.info(f"Testing endpoint: {self.base_url}")
        
        # Core API tests
        self.test_api_health_check()
        self.test_mongodb_connection()
        
        # Authentication tests  
        self.test_user_registration()
        self.test_user_login()
        self.test_protected_route_access()
        
        # Core functionality tests
        self.test_project_creation()
        self.test_get_user_projects()
        
        # NEW FEATURES TESTING - From review request
        logger.info("\n🆕 Testing New Features:")
        self.test_notifications_system()
        self.test_mark_notifications_read() 
        self.test_project_chat_messages()
        self.test_send_chat_message()
        self.test_analytics_revenue_admin_only()
        
        # Public endpoints
        self.test_get_portfolio()
        self.test_contact_form_submission()
        
        # Admin functionality
        self.test_admin_functionality()
        
        # Stripe and Resend integration tests
        self.test_password_reset_email()
        self.test_stripe_payment_intent_creation()
        
        # Print summary
        self.print_summary()
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = len(self.test_results["failed_tests"])
        
        logger.info("\n" + "="*50)
        logger.info("📊 TEST SUMMARY")
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
    """Main function to run tests"""
    tester = AndreDevelopmentAPITester()
    
    try:
        results = tester.run_all_tests()
        
        # Save results to file
        with open("/app/test_results_backend.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Return exit code based on success
        if results["passed_tests"] == results["total_tests"]:
            logger.info("🎉 All tests passed!")
            return 0
        else:
            logger.error(f"💥 {len(results['failed_tests'])} tests failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())