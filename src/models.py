from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from src.enums import AssetType

__all__ = [
    "AssetType",
    "AssetRecord",
    "IngestBatchRequest",
    "IngestedRecord",
    "IngestBatchResponse",
]


class AssetRecord(BaseModel):
    """หนึ่งรายการ asset ที่ต้องการ ingest เข้าระบบ"""

    source_system: str = Field(..., min_length=1, description="ระบบต้นทาง เช่น 'aws-prod', 'on-prem-vsphere'")
    asset_type: AssetType
    external_id: str = Field(..., min_length=1, description="ID ของ asset ในระบบต้นทาง")
    payload: dict[str, Any] = Field(default_factory=dict, description="ข้อมูลดิบของ asset")


class IngestBatchRequest(BaseModel):
    """คำขอ ingest ทีเดียวหลาย record"""

    records: list[AssetRecord] = Field(..., min_length=1, max_length=1000)


class IngestedRecord(BaseModel):
    """record ที่ถูกบันทึกแล้ว พร้อม metadata สำหรับ traceability"""

    ingest_id: str
    source_system: str
    asset_type: AssetType
    external_id: str
    content_hash: str
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    asset_type_source: str | None = Field(
        default=None,
        description=(
            "ที่มาของ asset_type สำหรับ audit trail: "
            "'declared' (ผู้ส่งระบุเองผ่าน /ingest), "
            "'cloud' (AI Guard ใช้ cloud backend classify ให้), "
            "'local_fallback' (cloud ใช้ไม่ได้ ใช้ deterministic rule-based แทน)"
        ),
    )


class IngestBatchResponse(BaseModel):
    """ผลลัพธ์หลัง ingest batch เสร็จ"""

    accepted: int
    rejected: int
    records: list[IngestedRecord]
    errors: list[str] = Field(default_factory=list)
