from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.main.get_client")
def test_health(mock_get_client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "weaviate" in response.json()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_task_status_not_found():
    response = client.get("/task-status/nonexistent-task-id")
    assert response.status_code == 200
    assert response.json() == {"error": "Task not found"}


def test_get_users_tasks_empty():
    response = client.get("/users/tasks/fakeuser@example.com")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_document(monkeypatch):
    monkeypatch.setattr("app.main.development", True)
    monkeypatch.setattr(
        "app.main.process_document", lambda task_id, structured_json: None
    )

    response = client.post(
        "/upload-document",
        files={"file": ("test.txt", b"Test content")},
        data={"user_email": "test@example.com"},
    )
    assert response.status_code == 200
    assert "task_id" in response.json()
