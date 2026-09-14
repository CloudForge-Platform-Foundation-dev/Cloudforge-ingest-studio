from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from src.ai_guard.guard import guard as ai_guard
from src.models import AssetRecord, IngestBatchRequest, IngestBatchResponse, IngestedRecord
from src.parsers.base import ParseError
from src.parsers.registry import get_parser
from src.resilience.backpressure import BackpressureError, BackpressureGuard
from src.storage import store

app = FastAPI(
    title="CloudForge Ingest API",
    version="0.3.0",
    description="Ingest Studio API - รับข้อมูล asset เข้าสู่ CloudForge Platform",
)

# จำกัด concurrent request ไม่ให้ traffic พุ่งจนระบบล่ม (fail-fast แทนต่อคิวไม่จำกัด)
backpressure_guard = BackpressureGuard(max_concurrent=100)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "ingest.ai", "status": "running", "records_stored": store.count()}


def _save_batch(records_with_source: list[tuple[AssetRecord, str | None]]) -> IngestBatchResponse:
    """ใช้ร่วมกันทั้ง /ingest (JSON) และ /ingest/file เพื่อไม่ให้ logic การเซฟซ้ำกันสองที่"""
    ingested: list[IngestedRecord] = []
    errors: list[str] = []
    for i, (record, source) in enumerate(records_with_source):
        try:
            ingested.append(store.save(record, asset_type_source=source))
        except Exception as exc:  # กันไม่ให้ record เดียวพังทั้ง batch
            errors.append(f"record[{i}] ({record.external_id}): {exc}")
    return IngestBatchResponse(
        accepted=len(ingested),
        rejected=len(errors),
        records=ingested,
        errors=errors,
    )


@app.post("/ingest", response_model=IngestBatchResponse, status_code=201, tags=["Ingest"])
def ingest_batch(request: IngestBatchRequest) -> IngestBatchResponse:
    """
    รับ asset records เข้ามาเป็น batch ผ่าน JSON โดยตรง (asset_type ต้อง
    ระบุมาชัดเจนเสมอในทางนี้ — บันทึกไว้เป็น asset_type_source='declared')
    บันทึกพร้อม hash สำหรับ traceability แล้วคืนผลลัพธ์ว่า record ไหนสำเร็จ/
    ไม่สำเร็จ
    """
    try:
        with backpressure_guard:
            pairs: list[tuple[AssetRecord, str | None]] = [
                (record, "declared") for record in request.records
            ]
            return _save_batch(pairs)
    except BackpressureError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/ingest/file", response_model=IngestBatchResponse, status_code=201, tags=["Ingest"])
async def ingest_file(
    file: UploadFile = File(..., description="ไฟล์ CSV, JSON หรือ Excel (.xlsx/.xls)"),
    mapping: str = Query(
        "default",
        description="ชื่อ mapping config (ดู mappings/default_mapping.yaml) ที่จะใช้แปลง column ของไฟล์นี้",
    ),
) -> IngestBatchResponse:
    """
    รับไฟล์ CSV/JSON/Excel เข้ามา parse ผ่าน parser registry + metadata-driven
    mapping (เพิ่ม source ใหม่ = เพิ่ม mapping ใน YAML ไม่ต้องแก้โค้ด)

    ถ้า mapping หาคอลัมน์ asset_type ไม่เจอ จะให้ AI Guard (cloud → local
    fallback อัตโนมัติถ้า cloud ใช้ไม่ได้) ช่วย classify ให้ พร้อมบันทึก
    ที่มาไว้ใน asset_type_source ของแต่ละ record เพื่อตรวจสอบย้อนหลังได้
    """
    try:
        parser = get_parser(file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw = await file.read()

    try:
        with backpressure_guard:
            rows = parser.parse(raw, mapping_name=mapping)
    except BackpressureError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pairs: list[tuple[AssetRecord, str | None]] = []
    row_errors: list[str] = []
    for i, row in enumerate(rows):
        asset_type = row.get("asset_type")
        source: str | None = "declared"
        if not asset_type:
            result = ai_guard.classify_asset_type(row.get("payload", {}))
            asset_type = result.asset_type
            source = result.source
        try:
            record = AssetRecord(
                source_system=row["source_system"],
                asset_type=asset_type,
                external_id=row["external_id"],
                payload=row.get("payload", {}),
            )
            pairs.append((record, source))
        except Exception as exc:
            row_errors.append(f"row[{i}]: {exc}")

    response = _save_batch(pairs)
    response.errors = row_errors + response.errors
    response.rejected += len(row_errors)
    return response


@app.get("/ingest/{ingest_id}", response_model=IngestedRecord, tags=["Ingest"])
def get_ingested_record(ingest_id: str) -> IngestedRecord:
    record = store.get(ingest_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"ไม่พบ ingest_id: {ingest_id}")
    return record


@app.get("/ingest", response_model=list[IngestedRecord], tags=["Ingest"])
def list_ingested_records() -> list[IngestedRecord]:
    return store.list_all()
