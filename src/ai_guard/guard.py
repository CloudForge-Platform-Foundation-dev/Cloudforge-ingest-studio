from __future__ import annotations

import logging
from typing import Any

from src.ai_guard.base import AIBackend, GuardDecisionSource
from src.ai_guard.cloud_backend import CloudAIBackend
from src.ai_guard.local_backend import LocalRuleBackend

logger = logging.getLogger("ai_guard")


class AIGuardResult:
    __slots__ = ("asset_type", "source")

    def __init__(self, asset_type: str, source: str) -> None:
        self.asset_type = asset_type
        self.source = source  # "cloud" | "local_fallback"

    def __repr__(self) -> str:  # pragma: no cover - เพื่อ debug เท่านั้น
        return f"AIGuardResult(asset_type={self.asset_type!r}, source={self.source!r})"


class AIGuard:
    """
    Failover layer หลักของ "AI เป็นการ์ด": ลอง cloud backend ก่อนเสมอ
    ถ้า fail ด้วยเหตุผลอะไรก็ตาม (network ล่ม, ไฟดับที่ dependency ฝั่ง
    cloud, ยังไม่ต่อ client, timeout) จะ fallback ไป local rule-based
    backend ทันที โดยไม่โยน exception ออกไปให้ caller

    หลักการ: pipeline การ ingest ข้อมูลต้องไม่หยุดเพราะ AI ล่ม — อย่างมาก
    ที่สุดคือได้คำตอบที่ "ฉลาดน้อยกว่า" (จาก local) ไม่ใช่ "ไม่ได้คำตอบเลย"

    ทุกครั้งที่ตัดสินใจ จะบันทึกไว้ว่ามาจาก backend ไหน (source) เพื่อให้
    audit trail ย้อนดูได้ว่า record ไหนถูก classify ด้วย cloud AI จริง
    กับ record ไหนใช้ fallback (ดู IngestedRecord.asset_type_source)
    """

    def __init__(
        self,
        cloud_backend: AIBackend | None = None,
        local_backend: AIBackend | None = None,
    ) -> None:
        self._cloud: AIBackend = cloud_backend or CloudAIBackend()
        self._local: AIBackend = local_backend or LocalRuleBackend()

    def classify_asset_type(self, payload: dict[str, Any]) -> AIGuardResult:
        try:
            asset_type = self._cloud.classify_asset_type(payload)
            return AIGuardResult(asset_type, GuardDecisionSource.CLOUD)
        except Exception as exc:
            logger.warning(
                "AIGuard: cloud backend ล้มเหลว (%s: %s) — fallback ไป local rule-based",
                type(exc).__name__,
                exc,
            )
            asset_type = self._local.classify_asset_type(payload)
            return AIGuardResult(asset_type, GuardDecisionSource.LOCAL_FALLBACK)


# instance เดียวใช้ร่วมกันทั้ง app (เหมือน pattern ของ store ใน storage.py)
guard = AIGuard()
