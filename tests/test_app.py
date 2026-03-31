"""Tests for the FastAPI extracurricular activities application"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that activities list contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_activity_participants_is_list(self, client):
        """Test that participants is a list"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to activity"""
        email = "newstudent@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_duplicate_student_returns_400(self, client):
        """Test signup for same student twice returns 400"""
        email = "michael@mergington.edu"
        
        # Try to sign up with existing participant
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_multiple_students(self, client):
        """Test signing up multiple different students"""
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Tennis%20Club/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify both are in participants
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data["Tennis Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from activity"""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister removes participant from activity"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_non_participant_returns_400(self, client):
        """Test unregister non-participant returns 400"""
        email = "nonexistent@mergington.edu"
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_then_signup_again(self, client):
        """Test unregistering and signing up again"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Sign up again should succeed
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant is back
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]


class TestActivityParticipantLimits:
    """Tests for participant limits"""

    def test_activity_respects_max_participants(self, client):
        """Test that activity tracks max participants"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Tennis Club"]
        assert activity["max_participants"] >= len(activity["participants"])

    def test_signup_calculation_respects_limits(self, client):
        """Test max_participants field"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Programming Class"]
        # Just verify we can calculate available spots
        spots_available = activity["max_participants"] - len(activity["participants"])
        assert spots_available >= 0


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete signup and unregister workflow"""
        email = "testingtesting@mergington.edu"
        activity = "Debate Club"
        
        # Verify student not in activity initially
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify student in activity
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify student not in activity
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]

    def test_multiple_students_in_activity(self, client):
        """Test multiple students can be in same activity"""
        activity = "Art Club"
        emails = ["newstudent1@mergington.edu", "newstudent2@mergington.edu"]
        
        # Sign up both students
        for email in emails:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify both are in activity
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data[activity]["participants"]
        
        # Unregister one student
        client.delete(
            f"/activities/{activity.replace(' ', '%20')}/unregister?email={emails[0]}"
        )
        
        # Verify one remains
        response = client.get("/activities")
        data = response.json()
        assert emails[0] not in data[activity]["participants"]
        assert emails[1] in data[activity]["participants"]
