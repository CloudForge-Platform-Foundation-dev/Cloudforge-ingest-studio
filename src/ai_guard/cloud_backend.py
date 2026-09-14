from __future__ import annotations

from typing import Any


class CloudAIBackend:
    """
    Backend หลัก — ตอน deploy จริงต้องผูก client จริงตรงนี้ (เช่น Anthropic
    SDK เรียก Claude ให้ช่วย classify asset_type จาก payload ที่กำกวม)

    TODO ก่อนใช้งาน production:
      1. ใส่ API client จริงใน __init__ (อ่าน key จาก env var ไม่ hardcode)
      2. เขียน prompt ที่ส่ง payload เข้าไปแล้วขอ asset_type กลับมาแบบ
         constrained (เช่น ให้ตอบ JSON ที่มีแค่ field เดียว)
      3. ตั้ง timeout สั้นๆ (2-3 วินาที) ที่ระดับ HTTP client — AIGuard เอง
         ไม่ได้ตั้ง timeout ให้ ต้องตั้งใน client ตรงนี้

    ตอนนี้เป็น stub ที่ raise NotImplementedError เสมอ โดยตั้งใจ เพื่อบังคับ
    ให้ AIGuard fallback ไป LocalRuleBackend จนกว่าจะเสียบ client จริง —
    กันไม่ให้ deploy ไปโดยเข้าใจผิดว่ามี cloud AI ทำงานอยู่ทั้งที่ยังไม่ได้ต่อ
    """

    def classify_asset_type(self, payload: dict[str, Any]) -> str:
        raise NotImplementedError(
            "CloudAIBackend ยังไม่ได้เชื่อม client จริง — ดู TODO ในไฟล์นี้ "
            "(src/ai_guard/cloud_backend.py)"
        )
