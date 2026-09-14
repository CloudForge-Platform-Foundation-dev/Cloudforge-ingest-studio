from __future__ import annotations

import json
from typing import Any

from src.parsers.base import ParseError
from src.parsers.mapping import resolve_row

_DIRECT_FIELDS = {"source_system", "external_id"}


class JsonParser:
    """
    รองรับสอง shape:
    1. record ที่มี field ตรงกับ internal schema อยู่แล้ว (source_system,
       external_id, ...) — ใช้ตรงๆ ไม่ต้องผ่าน mapping
    2. record แบบ raw ที่ column ชื่ออื่น — fallback ไปใช้ mapping config
       เหมือน CSV/Excel

    ตรวจ shape 1 ก่อนเสมอ (เร็วกว่า และเป็น fast-path สำหรับ producer ที่
    ส่งข้อมูลตรง schema เราอยู่แล้ว)
    """

    def parse(self, raw: bytes, mapping_name: str = "default") -> list[dict[str, Any]]:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ParseError(f"ไฟล์ JSON parse ไม่ได้: {exc}") from exc

        if isinstance(data, dict):
            data = data.get("records", [data])
        if not isinstance(data, list):
            raise ParseError('โครงสร้าง JSON ต้องเป็น list ของ record หรือ {"records": [...]}')

        results: list[dict[str, Any]] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ParseError(f"JSON record[{i}] ต้องเป็น object")
            if _DIRECT_FIELDS.issubset(item.keys()):
                results.append(
                    {
                        "source_system": item["source_system"],
                        "asset_type": item.get("asset_type"),
                        "external_id": item["external_id"],
                        "payload": item.get("payload", {}),
                    }
                )
            else:
                try:
                    results.append(resolve_row(item, mapping_name))
                except Exception as exc:
                    raise ParseError(f"JSON record[{i}]: {exc}") from exc
        return results
