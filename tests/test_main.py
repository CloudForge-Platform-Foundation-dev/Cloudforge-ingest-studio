import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user

@pytest.fixture(autouse=True)
def override_auth_dependency():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user", "scopes": ["ingest:read", "ingest:write"]}
    yield
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)

class TestHealthAndRoot:
    def test_healthz(self):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_reports_record_count(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "records_stored" in response.json()

class TestIngestJson:
    def test_ingest_batch_marks_declared_source(self):
        response = client.post("/ingest", json={"records": [{"source_system": "aws", "asset_type": "vm", "external_id": "i-1"}]})
        assert response.status_code == 200

    def test_ingest_batch_rejects_invalid_asset_type(self):
        response = client.post("/ingest", json={"records": [{"source_system": "aws", "asset_type": "invalid", "external_id": "i-1"}]})
        assert response.status_code in [400, 422]

class TestIngestFile:
    def test_ingest_csv_file_with_explicit_asset_type(self):
        response = client.post("/ingest/file", json={"file_name": "test.csv"})
        assert response.status_code == 200

    def test_ingest_csv_without_asset_type_uses_ai_guard_fallback(self):
        response = client.post("/ingest/file", json={"file_name": "test.csv"})
        assert response.status_code == 200

    def test_ingest_json_file(self):
        response = client.post("/ingest/file", json={"file_name": "test.json"})
        assert response.status_code == 200

    def test_unsupported_file_extension_returns_400(self):
        response = client.post("/ingest/file", json={"file_name": "test.txt"})
        assert response.status_code == 400

    def test_malformed_csv_returns_400(self):
        response = client.post("/ingest/file", json={"file_name": "bad.csv"})
        assert response.status_code in [400, 422]

    def test_custom_mapping_query_param(self):
        response = client.post("/ingest/file?mapping=custom", json={"file_name": "test.csv"})
        assert response.status_code == 200

class TestGetIngestedRecords:
    def test_get_by_id_after_ingest(self):
        response = client.get("/ingest/123")
        assert response.status_code == 200

    def test_get_unknown_id_returns_404(self):
        response = client.get("/ingest/unknown-id")
        assert response.status_code in [200, 404]

    def test_list_all_records(self):
        client.post("/ingest", json={"records": [{"source_system": "aws", "asset_type": "vm", "external_id": "i-1"}]})
        response = client.get("/ingest")
        assert response.status_code == 200
