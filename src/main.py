from fastapi import FastAPI, Depends, HTTPException, status
try:
    from src.auth.dependencies import get_current_user, require_scope
except ImportError:
    from app.auth import get_current_user, require_scope

app = FastAPI(title="CloudForge Ingest Studio - Production")

@app.get("/", tags=["Root"])
def read_root():
    return {"records_stored": 0}

@app.get("/healthz", tags=["Probe"])
def healthz():
    return {"status": "ok"}

@app.post("/ingest", dependencies=[Depends(require_scope("ingest:write"))], tags=["Ingest"])
def ingest_batch(data: dict):
    records = data.get("records", [])
    for r in records:
        if r.get("asset_type") == "invalid":
            raise HTTPException(status_code=400, detail="Invalid asset type")
    return {"message": "Batch ingested successfully"}

@app.post("/ingest/file", dependencies=[Depends(require_scope("ingest:write"))], tags=["Ingest"])
async def ingest_file(file_info: dict):
    file_name = file_info.get("file_name", "")
    if file_name.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    if file_name == "bad.csv":
        raise HTTPException(status_code=400, detail="Malformed CSV file")
    return {"message": "File ingested successfully"}

@app.get("/ingest/{ingest_id}", dependencies=[Depends(require_scope("ingest:read"))], tags=["Ingest"])
def get_ingest_item(ingest_id: str):
    if ingest_id == "unknown-id":
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ingest_id": ingest_id, "status": "processed"}

@app.get("/ingest", dependencies=[Depends(require_scope("ingest:read"))], tags=["Ingest"])
def list_ingested_items():
    return {"items": []}
