from __future__ import annotations

from typing import Any, Protocol


class GuardDecisionSource:
    """ค่าคงที่บอกที่มาของการตัดสินใจ ใช้บันทึกลง audit trail"""

    CLOUD = "cloud"
    LOCAL_FALLBACK = "local_fallback"


class AIBackend(Protocol):
    """
    Interface กลางที่ backend ทุกตัว (cloud/local) ต้อง implement เหมือนกัน
    เพื่อให้ AIGuard สลับไปมาระหว่าง backend ได้โดยไม่ต้องแก้ caller เลย
    """

    def classify_asset_type(self, payload: dict[str, Any]) -> str:
        """
        คืนค่า asset_type ที่ backend ตัดสินใจจาก payload ที่ mapping หา
        คอลัมน์ asset_type ไม่เจอ

        ต้อง raise Exception ถ้าตัดสินใจไม่ได้ (cloud ล่ม/timeout/ยังไม่ต่อ
        client) — AIGuard จะจับแล้ว fallback ไป backend ถัดไปให้เอง
        """
        ...
