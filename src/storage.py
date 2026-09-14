"""
In-memory storage สำหรับ Ingest Studio

หมายเหตุ: นี่คือ placeholder ชั่วคราว ตามแผนที่วางไว้ (ขั้นตอน 4: เพิ่ม
redis/db ใน compose "ทีหลังถ้าจำเป็น") — ตอนนี้ยังไม่ต้องมี DB จริง
พอจะเปลี่ยนเป็น Postgres ทีหลัง แค่เปลี่ยน implementation ของคลาสนี้
โดยไม่ต้องแก้ routes ใน main.py
"""

import hashlib
import json
import uuid
from typing import Any

from src.models import AssetRecord, IngestedRecord


def compute_hash(payload: dict[str, Any]) -> str:
    """
    คำนวณ SHA-256 hash ของ payload แบบ deterministic
    (sort keys ก่อน serialize เพื่อให้ hash เดิมทุกครั้งถ้าข้อมูลเหมือนกัน)

    ใช้แนวคิดเดียวกับ EvidenceCollector.compute_hash() ใน
    foundation-validation เพื่อให้ hash ที่สร้างจากทั้งสองฝั่ง compare กันได้
    """
    serialized = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


class IngestStore:
    """เก็บ record ที่ ingest แล้วไว้ใน memory (dev/test only)"""

    def __init__(self) -> None:
        self._records: dict[str, IngestedRecord] = {}

    def save(self, record: AssetRecord, asset_type_source: str | None = None) -> IngestedRecord:
        ingest_id = str(uuid.uuid4())
        ingested = IngestedRecord(
            ingest_id=ingest_id,
            source_system=record.source_system,
            asset_type=record.asset_type,
            external_id=record.external_id,
            content_hash=compute_hash(record.payload),
            asset_type_source=asset_type_source,
        )
        self._records[ingest_id] = ingested
        return ingested

    def get(self, ingest_id: str) -> IngestedRecord | None:
        return self._records.get(ingest_id)

    def list_all(self) -> list[IngestedRecord]:
        return list(self._records.values())

    def count(self) -> int:
        return len(self._records)


# instance เดียวใช้ร่วมกันทั้ง app (dev only — จะเปลี่ยนเป็น dependency
# injection ตอนต่อ DB จริง)
store = IngestStore()
