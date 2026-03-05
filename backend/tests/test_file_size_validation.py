"""
Test suite for File Size Validation - MongoDB BSON 16MB Document Limit Fix
Tests:
1. Backend: POST /api/projects/{id}/previews should reject base64 data > 15MB with 413 status
2. Backend: POST /api/projects/{id}/files should reject base64 data > 15MB with 413 status
3. Small file uploads should still work correctly
4. URL-based previews should work without size limits
5. Basic project flow still works: Create project, send messages, view project details
"""

import pytest
import requests
import os
import uuid
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://appagency-fix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

# Test data with unique identifiers
TEST_ID = str(uuid.uuid4())[:8]
TEST_ADMIN_EMAIL = f"admin_filetest_{TEST_ID}@test.com"
TEST_ADMIN_PASSWORD = "admin123"
TEST_CLIENT_EMAIL = f"client_filetest_{TEST_ID}@test.com"
TEST_CLIENT_PASSWORD = "client123"

# Size constants (matching backend limits)
MAX_BASE64_SIZE = 15 * 1024 * 1024  # 15MB in base64


class TestSetup:
    """Setup test users and get tokens"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get or create admin token"""
        # Try to login with existing admin accounts
        admin_credentials = [
            ("admin@test.com", "admin123"),
            ("admin@andredev.pt", "admin123"),
        ]
        
        for email, password in admin_credentials:
            response = requests.post(f"{API}/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200:
                data = response.json()
                if data["user"]["role"] == "admin":
                    print(f"Admin logged in: {email}")
                    return data["access_token"]
        
        # Check if admin exists
        check_response = requests.get(f"{API}/admin/check")
        if check_response.status_code == 200 and not check_response.json().get("admin_exists"):
            # Create new admin
            setup_response = requests.post(f"{API}/admin/setup", json={
                "name": "Test Admin FileSize",
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            })
            if setup_response.status_code == 200:
                print(f"Admin created: {TEST_ADMIN_EMAIL}")
                return setup_response.json()["access_token"]
        
        pytest.skip("Could not get admin access")
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Register client and get token"""
        # Try login first
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        # Register new client
        response = requests.post(f"{API}/auth/register", json={
            "name": "Test Client FileSize",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD,
            "company": "Test Company"
        })
        if response.status_code == 200:
            print(f"Client registered: {TEST_CLIENT_EMAIL}")
            return response.json()["access_token"]
        
        pytest.fail(f"Failed to setup client: {response.text}")
    
    @pytest.fixture(scope="class")
    def test_project_id(self, client_token):
        """Create a test project for file uploads"""
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_FileSize_Project_{TEST_ID}",
                "description": "Test project for file size validation",
                "project_type": "web",
                "budget": "5000€"
            }
        )
        assert response.status_code == 200, f"Project creation failed: {response.text}"
        project_id = response.json()["id"]
        print(f"Test project created: {project_id}")
        return project_id

    def test_health_check(self):
        """Verify API is accessible"""
        response = requests.get(f"{API}/")
        assert response.status_code == 200
        print("API health check passed")


class TestFileSizeValidation:
    """Test file size validation for files endpoint"""
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token"""
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        # Register
        response = requests.post(f"{API}/auth/register", json={
            "name": "Test Client FileSize",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_project_id(self, client_token):
        """Create project for tests"""
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_FileValidation_{TEST_ID}",
                "description": "Test project",
                "project_type": "web",
                "budget": "3000€"
            }
        )
        if response.status_code == 200:
            return response.json()["id"]
        pytest.fail(f"Could not create project: {response.text}")
    
    def test_01_small_file_upload_works(self, client_token, test_project_id):
        """Test 1: Small file upload should succeed"""
        # Create a small base64 string (about 1KB)
        small_data = base64.b64encode(b"Test file content " * 50).decode('utf-8')
        
        response = requests.post(f"{API}/projects/{test_project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "filename": "small_test_file.txt",
                "file_data": small_data
            }
        )
        assert response.status_code == 200, f"Small file upload failed: {response.text}"
        data = response.json()
        assert "data" in data
        assert data["data"]["filename"] == "small_test_file.txt"
        print(f"PASS: Small file uploaded successfully (size: {len(small_data)} bytes)")
    
    def test_02_large_file_upload_rejected_with_413(self, client_token, test_project_id):
        """Test 2: Large file (>15MB base64) should be rejected with 413"""
        # Create a base64 string larger than 15MB
        # 15MB in base64 = ~15 * 1024 * 1024 characters
        large_size = 16 * 1024 * 1024  # 16MB - definitely over limit
        large_data = "A" * large_size  # Simple base64-like string
        
        response = requests.post(f"{API}/projects/{test_project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "filename": "large_test_file.bin",
                "file_data": large_data
            }
        )
        
        assert response.status_code == 413, f"Expected 413 for large file, got {response.status_code}: {response.text}"
        
        # Verify error message mentions size limit
        error_detail = response.json().get("detail", "")
        assert "grande" in error_detail.lower() or "limit" in error_detail.lower() or "12mb" in error_detail.lower(), \
            f"Error message should mention file size: {error_detail}"
        
        print(f"PASS: Large file ({large_size // (1024*1024)}MB) rejected with 413")
        print(f"Error message: {error_detail}")
    
    def test_03_url_based_file_upload_works(self, client_token, test_project_id):
        """Test 3: URL-based file (no size limit) should work"""
        response = requests.post(f"{API}/projects/{test_project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "filename": "external_file.pdf",
                "file_url": "https://example.com/large-file.pdf"
            }
        )
        assert response.status_code == 200, f"URL file upload failed: {response.text}"
        data = response.json()
        assert data["data"]["file_url"] == "https://example.com/large-file.pdf"
        print("PASS: URL-based file upload works without size limit")


