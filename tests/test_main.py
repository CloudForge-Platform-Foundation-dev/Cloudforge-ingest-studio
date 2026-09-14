"""
Integration tests ผ่าน FastAPI TestClient

ทดสอบ behavior จริงของ pipeline (parser -> mapping -> AI Guard -> storage)
ไม่ใช่แค่ status code ของ stub — override get_current_user ด้วย full-scope
user จำลอง เพื่อแยกการทดสอบ business logic ออกจากการทดสอบ auth (ซึ่งมี
tests/test_route_enforcement.py และ tests/test_auth*.py คุมอยู่แล้ว)

หมายเหตุ: ไฟล์นี้ต้องมี fastapi/httpx ติดตั้งถึงจะรันได้
(pip install -r requirements-dev.txt)
"""

import json

import pytest
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.main import app
from src.storage import store

FULL_ACCESS_USER = {"sub": "test-user", "scopes": ["ingest:read", "ingest:write"]}


@pytest.fixture(autouse=True)
def _auth_override_and_reset_store():
    """Override auth ให้ผ่านเสมอ (full scope) + เคลียร์ store ก่อนทุก test"""
    app.dependency_overrides[get_current_user] = lambda: FULL_ACCESS_USER
    store._records.clear()
    yield
    app.dependency_overrides.pop(get_current_user, None)
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
        # pydantic validation ที่ระดับ request body -> 422 ตั้งแต่ก่อนถึง handler
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
        """ไม่มีคอลัมน์ asset_type เลย -> ต้องผ่าน AI Guard และเนื่องจากยังไม่ได้
        เสียบ cloud client จริง (CloudAIBackend เป็น stub) จะได้ local_fallback เสมอ"""
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
        assert record["asset_type"] == "database"  # local backend เจอ keyword "mysql"

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
            files={"file": ("assets.csv", "asset_type\nvm\n", "text/csv")},  # ไม่มี source_system/external_id
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


class TestScopeEnforcement:
    """ยืนยันว่า scope ที่ไม่ถูกต้องโดน 403 แม้ authenticated แล้วก็ตาม
    (แยกจาก test_route_enforcement.py ที่คุมเคส unauthenticated -> 401)"""

    def test_write_scope_required_for_ingest(self, client):
        app.dependency_overrides[get_current_user] = lambda: {
            "sub": "read-only-user",
            "scopes": ["ingest:read"],  # ไม่มี ingest:write
        }
        resp = client.post(
            "/ingest",
            json={"records": [{"source_system": "aws", "asset_type": "vm", "external_id": "i-1"}]},
        )
        assert resp.status_code == 403

    def test_read_scope_required_for_list(self, client):
        app.dependency_overrides[get_current_user] = lambda: {
            "sub": "write-only-user",
            "scopes": ["ingest:write"],  # ไม่มี ingest:read
        }
        resp = client.get("/ingest")
        assert resp.status_code == 403
