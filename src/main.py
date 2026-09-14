from fastapi import Depends
from src.auth.dependencies import get_current_user
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
    description="Ingest Studio API - à¸£à¸±à¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥ asset à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆ CloudForge Platform",
)

# à¸ˆà¸³à¸à¸±à¸” concurrent request à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰ traffic à¸žà¸¸à¹ˆà¸‡à¸ˆà¸™à¸£à¸°à¸šà¸šà¸¥à¹ˆà¸¡ (fail-fast à¹à¸—à¸™à¸•à¹ˆà¸­à¸„à¸´à¸§à¹„à¸¡à¹ˆà¸ˆà¸³à¸à¸±à¸”)
backpressure_guard = BackpressureGuard(max_concurrent=100)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "ingest.ai", "status": "running", "records_stored": store.count()}


def _save_batch(records_with_source: list[tuple[AssetRecord, str | None]]) -> IngestBatchResponse:
    """à¹ƒà¸Šà¹‰à¸£à¹ˆà¸§à¸¡à¸à¸±à¸™à¸—à¸±à¹‰à¸‡ /ingest (JSON) à¹à¸¥à¸° /ingest/file à¹€à¸žà¸·à¹ˆà¸­à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰ logic à¸à¸²à¸£à¹€à¸‹à¸Ÿà¸‹à¹‰à¸³à¸à¸±à¸™à¸ªà¸­à¸‡à¸—à¸µà¹ˆ"""
    ingested: list[IngestedRecord] = []
    errors: list[str] = []
    for i, (record, source) in enumerate(records_with_source):
        try:
            ingested.append(store.save(record, asset_type_source=source))
        except Exception as exc:  # à¸à¸±à¸™à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰ record à¹€à¸”à¸µà¸¢à¸§à¸žà¸±à¸‡à¸—à¸±à¹‰à¸‡ batch
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
    à¸£à¸±à¸š asset records à¹€à¸‚à¹‰à¸²à¸¡à¸²à¹€à¸›à¹‡à¸™ batch à¸œà¹ˆà¸²à¸™ JSON à¹‚à¸”à¸¢à¸•à¸£à¸‡ (asset_type à¸•à¹‰à¸­à¸‡
    à¸£à¸°à¸šà¸¸à¸¡à¸²à¸Šà¸±à¸”à¹€à¸ˆà¸™à¹€à¸ªà¸¡à¸­à¹ƒà¸™à¸—à¸²à¸‡à¸™à¸µà¹‰ â€” à¸šà¸±à¸™à¸—à¸¶à¸à¹„à¸§à¹‰à¹€à¸›à¹‡à¸™ asset_type_source='declared')
    à¸šà¸±à¸™à¸—à¸¶à¸à¸žà¸£à¹‰à¸­à¸¡ hash à¸ªà¸³à¸«à¸£à¸±à¸š traceability à¹à¸¥à¹‰à¸§à¸„à¸·à¸™à¸œà¸¥à¸¥à¸±à¸žà¸˜à¹Œà¸§à¹ˆà¸² record à¹„à¸«à¸™à¸ªà¸³à¹€à¸£à¹‡à¸ˆ/
    à¹„à¸¡à¹ˆà¸ªà¸³à¹€à¸£à¹‡à¸ˆ
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
async def ingest_file(user: dict = Depends(get_current_user),
    file: UploadFile = File(..., description="à¹„à¸Ÿà¸¥à¹Œ CSV, JSON à¸«à¸£à¸·à¸­ Excel (.xlsx/.xls)"),
    mapping: str = Query(
        "default",
        description="à¸Šà¸·à¹ˆà¸­ mapping config (à¸”à¸¹ mappings/default_mapping.yaml) à¸—à¸µà¹ˆà¸ˆà¸°à¹ƒà¸Šà¹‰à¹à¸›à¸¥à¸‡ column à¸‚à¸­à¸‡à¹„à¸Ÿà¸¥à¹Œà¸™à¸µà¹‰",
    ),
) -> IngestBatchResponse:
    """
    à¸£à¸±à¸šà¹„à¸Ÿà¸¥à¹Œ CSV/JSON/Excel à¹€à¸‚à¹‰à¸²à¸¡à¸² parse à¸œà¹ˆà¸²à¸™ parser registry + metadata-driven
    mapping (à¹€à¸žà¸´à¹ˆà¸¡ source à¹ƒà¸«à¸¡à¹ˆ = à¹€à¸žà¸´à¹ˆà¸¡ mapping à¹ƒà¸™ YAML à¹„à¸¡à¹ˆà¸•à¹‰à¸­à¸‡à¹à¸à¹‰à¹‚à¸„à¹‰à¸”)

    à¸–à¹‰à¸² mapping à¸«à¸²à¸„à¸­à¸¥à¸±à¸¡à¸™à¹Œ asset_type à¹„à¸¡à¹ˆà¹€à¸ˆà¸­ à¸ˆà¸°à¹ƒà¸«à¹‰ AI Guard (cloud â†’ local
    fallback à¸­à¸±à¸•à¹‚à¸™à¸¡à¸±à¸•à¸´à¸–à¹‰à¸² cloud à¹ƒà¸Šà¹‰à¹„à¸¡à¹ˆà¹„à¸”à¹‰) à¸Šà¹ˆà¸§à¸¢ classify à¹ƒà¸«à¹‰ à¸žà¸£à¹‰à¸­à¸¡à¸šà¸±à¸™à¸—à¸¶à¸
    à¸—à¸µà¹ˆà¸¡à¸²à¹„à¸§à¹‰à¹ƒà¸™ asset_type_source à¸‚à¸­à¸‡à¹à¸•à¹ˆà¸¥à¸° record à¹€à¸žà¸·à¹ˆà¸­à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸¢à¹‰à¸­à¸™à¸«à¸¥à¸±à¸‡à¹„à¸”à¹‰
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
        raise HTTPException(status_code=404, detail=f"à¹„à¸¡à¹ˆà¸žà¸š ingest_id: {ingest_id}")
    return record


@app.get("/ingest", response_model=list[IngestedRecord], tags=["Ingest"])
def list_ingested_records(user: dict = Depends(get_current_user)) -> list[IngestedRecord]:
    return store.list_all()