class TestPreviewSizeValidation:
    """Test file size validation for previews endpoint (admin only)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        admin_credentials = [
            ("admin@test.com", "admin123"),
            ("admin@andredev.pt", "admin123"),
        ]
        
        for email, password in admin_credentials:
            response = requests.post(f"{API}/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200:
                data = response.json()
                if data["user"]["role"] == "admin":
                    return data["access_token"]
        
        # Try setup
        check = requests.get(f"{API}/admin/check")
        if check.status_code == 200 and not check.json().get("admin_exists"):
            setup = requests.post(f"{API}/admin/setup", json={
                "name": "Admin Preview Test",
                "email": f"adminpreview_{TEST_ID}@test.com",
                "password": "admin123"
            })
            if setup.status_code == 200:
                return setup.json()["access_token"]
        
        pytest.skip("Could not get admin access")
    
    @pytest.fixture(scope="class")
    def test_project_id(self, admin_token):
        """Get or create a project for preview tests"""
        # Get existing projects
        response = requests.get(f"{API}/admin/projects",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            projects = response.json()
            if projects:
                return projects[0]["id"]
        
        # Need to create as client first
        # Register client
        client_email = f"previewclient_{TEST_ID}@test.com"
        reg_response = requests.post(f"{API}/auth/register", json={
            "name": "Preview Test Client",
            "email": client_email,
            "password": "client123"
        })
        if reg_response.status_code == 200:
            client_token = reg_response.json()["access_token"]
        else:
            # Try login
            login = requests.post(f"{API}/auth/login", json={
                "email": client_email,
                "password": "client123"
            })
            if login.status_code == 200:
                client_token = login.json()["access_token"]
            else:
                pytest.skip("Could not create client for preview test")
        
        # Create project
        proj_response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_Preview_Project_{TEST_ID}",
                "description": "Preview size validation test",
                "project_type": "web",
                "budget": "2000€"
            }
        )
        if proj_response.status_code == 200:
            return proj_response.json()["id"]
        
        pytest.skip("Could not create project for preview tests")
    
    def test_04_small_preview_upload_works(self, admin_token, test_project_id):
        """Test 4: Small image preview upload should succeed"""
        # Create a small base64 image (simulated)
        small_data = base64.b64encode(b"PNG IMAGE DATA " * 100).decode('utf-8')
        
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "Small test preview",
                "image_data": small_data,
                "mime_type": "image/png"
            }
        )
        assert response.status_code == 200, f"Small preview upload failed: {response.text}"
        data = response.json()
        assert data["data"]["description"] == "Small test preview"
        print(f"PASS: Small preview uploaded successfully (size: {len(small_data)} bytes)")
    
    def test_05_large_preview_upload_rejected_with_413(self, admin_token, test_project_id):
        """Test 5: Large preview (>15MB base64) should be rejected with 413"""
        # Create data larger than 15MB
        large_size = 16 * 1024 * 1024  # 16MB
        large_data = "B" * large_size
        
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "Large test preview",
                "image_data": large_data,
                "mime_type": "video/mp4"
            }
        )
        
        assert response.status_code == 413, f"Expected 413 for large preview, got {response.status_code}: {response.text}"
        
        error_detail = response.json().get("detail", "")
        assert "grande" in error_detail.lower() or "limit" in error_detail.lower() or "12mb" in error_detail.lower(), \
            f"Error message should mention size: {error_detail}"
        
        print(f"PASS: Large preview ({large_size // (1024*1024)}MB) rejected with 413")
        print(f"Error message: {error_detail}")
    
    def test_06_url_based_preview_works(self, admin_token, test_project_id):
        """Test 6: URL-based preview should work without size restrictions"""
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "YouTube video preview",
                "image_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        )
        assert response.status_code == 200, f"URL preview upload failed: {response.text}"
        data = response.json()
        assert data["data"]["image_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print("PASS: URL-based preview works for large content")
    
    def test_07_non_admin_cannot_add_previews(self, test_project_id):
        """Test 7: Non-admin users should not be able to add previews"""
        # Get client token
        client_email = f"nonadmin_{TEST_ID}@test.com"
        reg_response = requests.post(f"{API}/auth/register", json={
            "name": "Non Admin User",
            "email": client_email,
            "password": "client123"
        })
        if reg_response.status_code == 200:
            client_token = reg_response.json()["access_token"]
        else:
            login = requests.post(f"{API}/auth/login", json={
                "email": client_email,
                "password": "client123"
            })
            client_token = login.json()["access_token"]
        
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "description": "Unauthorized preview",
                "image_url": "https://example.com/image.png"
            }
        )
        
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("PASS: Non-admin cannot add previews (403 Forbidden)")


class TestBasicProjectFlow:
    """Test that basic project flows still work after the fix"""
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token"""
        client_email = f"flowclient_{TEST_ID}@test.com"
        login_response = requests.post(f"{API}/auth/login", json={
            "email": client_email,
            "password": "client123"
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        response = requests.post(f"{API}/auth/register", json={
            "name": "Flow Test Client",
            "email": client_email,
            "password": "client123"
        })
        return response.json()["access_token"]
    
    def test_08_create_project(self, client_token):
        """Test 8: Create project works"""
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_BasicFlow_{TEST_ID}",
                "description": "Basic flow test project",
                "project_type": "android",
                "budget": "7000€"
            }
        )
        assert response.status_code == 200, f"Project creation failed: {response.text}"
        data = response.json()
        assert data["name"] == f"TEST_BasicFlow_{TEST_ID}"
        assert data["budget"] == "7000€"
        print(f"PASS: Project created: {data['id']}")
        return data["id"]
    
    def test_09_send_message(self, client_token):
        """Test 9: Send message to project works"""
        # Get project
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects available for message test")
        
        project_id = projects[0]["id"]
        
        response = requests.post(f"{API}/projects/{project_id}/messages",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "content": f"Test message {TEST_ID}"
            }
        )
        assert response.status_code == 200, f"Message send failed: {response.text}"
        print("PASS: Message sent to project")
    
    def test_10_view_project_details(self, client_token):
        """Test 10: View project details works"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects to view")
        
        project_id = projects[0]["id"]
        
        response = requests.get(f"{API}/projects/{project_id}",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200, f"Project details fetch failed: {response.text}"
        data = response.json()
        assert "name" in data
        assert "budget" in data
        assert "budget_status" in data
        print(f"PASS: Project details retrieved: {data['name']}")
    
    def test_11_get_project_messages(self, client_token):
        """Test 11: Get project messages works"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects")
        
        project_id = projects[0]["id"]
        
        response = requests.get(f"{API}/projects/{project_id}/messages",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200, f"Messages fetch failed: {response.text}"
        messages = response.json()
        assert isinstance(messages, list)
        print(f"PASS: Retrieved {len(messages)} messages from project")
    
    def test_12_get_project_files(self, client_token):
        """Test 12: Get project files works"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects")
        
        project_id = projects[0]["id"]
        
        response = requests.get(f"{API}/projects/{project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200, f"Files fetch failed: {response.text}"
        files = response.json()
        assert isinstance(files, list)
        print(f"PASS: Retrieved {len(files)} files from project")
    
    def test_13_get_project_previews(self, client_token):
        """Test 13: Get project previews works"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects")
        
        project_id = projects[0]["id"]
        
        response = requests.get(f"{API}/projects/{project_id}/previews",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200, f"Previews fetch failed: {response.text}"
        previews = response.json()
        assert isinstance(previews, list)
        print(f"PASS: Retrieved {len(previews)} previews from project")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
