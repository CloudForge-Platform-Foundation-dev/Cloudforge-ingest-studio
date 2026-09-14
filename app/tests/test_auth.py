from fastapi.testclient import TestClient
from app.main import app
import jwt

client = TestClient(app)
SECRET_KEY = "super-secure-and-long-secret-key-exceeding-thirty-two-bytes-for-production"
ALGORITHM = "HS256"

def test_read_ingest_with_correct_scope():
    token = jwt.encode({"scopes": ["ingest:read"]}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.get("/ingest", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "Success: Read" in response.json()["message"]

def test_write_ingest_without_scope():
    token = jwt.encode({"scopes": ["ingest:read"]}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.post("/ingest", json={"test": "data"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Missing required scope: ingest:write" in response.json()["detail"]
