"""
Test suite for Andre Dev Agency - Budget/Counter-Proposal Feature
Tests:
1. Client creates project with MANDATORY budget field
2. Project creation fails without budget
3. Admin views projects with proposed budget
4. Admin responds to budget - accept or counter_proposal
5. Counter proposal requires value
6. Client sees budget status and counter_proposal
7. Contact form submissions appear in admin contacts
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://appagency-fix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

# Test data with unique identifiers
TEST_ID = str(uuid.uuid4())[:8]
TEST_ADMIN_EMAIL = "admin@andredev.pt"  # Use existing admin
TEST_ADMIN_PASSWORD = "admin123"
TEST_CLIENT_EMAIL = f"testclient_{TEST_ID}@test.com"
TEST_CLIENT_PASSWORD = "testclient123"

class TestAdminSetup:
    """Admin account setup tests"""
    
    def test_check_admin_exists(self):
        """Check if admin exists endpoint works"""
        response = requests.get(f"{API}/admin/check")
        assert response.status_code == 200
        data = response.json()
        assert "admin_exists" in data
        print(f"Admin exists: {data['admin_exists']}")

class TestAuthFlow:
    """Authentication flow tests"""
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Register client and get token"""
        # First try to login, if fails then register
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        # Register new client
        response = requests.post(f"{API}/auth/register", json={
            "name": "Test Client Budget",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD,
            "company": "Test Company"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "client"
        print(f"Client registered: {TEST_CLIENT_EMAIL}")
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token - try login first, then setup if needed"""
        # Try login with test credentials first
        admin_emails = ["admin@test.com", TEST_ADMIN_EMAIL]
        admin_password = "admin123"
        
        for email in admin_emails:
            login_response = requests.post(f"{API}/auth/login", json={
                "email": email,
                "password": admin_password
            })
            if login_response.status_code == 200:
                data = login_response.json()
                if data["user"]["role"] == "admin":
                    print(f"Admin logged in: {email}")
                    return data["access_token"]
        
        # Check if admin exists
        check_response = requests.get(f"{API}/admin/check")
        if check_response.status_code == 200 and check_response.json().get("admin_exists"):
            # Admin exists but we couldn't login - skip tests requiring admin
            pytest.skip("Admin exists but credentials not matching")
        
        # Try to setup new admin
        setup_response = requests.post(f"{API}/admin/setup", json={
            "name": "Test Admin",
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        if setup_response.status_code == 200:
            print(f"Admin created: {TEST_ADMIN_EMAIL}")
            return setup_response.json()["access_token"]
        elif setup_response.status_code == 400 and "Já existe" in setup_response.text:
            pytest.skip("Admin already exists")
        else:
            pytest.fail(f"Admin setup failed: {setup_response.text}")

    def test_client_registration(self, client_token):
        """Test client token is valid"""
        response = requests.get(f"{API}/auth/me", headers={
            "Authorization": f"Bearer {client_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "client"
        print(f"Client authenticated: {data['email']}")


class TestProjectBudgetFeature:
    """Main budget feature tests"""
    
    @pytest.fixture(scope="class")
    def client_session(self):
        """Setup client session"""
        # Try login first
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        # Register new client
        response = requests.post(f"{API}/auth/register", json={
            "name": "Test Client Budget",
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD,
            "company": "Test Company"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        elif response.status_code == 400 and "já registado" in response.text.lower():
            # User exists, try to login
            login_response = requests.post(f"{API}/auth/login", json={
                "email": TEST_CLIENT_EMAIL,
                "password": TEST_CLIENT_PASSWORD
            })
            return login_response.json()["access_token"]
        pytest.fail(f"Failed to setup client: {response.text}")
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Setup admin session"""
        # Try login with known admin credentials
        admin_credentials = [
            ("admin@test.com", "admin123"),
            (TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD),
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
        
        # Try admin setup
        check = requests.get(f"{API}/admin/check")
        if check.status_code == 200 and not check.json().get("admin_exists"):
            setup_response = requests.post(f"{API}/admin/setup", json={
                "name": "Test Admin",
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            })
            if setup_response.status_code == 200:
                return setup_response.json()["access_token"]
        
        pytest.skip("Could not get admin access")
    
    def test_01_project_creation_requires_budget(self, client_session):
        """Test 1: Project creation should fail without budget field"""
        # Try to create project without budget - this tests validation
        response = requests.post(f"{API}/projects", 
            headers={"Authorization": f"Bearer {client_session}"},
            json={
                "name": "Test Project No Budget",
                "description": "This should fail",
                "project_type": "web"
            }
        )
        # Pydantic should return 422 for missing required field
        assert response.status_code == 422, f"Expected 422 for missing budget, got {response.status_code}"
        print("PASS: Project creation without budget returns 422 (validation error)")
    
    def test_02_project_creation_with_budget(self, client_session):
        """Test 2: Client creates project with mandatory budget"""
        response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"},
            json={
                "name": f"TEST_Project_Budget_{TEST_ID}",
                "description": "Test project with budget",
                "project_type": "web",
                "budget": "5000€"
            }
        )
        assert response.status_code == 200, f"Project creation failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert data["budget"] == "5000€"
        assert data["budget_status"] == "pending"
        assert data["counter_proposal"] is None
        print(f"PASS: Project created with budget: {data['budget']}, status: {data['budget_status']}")
        return data["id"]
    
    def test_03_client_sees_own_projects_with_budget(self, client_session):
        """Test 3: Client can view their projects with budget info"""
        response = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"}
        )
        assert response.status_code == 200
        projects = response.json()
        
        # Find our test project
        test_projects = [p for p in projects if f"TEST_Project_Budget_{TEST_ID}" in p.get("name", "")]
        assert len(test_projects) > 0, "Test project not found in client's projects"
        
        project = test_projects[0]
        assert "budget" in project
        assert "budget_status" in project
        print(f"PASS: Client sees project with budget: {project['budget']}, status: {project['budget_status']}")
    
    def test_04_admin_views_all_projects_with_budget(self, admin_session):
        """Test 4: Admin can view all projects with proposed budget"""
        response = requests.get(f"{API}/admin/projects",
            headers={"Authorization": f"Bearer {admin_session}"}
        )
        assert response.status_code == 200
        projects = response.json()
        
        # Find our test project
        test_projects = [p for p in projects if f"TEST_Project_Budget_{TEST_ID}" in p.get("name", "")]
        if not test_projects:
            pytest.skip("Test project not found - may have been cleaned up")
        
        project = test_projects[0]
        assert "budget" in project
        assert "user" in project  # Should include user info for admin
        assert project["budget"] == "5000€"
        print(f"PASS: Admin sees project budget: {project['budget']}, client: {project['user']}")
        return project["id"]
    
    def test_05_admin_accepts_budget(self, admin_session, client_session):
        """Test 5a: Admin accepts project budget"""
        # First create a new project for accept test
        create_response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"},
            json={
                "name": f"TEST_Accept_Budget_{TEST_ID}",
                "description": "Project for accept test",
                "project_type": "android",
                "budget": "3000€"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        # Admin accepts budget
        response = requests.put(f"{API}/admin/projects/{project_id}/budget-response",
            headers={"Authorization": f"Bearer {admin_session}"},
            json={
                "budget_status": "accepted",
                "admin_notes": "Budget accepted, project approved"
            }
        )
        assert response.status_code == 200, f"Budget accept failed: {response.text}"
        print("PASS: Admin accepted budget")
        
        # Verify project was updated
        verify_response = requests.get(f"{API}/admin/projects",
            headers={"Authorization": f"Bearer {admin_session}"}
        )
        projects = verify_response.json()
        project = next((p for p in projects if p["id"] == project_id), None)
        assert project is not None
        assert project["budget_status"] == "accepted"
        print(f"PASS: Budget status verified as: {project['budget_status']}")
    
    def test_06_admin_counter_proposal_requires_value(self, admin_session, client_session):
        """Test 5b: Counter proposal requires a value"""
        # Create project for counter proposal test
        create_response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"},
            json={
                "name": f"TEST_Counter_Budget_{TEST_ID}",
                "description": "Project for counter proposal test",
                "project_type": "ios",
                "budget": "8000€"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        # Try counter proposal without value - should fail
        response = requests.put(f"{API}/admin/projects/{project_id}/budget-response",
            headers={"Authorization": f"Bearer {admin_session}"},
            json={
                "budget_status": "counter_proposal"
                # Missing counter_proposal value
            }
        )
        assert response.status_code == 400, f"Expected 400 for missing counter_proposal, got {response.status_code}"
        print("PASS: Counter proposal without value returns 400")
    
    def test_07_admin_counter_proposal_with_value(self, admin_session, client_session):
        """Test 5c: Admin makes counter proposal with value"""
        # Create project for counter proposal
        create_response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"},
            json={
                "name": f"TEST_Counter2_Budget_{TEST_ID}",
                "description": "Project for counter proposal with value",
                "project_type": "hybrid",
                "budget": "10000€"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        # Admin makes counter proposal
        response = requests.put(f"{API}/admin/projects/{project_id}/budget-response",
            headers={"Authorization": f"Bearer {admin_session}"},
            json={
                "budget_status": "counter_proposal",
                "counter_proposal": "12000€",
                "admin_notes": "Additional features require higher budget"
            }
        )
        assert response.status_code == 200, f"Counter proposal failed: {response.text}"
        print("PASS: Admin made counter proposal")
        
        # Verify through admin endpoint
        verify_response = requests.get(f"{API}/admin/projects",
            headers={"Authorization": f"Bearer {admin_session}"}
        )
        projects = verify_response.json()
        project = next((p for p in projects if p["id"] == project_id), None)
        assert project is not None
        assert project["budget_status"] == "counter_proposal"
        assert project["counter_proposal"] == "12000€"
        assert project["admin_notes"] == "Additional features require higher budget"
        print(f"PASS: Counter proposal verified: {project['counter_proposal']}")
        
        return project_id
    
    def test_08_client_sees_counter_proposal(self, client_session, admin_session):
        """Test 6: Client sees budget status and counter proposal"""
        # Create and counter-propose
        create_response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"},
            json={
                "name": f"TEST_ClientView_{TEST_ID}",
                "description": "Client view test",
                "project_type": "web",
                "budget": "7500€"
            }
        )
        project_id = create_response.json()["id"]
        
        # Admin counter proposes
        requests.put(f"{API}/admin/projects/{project_id}/budget-response",
            headers={"Authorization": f"Bearer {admin_session}"},
            json={
                "budget_status": "counter_proposal",
                "counter_proposal": "9000€",
                "admin_notes": "Scope requires more work"
            }
        )
        
        # Client views their projects
        response = requests.get(f"{API}/projects",
            headers={"Authorization": f"Bearer {client_session}"}
        )
        assert response.status_code == 200
        projects = response.json()
        
        project = next((p for p in projects if p["id"] == project_id), None)
        assert project is not None
        assert project["budget_status"] == "counter_proposal"
        assert project["counter_proposal"] == "9000€"
        assert project["admin_notes"] == "Scope requires more work"
        print(f"PASS: Client sees counter proposal - original: {project['budget']}, counter: {project['counter_proposal']}")


class TestContactForm:
    """Contact form tests - Test 7"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session"""
        admin_credentials = [
            ("admin@test.com", "admin123"),
            (TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD),
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
        pytest.skip("No admin access available")
    
    def test_contact_form_submission(self):
        """Test 7a: Contact form submission works"""
        response = requests.post(f"{API}/contact", json={
            "name": f"Test Contact {TEST_ID}",
            "email": f"contact_{TEST_ID}@test.com",
            "phone": "+351 912 345 678",
            "message": "This is a test contact message",
            "service_type": "web"
        })
        assert response.status_code == 200, f"Contact submission failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == f"Test Contact {TEST_ID}"
        print(f"PASS: Contact submitted with ID: {data['id']}")
        return data["id"]
    
    def test_admin_sees_contacts(self, admin_session):
        """Test 7b: Admin can see contact submissions"""
        response = requests.get(f"{API}/admin/contacts",
            headers={"Authorization": f"Bearer {admin_session}"}
        )
        assert response.status_code == 200
        contacts = response.json()
        
        # Find our test contact
        test_contacts = [c for c in contacts if f"Test Contact {TEST_ID}" in c.get("name", "")]
        assert len(test_contacts) > 0, "Test contact not found in admin contacts"
        
        contact = test_contacts[0]
        assert contact["email"] == f"contact_{TEST_ID}@test.com"
        print(f"PASS: Admin sees contact: {contact['name']} - {contact['email']}")


class TestInvalidBudgetStatus:
    """Test invalid budget status values"""
    
    @pytest.fixture(scope="class")
    def sessions(self):
        """Get both client and admin sessions"""
        # Client session
        login_response = requests.post(f"{API}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_CLIENT_PASSWORD
        })
        
        if login_response.status_code != 200:
            register_response = requests.post(f"{API}/auth/register", json={
                "name": "Test Client",
                "email": TEST_CLIENT_EMAIL,
                "password": TEST_CLIENT_PASSWORD
            })
            if register_response.status_code == 200:
                client_token = register_response.json()["access_token"]
            else:
                pytest.skip("Could not get client session")
        else:
            client_token = login_response.json()["access_token"]
        
        # Admin session
        for email, password in [("admin@test.com", "admin123"), (TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)]:
            response = requests.post(f"{API}/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200 and response.json()["user"]["role"] == "admin":
                return {"client": client_token, "admin": response.json()["access_token"]}
        
        pytest.skip("Could not get admin session")
    
    def test_invalid_budget_status_rejected(self, sessions):
        """Test that invalid budget_status is rejected"""
        # Create project
        create_response = requests.post(f"{API}/projects",
            headers={"Authorization": f"Bearer {sessions['client']}"},
            json={
                "name": f"TEST_Invalid_Status_{TEST_ID}",
                "description": "Test invalid status",
                "project_type": "web",
                "budget": "2000€"
            }
        )
        if create_response.status_code != 200:
            pytest.skip("Could not create test project")
        
        project_id = create_response.json()["id"]
        
        # Try invalid budget status
        response = requests.put(f"{API}/admin/projects/{project_id}/budget-response",
            headers={"Authorization": f"Bearer {sessions['admin']}"},
            json={
                "budget_status": "invalid_status"
            }
        )
        assert response.status_code == 400, f"Expected 400 for invalid status, got {response.status_code}"
        print("PASS: Invalid budget status rejected with 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
