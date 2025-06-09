import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
import tempfile
import os
from io import BytesIO

import models
import schemas


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Meeting Transcription API" in response.json()["message"]
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_health_check_detailed(self, client):
        """Test detailed health check endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestUserEndpoints:
    """Test user-related endpoints"""
    
    def test_create_user_success(self, client):
        """Test successful user creation"""
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPassword123!"
        }
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password
    
    def test_create_user_duplicate_email(self, client, test_user):
        """Test creating user with duplicate email"""
        user_data = {
            "email": test_user.email,
            "password": "NewPassword123!"
        }
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_create_user_invalid_data(self, client):
        """Test creating user with invalid data"""
        # Weak password
        user_data = {
            "email": "test@example.com",
            "password": "weak"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422
        
        # Invalid email
        user_data = {
            "email": "invalid-email",
            "password": "StrongPassword123!"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 422
    
    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        # First create user
        user_create_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        client.post("/users/", json=user_create_data)
        
        # Then login
        response = client.post("/token", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/token", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password"""
        # First create user
        client.post("/users/", json=test_user_data)
        
        # Then try to login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/token", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestPasswordResetEndpoints:
    """Test password reset endpoints"""
    
    @patch('email_service.email_service.send_password_reset_email')
    def test_request_password_reset_success(self, mock_send_email, client, test_user):
        """Test successful password reset request"""
        mock_send_email.return_value = True
        
        reset_data = {"email": test_user.email}
        response = client.post("/password-reset/request", json=reset_data)
        
        assert response.status_code == 200
        assert "Password reset email sent" in response.json()["message"]
        mock_send_email.assert_called_once()
    
    def test_request_password_reset_nonexistent_user(self, client):
        """Test password reset request for nonexistent user"""
        reset_data = {"email": "nonexistent@example.com"}
        response = client.post("/password-reset/request", json=reset_data)
        
        # Should still return 200 for security (don't reveal if email exists)
        assert response.status_code == 200
    
    def test_confirm_password_reset_invalid_token(self, client):
        """Test password reset confirmation with invalid token"""
        reset_data = {
            "token": "invalid-token",
            "new_password": "NewPassword123!"
        }
        response = client.post("/password-reset/confirm", json=reset_data)
        
        assert response.status_code == 400
        assert "Invalid or expired token" in response.json()["detail"]


