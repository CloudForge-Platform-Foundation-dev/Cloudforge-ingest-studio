from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Optional
# ???????????? get_current_user ??? src.auth.dependencies ??????????????????????????
try:
    from src.auth.dependencies import get_current_user
except ImportError:
    # Fallback ????????????? path ?? local test
    from app.auth import require_scope as get_current_user

app = FastAPI(title="CloudForge Ingest Studio - Production")

@app.get("/healthz", tags=["Probe"])
def healthz():
    """Public health check probe (No auth required)"""
    return {"status": "healthy"}

@app.post("/ingest", dependencies=[Depends(get_current_user)], tags=["Ingest"])
def ingest_batch(data: dict):
    """Ingest batch data (Requires Authentication)"""
    return {"message": "Batch ingested successfully"}

@app.post("/ingest/file", dependencies=[Depends(get_current_user)], tags=["Ingest"])
async def ingest_file(file_info: dict):
    """Ingest file (Requires Authentication)"""
    return {"message": "File ingested successfully"}

@app.get("/ingest/{ingest_id}", dependencies=[Depends(get_current_user)], tags=["Ingest"])
def get_ingest_item(ingest_id: str):
    """Get specific ingested item details (Requires Authentication)"""
    return {"ingest_id": ingest_id, "status": "processed"}

@app.get("/ingest", dependencies=[Depends(get_current_user)], tags=["Ingest"])
def list_ingested_items():
    """List all ingested items (Requires Authentication)"""
    return {"items": []}
