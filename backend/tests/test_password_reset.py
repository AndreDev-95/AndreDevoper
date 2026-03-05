"""
Password Reset Feature Tests
Testing: forgot-password, reset-password, verify-reset-token endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://appagency-fix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


class TestForgotPassword:
    """Tests for POST /api/auth/forgot-password"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user for password reset tests"""
        self.test_email = f"TEST_pwreset_{uuid.uuid4().hex[:8]}@test.com"
        self.test_password = "testpass123"
        self.test_name = "Test Reset User"
        
        # Register a test user
        response = requests.post(f"{API}/auth/register", json={
            "name": self.test_name,
            "email": self.test_email,
            "password": self.test_password
        })
        if response.status_code == 200:
            self.test_user_id = response.json().get("user", {}).get("id")
        yield
        # Cleanup would happen here if needed
    
    def test_forgot_password_valid_email_returns_token(self):
        """POST /api/auth/forgot-password should return reset_token for valid email"""
        response = requests.post(f"{API}/auth/forgot-password", json={
            "email": self.test_email
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "reset_token" in data, "Should return reset_token in dev mode"
        assert len(data["reset_token"]) > 0, "Token should not be empty"
        print(f"✓ Forgot password returned token for {self.test_email}")
    
    def test_forgot_password_invalid_email_still_returns_success(self):
        """POST /api/auth/forgot-password should return same message for non-existent email (prevent enumeration)"""
        response = requests.post(f"{API}/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        
        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "message" in data
        # For non-existent email, reset_token should not be included
        print("✓ Forgot password handles non-existent email gracefully")
    
    def test_forgot_password_empty_email_returns_validation_error(self):
        """POST /api/auth/forgot-password should validate email format"""
        response = requests.post(f"{API}/auth/forgot-password", json={
            "email": ""
        })
        
        # Should return validation error
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"
        print("✓ Forgot password validates empty email")


class TestResetPassword:
    """Tests for POST /api/auth/reset-password"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and get reset token"""
        self.test_email = f"TEST_reset_{uuid.uuid4().hex[:8]}@test.com"
        self.test_password = "oldpassword123"
        self.new_password = "newpassword456"
        
        # Register a test user
        reg_response = requests.post(f"{API}/auth/register", json={
            "name": "Test Reset User",
            "email": self.test_email,
            "password": self.test_password
        })
        assert reg_response.status_code == 200, f"Failed to register test user: {reg_response.text}"
        
        # Get reset token
        forgot_response = requests.post(f"{API}/auth/forgot-password", json={
            "email": self.test_email
        })
        assert forgot_response.status_code == 200
        self.reset_token = forgot_response.json().get("reset_token")
        yield
    
    def test_reset_password_with_valid_token_changes_password(self):
        """POST /api/auth/reset-password should change password with valid token"""
        response = requests.post(f"{API}/auth/reset-password", json={
            "token": self.reset_token,
            "new_password": self.new_password
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"✓ Password reset successful: {data['message']}")
        
        # Verify new password works by logging in
        login_response = requests.post(f"{API}/auth/login", json={
            "email": self.test_email,
            "password": self.new_password
        })
        assert login_response.status_code == 200, "Should be able to login with new password"
        print("✓ Login with new password works")
        
        # Verify old password no longer works
        old_login = requests.post(f"{API}/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        assert old_login.status_code == 401, "Old password should no longer work"
        print("✓ Old password no longer works")
    
    def test_reset_password_with_invalid_token_fails(self):
        """POST /api/auth/reset-password should fail with invalid token"""
        response = requests.post(f"{API}/auth/reset-password", json={
            "token": "invalid_token_here",
            "new_password": "newpass123"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Reset password rejects invalid token")
    
    def test_reset_password_with_short_password_fails(self):
        """POST /api/auth/reset-password should validate password length"""
        response = requests.post(f"{API}/auth/reset-password", json={
            "token": self.reset_token,
            "new_password": "abc"  # Too short (< 6 chars)
        })
        
        assert response.status_code == 400, f"Expected 400 for short password, got {response.status_code}"
        data = response.json()
        assert "6 caracteres" in data.get("detail", "").lower() or "detail" in data
        print("✓ Reset password validates password length")
    
    def test_reset_password_token_cannot_be_reused(self):
        """POST /api/auth/reset-password - token should be marked as used after first use"""
        # First use - should succeed
        first_response = requests.post(f"{API}/auth/reset-password", json={
            "token": self.reset_token,
            "new_password": self.new_password
        })
        assert first_response.status_code == 200, "First reset should succeed"
        
        # Second use - should fail
        second_response = requests.post(f"{API}/auth/reset-password", json={
            "token": self.reset_token,
            "new_password": "anotherpassword789"
        })
        assert second_response.status_code == 400, "Second reset with same token should fail"
        print("✓ Reset token cannot be reused")


class TestVerifyResetToken:
    """Tests for GET /api/auth/verify-reset-token"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and get reset token"""
        self.test_email = f"TEST_verify_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register a test user
        requests.post(f"{API}/auth/register", json={
            "name": "Test Verify User",
            "email": self.test_email,
            "password": "testpass123"
        })
        
        # Get reset token
        forgot_response = requests.post(f"{API}/auth/forgot-password", json={
            "email": self.test_email
        })
        self.reset_token = forgot_response.json().get("reset_token")
        yield
    
    def test_verify_reset_token_valid(self):
        """GET /api/auth/verify-reset-token should return valid=true for valid token"""
        response = requests.get(f"{API}/auth/verify-reset-token", params={
            "token": self.reset_token
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("valid") == True, "Token should be valid"
        assert data.get("email") == self.test_email, "Should return correct email"
        print(f"✓ Token verified for {self.test_email}")
    
    def test_verify_reset_token_invalid(self):
        """GET /api/auth/verify-reset-token should return valid=false for invalid token"""
        response = requests.get(f"{API}/auth/verify-reset-token", params={
            "token": "invalid_token"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("valid") == False, "Invalid token should return valid=false"
        print("✓ Invalid token correctly identified")
    
    def test_verify_reset_token_used(self):
        """GET /api/auth/verify-reset-token should return valid=false for used token"""
        # First, use the token
        requests.post(f"{API}/auth/reset-password", json={
            "token": self.reset_token,
            "new_password": "newpassword123"
        })
        
        # Then verify it - should be invalid now
        response = requests.get(f"{API}/auth/verify-reset-token", params={
            "token": self.reset_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == False, "Used token should be invalid"
        print("✓ Used token correctly identified as invalid")


class TestEndToEndPasswordReset:
    """End-to-end password reset flow test"""
    
    def test_complete_password_reset_flow(self):
        """Test complete flow: register -> forgot-password -> verify-token -> reset-password -> login"""
        test_email = f"TEST_e2e_{uuid.uuid4().hex[:8]}@test.com"
        original_password = "originalpass123"
        new_password = "brandnewpass456"
        
        # Step 1: Register user
        reg_response = requests.post(f"{API}/auth/register", json={
            "name": "E2E Test User",
            "email": test_email,
            "password": original_password
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        print(f"✓ Step 1: User registered with {test_email}")
        
        # Step 2: Request password reset
        forgot_response = requests.post(f"{API}/auth/forgot-password", json={
            "email": test_email
        })
        assert forgot_response.status_code == 200
        reset_token = forgot_response.json().get("reset_token")
        assert reset_token, "Should get reset token"
        print("✓ Step 2: Got reset token")
        
        # Step 3: Verify token is valid
        verify_response = requests.get(f"{API}/auth/verify-reset-token", params={
            "token": reset_token
        })
        assert verify_response.status_code == 200
        assert verify_response.json().get("valid") == True
        print("✓ Step 3: Token verified as valid")
        
        # Step 4: Reset password
        reset_response = requests.post(f"{API}/auth/reset-password", json={
            "token": reset_token,
            "new_password": new_password
        })
        assert reset_response.status_code == 200
        print("✓ Step 4: Password reset successful")
        
        # Step 5: Login with new password
        login_response = requests.post(f"{API}/auth/login", json={
            "email": test_email,
            "password": new_password
        })
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        print("✓ Step 5: Login with new password successful")
        
        # Step 6: Verify token is now marked as used
        verify_again = requests.get(f"{API}/auth/verify-reset-token", params={
            "token": reset_token
        })
        assert verify_again.json().get("valid") == False
        print("✓ Step 6: Token correctly marked as used")
        
        print("\n✅ Complete password reset flow passed!")
