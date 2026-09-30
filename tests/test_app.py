import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        name: activity["participants"].copy()
        for name, activity in activities.items()
    }
    yield
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_registers_new_participant():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Basketball Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Basketball Team"
    }
    assert email in activities["Basketball Team"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"
    original_count = activities["Chess Club"]["participants"].count(email)

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities["Chess Club"]["participants"].count(email) == original_count


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_unregisters_participant():
    email = "removable.student@mergington.edu"
    activities["Basketball Team"]["participants"].append(email)

    response = client.delete(
        "/activities/Basketball Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Basketball Team"
    }
    assert email not in activities["Basketball Team"]["participants"]


def test_delete_rejects_unknown_participant():
    response = client.delete(
        "/activities/Basketball Team/signup",
        params={"email": "missing.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_delete_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