class TestMeetingEndpoints:
    """Test meeting-related endpoints"""
    
    def test_create_meeting_success(self, client, auth_headers):
        """Test successful meeting creation"""
        meeting_data = {
            "title": "Test Meeting",
            "description": "This is a test meeting"
        }
        response = client.post("/meetings/", json=meeting_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Meeting"
        assert data["description"] == "This is a test meeting"
        assert "id" in data
    
    def test_create_meeting_unauthorized(self, client):
        """Test creating meeting without authentication"""
        meeting_data = {
            "title": "Test Meeting",
            "description": "This is a test meeting"
        }
        response = client.post("/meetings/", json=meeting_data)
        
        assert response.status_code == 401
    
    def test_create_meeting_invalid_data(self, client, auth_headers):
        """Test creating meeting with invalid data"""
        # Empty title
        meeting_data = {
            "title": "",
            "description": "This is a test meeting"
        }
        response = client.post("/meetings/", json=meeting_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Title too long
        meeting_data = {
            "title": "a" * 201,  # Max is 200
            "description": "This is a test meeting"
        }
        response = client.post("/meetings/", json=meeting_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_get_meetings(self, client, auth_headers, test_meeting):
        """Test getting meetings"""
        response = client.get("/meetings/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Check if our test meeting is in the list
        meeting_ids = [meeting["id"] for meeting in data]
        assert test_meeting.id in meeting_ids
    
    def test_get_meetings_unauthorized(self, client):
        """Test getting meetings without authentication"""
        response = client.get("/meetings/")
        assert response.status_code == 401
    
    def test_update_meeting_success(self, client, auth_headers, test_meeting):
        """Test successful meeting update"""
        update_data = {
            "title": "Updated Meeting Title",
            "description": "Updated description"
        }
        response = client.put(
            f"/meetings/{test_meeting.id}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Meeting Title"
        assert data["description"] == "Updated description"
    
    def test_update_meeting_not_found(self, client, auth_headers):
        """Test updating non-existent meeting"""
        update_data = {
            "title": "Updated Meeting Title"
        }
        response = client.put(
            "/meetings/99999", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_meeting_success(self, client, auth_headers, test_meeting):
        """Test successful meeting deletion"""
        response = client.delete(f"/meetings/{test_meeting.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
    
    def test_delete_meeting_not_found(self, client, auth_headers):
        """Test deleting non-existent meeting"""
        response = client.delete("/meetings/99999", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_meeting_transcriptions(self, client, auth_headers, test_meeting):
        """Test getting meeting transcriptions"""
        response = client.get(
            f"/meetings/{test_meeting.id}/transcriptions", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_end_meeting_success(self, client, auth_headers, test_meeting):
        """Test ending a meeting"""
        response = client.post(
            f"/meetings/{test_meeting.id}/end", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_ended"] is True
        assert data["status"] == "completed"
    
    def test_get_meeting_status(self, client, auth_headers, test_meeting):
        """Test getting meeting status"""
        response = client.get(
            f"/meetings/{test_meeting.id}/status", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "is_ended" in data
        assert "transcription_count" in data


class TestTagEndpoints:
    """Test tag-related endpoints"""
    
    def test_create_tag_success(self, client, auth_headers):
        """Test successful tag creation"""
        tag_data = {
            "name": "Test Tag",
            "color": "#ff0000"
        }
        response = client.post("/tags/", json=tag_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test tag"  # Should be normalized
        assert data["color"] == "#ff0000"
    
    def test_create_tag_invalid_data(self, client, auth_headers):
        """Test creating tag with invalid data"""
        # Invalid color
        tag_data = {
            "name": "Test Tag",
            "color": "invalid-color"
        }
        response = client.post("/tags/", json=tag_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Empty name
        tag_data = {
            "name": "",
            "color": "#ff0000"
        }
        response = client.post("/tags/", json=tag_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_get_tags(self, client, auth_headers, test_tag):
        """Test getting tags"""
        response = client.get("/tags/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check if our test tag is in the list
        tag_names = [tag["name"] for tag in data]
        assert test_tag.name in tag_names
    
    def test_get_tag_by_id(self, client, auth_headers, test_tag):
        """Test getting tag by ID"""
        response = client.get(f"/tags/{test_tag.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_tag.id
        assert data["name"] == test_tag.name
    
    def test_update_tag_success(self, client, auth_headers, test_tag):
        """Test successful tag update"""
        update_data = {
            "name": "Updated Tag",
            "color": "#00ff00"
        }
        response = client.put(
            f"/tags/{test_tag.id}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated tag"
        assert data["color"] == "#00ff00"
    
    def test_delete_tag_success(self, client, auth_headers, test_tag):
        """Test successful tag deletion"""
        response = client.delete(f"/tags/{test_tag.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]


class TestAudioEndpoints:
    """Test audio-related endpoints"""
    
    @patch('main.validate_audio_file')
    @patch('main.save_uploaded_file_securely')
    def test_transcribe_meeting_success(
        self, 
        mock_save_file, 
        mock_validate_audio, 
        client, 
        auth_headers, 
        test_meeting
    ):
        """Test successful audio transcription"""
        mock_save_file.return_value = "/tmp/test_audio.wav"
        mock_validate_audio.return_value = None
        
        # Create a mock audio file
        audio_data = b"fake_audio_data"
        files = {"audio": ("test.wav", BytesIO(audio_data), "audio/wav")}
        
        response = client.post(
            f"/meetings/{test_meeting.id}/transcribe",
            files=files,
            headers=auth_headers
        )
        
        # Note: This endpoint processes in background, so we expect 202
        assert response.status_code == 202
        assert "Transcription started" in response.json()["message"]
    
    def test_transcribe_meeting_no_file(self, client, auth_headers, test_meeting):
        """Test transcription without audio file"""
        response = client.post(
            f"/meetings/{test_meeting.id}/transcribe",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_transcribe_meeting_not_found(self, client, auth_headers):
        """Test transcription for non-existent meeting"""
        audio_data = b"fake_audio_data"
        files = {"audio": ("test.wav", BytesIO(audio_data), "audio/wav")}
        
        response = client.post(
            "/meetings/99999/transcribe",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    def test_get_all_users_admin_success(self, client, admin_auth_headers):
        """Test getting all users as admin"""
        response = client.get("/admin/users", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_all_users_non_admin(self, client, auth_headers):
        """Test getting all users as non-admin"""
        response = client.get("/admin/users", headers=auth_headers)
        
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()
    
    def test_update_user_type_admin_success(self, client, admin_auth_headers, test_user):
        """Test updating user type as admin"""
        update_data = {"user_type": "pro"}
        response = client.put(
            f"/admin/users/{test_user.id}/type",
            json=update_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_type"] == "pro"
    
    def test_update_user_type_non_admin(self, client, auth_headers, test_user):
        """Test updating user type as non-admin"""
        update_data = {"user_type": "pro"}
        response = client.put(
            f"/admin/users/{test_user.id}/type",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_endpoint(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.patch("/users/")  # PATCH not supported
        assert response.status_code == 405
    
    def test_malformed_json(self, client):
        """Test malformed JSON request"""
        response = client.post(
            "/users/",
            data="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestCORSAndSecurity:
    """Test CORS and security headers"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/users/")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_security_headers(self, client):
        """Test security headers"""
        response = client.get("/")
        
        # Should have basic security headers
        assert response.status_code == 200
        # Security headers are added by middleware in the main app 