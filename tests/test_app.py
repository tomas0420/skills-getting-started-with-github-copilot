"""
Integration tests for the Mergington High School Activities API.

Uses the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up the test state and preconditions
- Act: Execute the action being tested
- Assert: Verify the results and side effects
"""

import copy
from fastapi.testclient import TestClient
from src.app import app, activities


# Create a test client
client = TestClient(app)


def reset_activities():
    """Reset activities to a clean state for each test."""
    activities.clear()
    activities.update(copy.deepcopy({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }))


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities():
    """
    Test GET /activities endpoint.
    
    AAA Pattern:
    - Arrange: Reset activities to known state
    - Act: Fetch all activities
    - Assert: Verify response includes all activities with correct structure
    """
    # Arrange
    reset_activities()
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    
    # Verify structure of activity object
    chess = data["Chess Club"]
    assert chess["description"] == "Learn strategies and compete in chess tournaments"
    assert chess["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert chess["max_participants"] == 12
    assert len(chess["participants"]) == 2
    assert "michael@mergington.edu" in chess["participants"]


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

def test_signup_success():
    """
    Test successful signup to an activity.
    
    AAA Pattern:
    - Arrange: Reset activities, prepare new email
    - Act: POST signup request for a new participant
    - Assert: Verify response success and participant added to activity
    """
    # Arrange
    reset_activities()
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"Signed up {new_email} for {activity_name}"
    
    # Verify participant was actually added
    activities_data = client.get("/activities").json()
    assert new_email in activities_data[activity_name]["participants"]


def test_signup_duplicate_prevention():
    """
    Test that duplicate signups are prevented.
    
    AAA Pattern:
    - Arrange: Reset activities with existing participant
    - Act: Attempt to signup with already-registered email
    - Assert: Verify 400 error and participant list unchanged
    """
    # Arrange
    reset_activities()
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"  # Already signed up
    original_count = len(activities["Chess Club"]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email}
    )
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student already signed up"
    
    # Verify participant count unchanged
    assert len(activities[activity_name]["participants"]) == original_count


def test_signup_nonexistent_activity():
    """
    Test signup to a non-existent activity.
    
    AAA Pattern:
    - Arrange: Reset activities, prepare invalid activity name
    - Act: POST signup request for non-existent activity
    - Assert: Verify 404 error response
    """
    # Arrange
    reset_activities()
    activity_name = "Fake Activity"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


# ============================================================================
# DELETE /activities/{activity_name}/unregister Tests
# ============================================================================

def test_unregister_success():
    """
    Test successful unregistration from an activity.
    
    AAA Pattern:
    - Arrange: Reset activities with existing participant
    - Act: DELETE request to unregister a participant
    - Assert: Verify response success and participant removed from activity
    """
    # Arrange
    reset_activities()
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    original_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify participant was actually removed
    assert len(activities[activity_name]["participants"]) == original_count - 1
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_found():
    """
    Test unregistration of a participant not in the activity.
    
    AAA Pattern:
    - Arrange: Reset activities, prepare email not in activity
    - Act: DELETE request to unregister non-participant
    - Assert: Verify 404 error response
    """
    # Arrange
    reset_activities()
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"  # Not signed up
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Student not found in activity"


def test_unregister_nonexistent_activity():
    """
    Test unregistration from a non-existent activity.
    
    AAA Pattern:
    - Arrange: Reset activities, prepare invalid activity name
    - Act: DELETE request for non-existent activity
    - Assert: Verify 404 error response
    """
    # Arrange
    reset_activities()
    activity_name = "Fake Activity"
    email = "student@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


# ============================================================================
# Integration Tests: Multiple Actions
# ============================================================================

def test_signup_then_unregister_workflow():
    """
    Test a complete workflow: signup then unregister.
    
    AAA Pattern:
    - Arrange: Reset activities
    - Act: Sign up new participant, then unregister them
    - Assert: Verify final participant list is correct
    """
    # Arrange
    reset_activities()
    activity_name = "Programming Class"
    new_email = "workflow@mergington.edu"
    original_count = len(activities[activity_name]["participants"])
    
    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )
    
    # Assert signup success
    assert signup_response.status_code == 200
    assert new_email in activities[activity_name]["participants"]
    
    # Act: Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": new_email}
    )
    
    # Assert unregister success and back to original count
    assert unregister_response.status_code == 200
    assert len(activities[activity_name]["participants"]) == original_count
    assert new_email not in activities[activity_name]["participants"]
