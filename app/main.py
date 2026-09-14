from fastapi import FastAPI, Depends
from app.auth import require_scope

app = FastAPI(title="CloudForge Ingest Studio")

@app.get("/ingest", dependencies=[Depends(require_scope("ingest:read"))])
def get_ingested_items():
    return {"message": "Success: Read ingested items and categories"}

@app.post("/ingest", dependencies=[Depends(require_scope("ingest:write"))])
def create_ingested_item(data: dict):
    return {"message": "Success: Data ingested and categorized"}
