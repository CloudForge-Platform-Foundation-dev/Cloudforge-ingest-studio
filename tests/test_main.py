from src.main import app
from src.auth.dependencies import get_current_user
import pytest

@pytest.fixture(autouse=True)
def override_auth_dependency():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user", "role": "admin"}
    yield
    app.dependency_overrides.clear()

"""
Integration tests à¸œà¹ˆà¸²à¸™ FastAPI TestClient

à¸«à¸¡à¸²à¸¢à¹€à¸«à¸•à¸¸: à¹„à¸Ÿà¸¥à¹Œà¸™à¸µà¹‰à¸•à¹‰à¸­à¸‡à¸¡à¸µ fastapi/httpx à¸•à¸´à¸”à¸•à¸±à¹‰à¸‡à¸–à¸¶à¸‡à¸ˆà¸°à¸£à¸±à¸™à¹„à¸”à¹‰
(pip install -r requirements-dev.txt) â€” à¹à¸¢à¸à¸ˆà¸²à¸ tests/test_parsers.py,
test_mapping.py, test_resilience.py, test_ai_guard.py à¸—à¸µà¹ˆà¸£à¸±à¸™à¹„à¸”à¹‰à¸”à¹‰à¸§à¸¢
stdlib unittest à¸¥à¹‰à¸§à¸™à¹† à¹‚à¸”à¸¢à¹„à¸¡à¹ˆà¸•à¹‰à¸­à¸‡à¸•à¸´à¸”à¸•à¸±à¹‰à¸‡à¸­à¸°à¹„à¸£à¹€à¸žà¸´à¹ˆà¸¡
"""

import json

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.storage import store


@pytest.fixture(autouse=True)
def _reset_store():
    """à¹€à¸„à¸¥à¸µà¸¢à¸£à¹Œ in-memory store à¸à¹ˆà¸­à¸™à¸—à¸¸à¸ test à¸à¸±à¸™à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰ test à¸à¹ˆà¸­à¸™à¸«à¸™à¹‰à¸²à¸à¸£à¸°à¸—à¸šà¸à¸±à¸™"""
    store._records.clear()
    yield
    store._records.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthAndRoot:
    def test_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_root_reports_record_count(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["records_stored"] == 0


class TestIngestJson:
    def test_ingest_batch_marks_declared_source(self, client):
        payload = {
            "records": [
                {
                    "source_system": "aws-prod",
                    "asset_type": "vm",
                    "external_id": "i-123",
                    "payload": {"region": "ap-southeast-1"},
                }
            ]
        }
        resp = client.post("/ingest", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["accepted"] == 1
        assert body["rejected"] == 0
        assert body["records"][0]["asset_type_source"] == "declared"

    def test_ingest_batch_rejects_invalid_asset_type(self, client):
        payload = {
            "records": [
                {"source_system": "aws", "asset_type": "not-a-real-type", "external_id": "1"}
            ]
        }
        resp = client.post("/ingest", json=payload)
        # pydantic validation à¸—à¸µà¹ˆà¸£à¸°à¸”à¸±à¸š request body -> 422 à¸•à¸±à¹‰à¸‡à¹à¸•à¹ˆà¸à¹ˆà¸­à¸™à¸–à¸¶à¸‡ handler
        assert resp.status_code == 422


class TestIngestFile:
    def test_ingest_csv_file_with_explicit_asset_type(self, client):
        csv_content = (
            "source_system,asset_type,external_id,region\n"
            "aws-prod,vm,i-1,ap-1\n"
            "aws-prod,database,db-1,ap-1\n"
        )
        resp = client.post(
            "/ingest/file",
            files={"file": ("assets.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["accepted"] == 2
        assert all(r["asset_type_source"] == "declared" for r in body["records"])

    def test_ingest_csv_without_asset_type_uses_ai_guard_fallback(self, client):
        """à¹„à¸¡à¹ˆà¸¡à¸µà¸„à¸­à¸¥à¸±à¸¡à¸™à¹Œ asset_type à¹€à¸¥à¸¢ -> à¸•à¹‰à¸­à¸‡à¸œà¹ˆà¸²à¸™ AI Guard à¹à¸¥à¸°à¹€à¸™à¸·à¹ˆà¸­à¸‡à¸ˆà¸²à¸à¸¢à¸±à¸‡à¹„à¸¡à¹ˆà¹„à¸”à¹‰
        à¹€à¸ªà¸µà¸¢à¸š cloud client à¸ˆà¸£à¸´à¸‡ (CloudAIBackend à¹€à¸›à¹‡à¸™ stub) à¸ˆà¸°à¹„à¸”à¹‰ local_fallback à¹€à¸ªà¸¡à¸­"""
        csv_content = "source_system,external_id,name\nlegacy-cmdb,CI-1,prod-mysql-primary\n"
        resp = client.post(
            "/ingest/file",
            files={"file": ("assets.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["accepted"] == 1
        record = body["records"][0]
        assert record["asset_type_source"] == "local_fallback"
        assert record["asset_type"] == "database"  # local backend à¹€à¸ˆà¸­ keyword "mysql"

    def test_ingest_json_file(self, client):
        payload = json.dumps(
            [{"source_system": "aws", "asset_type": "vm", "external_id": "i-9"}]
        )
        resp = client.post(
            "/ingest/file",
            files={"file": ("assets.json", payload, "application/json")},
        )
        assert resp.status_code == 201
        assert resp.json()["accepted"] == 1

    def test_unsupported_file_extension_returns_400(self, client):
        resp = client.post(
            "/ingest/file",
            files={"file": ("assets.pdf", b"whatever", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_malformed_csv_returns_400(self, client):
        resp = client.post(
            "/ingest/file",
            files={"file": ("assets.csv", "asset_type\nvm\n", "text/csv")},  # à¹„à¸¡à¹ˆà¸¡à¸µ source_system/external_id
        )
        assert resp.status_code == 400

    def test_custom_mapping_query_param(self, client):
        csv_content = "cmdb_source,ci_id,name\nlegacy-system,CI-42,web-app-frontend\n"
        resp = client.post(
            "/ingest/file?mapping=legacy-cmdb-export",
            files={"file": ("export.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["accepted"] == 1
        assert body["records"][0]["source_system"] == "legacy-system"


class TestGetIngestedRecords:
    def test_get_by_id_after_ingest(self, client):
        resp = client.post(
            "/ingest",
            json={"records": [{"source_system": "aws", "asset_type": "vm", "external_id": "i-1"}]},
        )
        ingest_id = resp.json()["records"][0]["ingest_id"]

        get_resp = client.get(f"/ingest/{ingest_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["external_id"] == "i-1"

    def test_get_unknown_id_returns_404(self, client):
        resp = client.get("/ingest/does-not-exist")
        assert resp.status_code == 404

    def test_list_all_records(self, client):
        client.post(
            "/ingest",
            json={"records": [{"source_system": "aws", "asset_type": "vm", "external_id": "i-1"}]},
        )
        resp = client.get("/ingest")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

