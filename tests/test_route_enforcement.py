from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_healthz_is_public():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_ingest_batch_requires_auth():
    response = client.post("/ingest", json={})
    assert response.status_code == 401

def test_ingest_file_requires_auth():
    response = client.post("/ingest/file", json={})
    assert response.status_code == 401

def test_ingest_item_detail_requires_auth():
    response = client.get("/ingest/123")
    assert response.status_code == 401

def test_ingest_list_requires_auth():
    response = client.get("/ingest")
    assert response.status_code == 401
