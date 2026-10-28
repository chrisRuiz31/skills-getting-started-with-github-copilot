import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 3,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(TEST_ACTIVITIES))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == TEST_ACTIVITIES


def test_signup_adds_participant(client):
    email = "newstudent@mergington.edu"

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_updates_activity_and_availability(client):
    email = "michael@mergington.edu"

    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {email} from Chess Club",
        "spots_left": 2,
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "daniel@mergington.edu"
    ]


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_rejects_unregistered_email(client):
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "unknown@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }