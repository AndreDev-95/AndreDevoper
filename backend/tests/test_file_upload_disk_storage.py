"""
Test suite for File Upload Disk Storage Implementation
Tests the NEW implementation that saves files to disk instead of storing base64 in MongoDB.

Tests:
1. POST /api/projects/{id}/files - saves file to /app/backend/uploads/files/
2. POST /api/projects/{id}/previews - saves preview to /app/backend/uploads/previews/
3. GET /uploads/files/* - static file serving
4. GET /uploads/previews/* - static file serving
5. Frontend URL format handling
6. Basic project flow: Create project, send messages, add preview, view preview
"""

import pytest
import requests
import os
import uuid
import base64
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://appagency-fix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

# Test data with unique identifiers
TEST_ID = str(uuid.uuid4())[:8]
TEST_ADMIN_EMAIL = f"admin_disk_{TEST_ID}@test.com"
TEST_ADMIN_PASSWORD = "admin123"
TEST_CLIENT_EMAIL = f"client_disk_{TEST_ID}@test.com"
TEST_CLIENT_PASSWORD = "client123"


class TestHealthCheck:
    """Verify API and static files are accessible"""
    
    def test_api_health(self):
        """Test 1: API is accessible"""
        response = requests.get(f"{API}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"PASS: API health check - {data['message']}")
    
    def test_uploads_directory_accessible(self):
        """Test 2: Static uploads directory should be accessible"""
        # Test accessing uploads path - should return 404 for non-existent file (not 403)
        response = requests.get(f"{BASE_URL}/uploads/test-nonexistent.txt")
        # 404 is expected for non-existent files, 403/500 would indicate misconfiguration
        assert response.status_code in [404, 200], f"Unexpected status: {response.status_code}"
        print(f"PASS: /uploads path is configured (status: {response.status_code} for missing file)")


class TestUserSetup:
    """Setup test users for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get or create admin token"""
        # Try existing admin accounts
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
                if data.get("user", {}).get("role") == "admin":
                    print(f"Admin logged in: {email}")
                    return data["access_token"]
        
        # Check if admin exists
        check = requests.get(f"{API}/admin/check")
        if check.status_code == 200 and not check.json().get("admin_exists"):
            setup = requests.post(f"{API}/admin/setup", json={
                "name": "Test Admin DiskStorage",
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            })
            if setup.status_code == 200:
                print(f"Admin created: {TEST_ADMIN_EMAIL}")
                return setup.json()["access_token"]
        
        pytest.skip("Could not get admin access")
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token"""
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        response = requests.post(f"{API}/auth/register", json={
            "name": "Test Client DiskStorage",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD,
            "company": "Test Company"
        })
        if response.status_code == 200:
            print(f"Client registered: {TEST_CLIENT_EMAIL}")
            return response.json()["access_token"]
        
        pytest.fail(f"Failed to setup client: {response.text}")
    
    def test_client_auth(self, client_token):
        """Test 3: Client authentication works"""
        assert client_token is not None
        response = requests.get(f"{API}/auth/me", 
            headers={"Authorization": f"Bearer {client_token}"})
        assert response.status_code == 200
        print("PASS: Client authentication works")


class TestFileUploadDiskStorage:
    """Test file uploads save to disk and return correct URLs"""
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token"""
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        response = requests.post(f"{API}/auth/register", json={
            "name": "Test Client DiskStorage",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_project_id(self, client_token):
        """Create test project"""
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_DiskStorage_{TEST_ID}",
                "description": "Test project for disk storage file uploads",
                "project_type": "web",
                "budget": "5000€"
            }
        )
        assert response.status_code == 200, f"Project creation failed: {response.text}"
        project_id = response.json()["id"]
        print(f"Test project created: {project_id}")
        return project_id
    
    def test_04_file_upload_returns_disk_url(self, client_token, test_project_id):
        """Test 4: File upload should return /uploads/files/* URL"""
        # Create a small test file content
        test_content = b"Test file content for disk storage validation"
        file_data = base64.b64encode(test_content).decode('utf-8')
        
        response = requests.post(f"{API}/projects/{test_project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "filename": "test_document.txt",
                "file_data": file_data
            }
        )
        
        assert response.status_code == 200, f"File upload failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "data" in data, "Response should contain 'data' field"
        file_entry = data["data"]
        assert "file_url" in file_entry, "File entry should have file_url"
        assert "filename" in file_entry, "File entry should have filename"
        assert "id" in file_entry, "File entry should have id"
        
        # Validate file_url format - should be /api/uploads/files/...
        file_url = file_entry["file_url"]
        assert file_url.startswith("/api/uploads/files/"), f"file_url should start with /api/uploads/files/, got: {file_url}"
        assert file_entry["filename"] == "test_document.txt"
        
        print(f"PASS: File upload returned disk URL: {file_url}")
        return file_url
    
    def test_05_uploaded_file_is_accessible(self, client_token, test_project_id):
        """Test 5: Uploaded file should be accessible via static serving"""
        # First upload a file
        test_content = b"Accessible file content test"
        file_data = base64.b64encode(test_content).decode('utf-8')
        
        upload_response = requests.post(f"{API}/projects/{test_project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "filename": "accessible_file.txt",
                "file_data": file_data
            }
        )
        
        assert upload_response.status_code == 200
        file_url = upload_response.json()["data"]["file_url"]
        
        # Now try to access the file
        full_url = f"{BASE_URL}{file_url}"
        access_response = requests.get(full_url)
        
        assert access_response.status_code == 200, f"Failed to access uploaded file at {full_url}: {access_response.status_code}"
        assert access_response.content == test_content, "Downloaded content doesn't match uploaded content"
        
        print(f"PASS: Uploaded file accessible at {full_url}")
    
    def test_06_get_project_files_returns_disk_urls(self, client_token, test_project_id):
        """Test 6: GET /projects/{id}/files returns files with disk URLs"""
        response = requests.get(f"{API}/projects/{test_project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get files: {response.text}"
        files = response.json()
        
        assert isinstance(files, list), "Response should be a list"
        assert len(files) > 0, "Should have uploaded files"
        
        for file_entry in files:
            if file_entry.get("file_url"):
                # Verify URL format
                url = file_entry["file_url"]
                assert url.startswith("/api/uploads/files/") or url.startswith("http"), \
                    f"Invalid file URL format: {url}"
        
        print(f"PASS: Retrieved {len(files)} files with proper URLs")


class TestPreviewUploadDiskStorage:
    """Test preview uploads save to disk and return correct URLs"""
    
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
                if data.get("user", {}).get("role") == "admin":
                    return data["access_token"]
        
        # Try setup
        check = requests.get(f"{API}/admin/check")
        if check.status_code == 200 and not check.json().get("admin_exists"):
            setup = requests.post(f"{API}/admin/setup", json={
                "name": "Admin Preview DiskTest",
                "email": f"adminprev_{TEST_ID}@test.com",
                "password": "admin123"
            })
            if setup.status_code == 200:
                return setup.json()["access_token"]
        
        pytest.skip("Could not get admin access")
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token for project creation"""
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        response = requests.post(f"{API}/auth/register", json={
            "name": "Client Preview Test",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_project_id(self, client_token):
        """Create or get a project for preview tests"""
        # Check existing projects
        response = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        if response.status_code == 200:
            projects = response.json()
            for p in projects:
                if "TEST_DiskStorage" in p["name"]:
                    return p["id"]
        
        # Create new project
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_PreviewDisk_{TEST_ID}",
                "description": "Preview disk storage test",
                "project_type": "web",
                "budget": "3000€"
            }
        )
        if response.status_code == 200:
            return response.json()["id"]
        
        pytest.skip("Could not create project for preview tests")
    
    def test_07_preview_upload_returns_disk_url(self, admin_token, test_project_id):
        """Test 7: Preview upload should return /uploads/previews/* URL"""
        # Create a small "image" (just binary data for testing)
        test_image_data = b"PNG FAKE IMAGE DATA FOR TESTING " * 10
        image_base64 = base64.b64encode(test_image_data).decode('utf-8')
        
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "Test preview image",
                "image_data": image_base64,
                "mime_type": "image/png"
            }
        )
        
        assert response.status_code == 200, f"Preview upload failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "data" in data, "Response should contain 'data' field"
        preview_entry = data["data"]
        assert "image_url" in preview_entry, "Preview entry should have image_url"
        assert "id" in preview_entry, "Preview entry should have id"
        
        # Validate image_url format - should be /api/uploads/previews/...
        image_url = preview_entry["image_url"]
        assert image_url.startswith("/api/uploads/previews/"), \
            f"image_url should start with /api/uploads/previews/, got: {image_url}"
        
        print(f"PASS: Preview upload returned disk URL: {image_url}")
        return image_url
    
    def test_08_preview_file_is_accessible(self, admin_token, test_project_id):
        """Test 8: Uploaded preview should be accessible via static serving"""
        # Upload a preview
        test_image_data = b"ACCESSIBLE PREVIEW IMAGE DATA"
        image_base64 = base64.b64encode(test_image_data).decode('utf-8')
        
        upload_response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "Accessible preview test",
                "image_data": image_base64,
                "mime_type": "image/jpeg"
            }
        )
        
        assert upload_response.status_code == 200
        image_url = upload_response.json()["data"]["image_url"]
        
        # Access the file
        full_url = f"{BASE_URL}{image_url}"
        access_response = requests.get(full_url)
        
        assert access_response.status_code == 200, \
            f"Failed to access preview at {full_url}: {access_response.status_code}"
        assert access_response.content == test_image_data, \
            "Downloaded preview content doesn't match uploaded content"
        
        print(f"PASS: Preview accessible at {full_url}")
    
    def test_09_video_preview_upload_works(self, admin_token, test_project_id):
        """Test 9: Video preview upload (MP4 mime type) works"""
        # Simulate video data
        test_video_data = b"MP4 VIDEO DATA SIMULATION " * 100
        video_base64 = base64.b64encode(test_video_data).decode('utf-8')
        
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "Video preview test",
                "image_data": video_base64,
                "mime_type": "video/mp4"
            }
        )
        
        assert response.status_code == 200, f"Video preview upload failed: {response.text}"
        data = response.json()
        
        image_url = data["data"]["image_url"]
        assert image_url.endswith(".mp4"), f"Video should have .mp4 extension: {image_url}"
        assert image_url.startswith("/api/uploads/previews/")
        
        print(f"PASS: Video preview uploaded: {image_url}")
    
    def test_10_url_based_preview_still_works(self, admin_token, test_project_id):
        """Test 10: URL-based preview (no file upload) still works"""
        response = requests.post(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "description": "External URL preview",
                "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600"
            }
        )
        
        assert response.status_code == 200, f"URL preview failed: {response.text}"
        data = response.json()
        
        image_url = data["data"]["image_url"]
        assert image_url == "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600"
        
        print("PASS: URL-based preview works")
    
    def test_11_get_project_previews_returns_correct_urls(self, admin_token, test_project_id):
        """Test 11: GET /projects/{id}/previews returns previews with correct URLs"""
        response = requests.get(f"{API}/projects/{test_project_id}/previews",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get previews: {response.text}"
        previews = response.json()
        
        assert isinstance(previews, list), "Response should be a list"
        assert len(previews) > 0, "Should have uploaded previews"
        
        disk_urls = 0
        external_urls = 0
        
        for preview in previews:
            url = preview.get("image_url", "")
            if url.startswith("/api/uploads/"):
                disk_urls += 1
            elif url.startswith("http"):
                external_urls += 1
        
        print(f"PASS: Retrieved {len(previews)} previews ({disk_urls} disk, {external_urls} external)")


class TestBasicProjectFlow:
    """Test basic project flow still works with new file storage"""
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token"""
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        response = requests.post(f"{API}/auth/register", json={
            "name": "Flow Test Client",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_12_create_project(self, client_token):
        """Test 12: Create project works"""
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "name": f"TEST_Flow_{TEST_ID}",
                "description": "Basic flow test",
                "project_type": "android",
                "budget": "4000€"
            }
        )
        assert response.status_code == 200, f"Project creation failed: {response.text}"
        data = response.json()
        assert data["name"] == f"TEST_Flow_{TEST_ID}"
        print(f"PASS: Project created: {data['id']}")
        return data["id"]
    
    def test_13_send_message_to_project(self, client_token):
        """Test 13: Send message to project"""
        # Get a project
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects available")
        
        project_id = projects[0]["id"]
        
        response = requests.post(f"{API}/projects/{project_id}/messages",
            headers={"Authorization": f"Bearer {client_token}"},
            json={"content": f"Test message {TEST_ID}"}
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        print("PASS: Message sent successfully")
    
    def test_14_view_project_with_files_and_previews(self, client_token):
        """Test 14: View project details with files and previews"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects")
        
        project_id = projects[0]["id"]
        
        # Get project details
        project_response = requests.get(f"{API}/projects/{project_id}",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert project_response.status_code == 200
        
        # Get files
        files_response = requests.get(f"{API}/projects/{project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert files_response.status_code == 200
        
        # Get previews
        previews_response = requests.get(f"{API}/projects/{project_id}/previews",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert previews_response.status_code == 200
        
        print(f"PASS: Project view works - Files: {len(files_response.json())}, Previews: {len(previews_response.json())}")


class TestFrontendURLCompatibility:
    """Test that frontend URL handling works correctly"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        admin_credentials = [("admin@test.com", "admin123"), ("admin@andredev.pt", "admin123")]
        for email, password in admin_credentials:
            response = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
            if response.status_code == 200 and response.json().get("user", {}).get("role") == "admin":
                return response.json()["access_token"]
        pytest.skip("No admin access")
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client token"""
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL, "password": TEST_CLIENT_PASSWORD
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        response = requests.post(f"{API}/auth/register", json={
            "name": "URL Test Client", "email": TEST_CLIENT_EMAIL, "password": TEST_CLIENT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_15_frontend_url_format_for_files(self, client_token):
        """Test 15: Files have URLs that work with frontend BACKEND_URL prepending"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects")
        
        project_id = projects[0]["id"]
        files = requests.get(f"{API}/projects/{project_id}/files",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        for file_entry in files:
            file_url = file_entry.get("file_url", "")
            if file_url.startswith("/api/uploads/"):
                # Frontend would do: BACKEND_URL + file_url
                full_url = f"{BASE_URL}{file_url}"
                response = requests.get(full_url)
                assert response.status_code == 200, f"Frontend URL pattern failed: {full_url}"
        
        print("PASS: File URLs work with frontend BACKEND_URL prepending")
    
    def test_16_frontend_url_format_for_previews(self, admin_token, client_token):
        """Test 16: Previews have URLs that work with frontend BACKEND_URL prepending"""
        projects = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        if not projects:
            pytest.skip("No projects")
        
        project_id = projects[0]["id"]
        previews = requests.get(f"{API}/projects/{project_id}/previews",
            headers={"Authorization": f"Bearer {client_token}"}
        ).json()
        
        for preview in previews:
            image_url = preview.get("image_url", "")
            if image_url.startswith("/api/uploads/"):
                # Frontend would do: BACKEND_URL + image_url
                full_url = f"{BASE_URL}{image_url}"
                response = requests.get(full_url)
                assert response.status_code == 200, f"Frontend preview URL failed: {full_url}"
        
        print("PASS: Preview URLs work with frontend BACKEND_URL prepending")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
