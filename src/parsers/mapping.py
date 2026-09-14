"""
Metadata-driven field mapping

แนวคิดตรงจากโพสต์อ้างอิง (LinkedIn ingestion framework): "รับ source ที่
หน้าตาไม่เหมือนกัน แปลงทุก format ให้เป็น internal schema เดียว ด้วย mapping
แบบ metadata-driven ไม่ต้อง rewrite pipeline ทุกครั้งที่มี source ใหม่"

วิธีใช้: เพิ่ม source ใหม่ = เพิ่ม entry ใน mappings/default_mapping.yaml
ระบุว่าคอลัมน์ชื่ออะไรบ้าง (ในไฟล์ต้นทาง) map ไปเป็น field ไหนของเรา
ไม่ต้องแตะโค้ด parser เลยสักบรรทัด
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DEFAULT_MAPPING_PATH = Path(__file__).resolve().parents[2] / "mappings" / "default_mapping.yaml"

# field ที่ "ต้องหาให้เจอเสมอ" ผ่าน mapping ไม่งั้นถือว่า record นี้ใช้ไม่ได้
REQUIRED_FIELDS = ("source_system", "external_id")

# field ที่ "หาไม่เจอก็ได้" — ถ้า mapping ไม่ระบุหรือหาคอลัมน์ไม่เจอ จะปล่อยเป็น
# None แล้วให้ชั้นถัดไป (AI Guard) ตัดสินใจแทน แทนที่จะ reject record ทั้งแถว
OPTIONAL_INFERRABLE_FIELDS = ("asset_type",)


class MappingError(Exception):
    """ไม่พบ mapping ที่ระบุ หรือ mapping หา required field ไม่เจอในข้อมูลจริง"""


def load_mappings(path: Path | None = None) -> dict[str, dict[str, list[str]]]:
    p = path or _DEFAULT_MAPPING_PATH
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("mappings", {})


def resolve_row(
    row: dict[str, Any],
    mapping_name: str = "default",
    mappings: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, Any]:
    """
    แปลง row เดียว (column name แบบไหนก็ได้ตาม source จริง) ให้เป็น dict
    มาตรฐาน: source_system, asset_type (หรือ None), external_id, payload

    field ที่ไม่ได้ถูก map เข้า required/optional fields จะถูกเก็บรวมไว้ใน
    payload โดยอัตโนมัติ — ไม่มีข้อมูลหายไปแม้ mapping จะระบุแค่บาง field
    """
    all_mappings = mappings if mappings is not None else load_mappings()
    spec = all_mappings.get(mapping_name)
    if spec is None:
        raise MappingError(f"ไม่พบ mapping ชื่อ '{mapping_name}' ใน mappings config")

    # normalize key เป็น lowercase + strip เพื่อ match แบบไม่สนตัวพิมพ์/ช่องว่างหัวท้าย
    normalized = {str(k).strip().lower(): v for k, v in row.items()}

    resolved: dict[str, Any] = {}
    consumed_keys: set[str] = set()

    def find_value(field: str) -> tuple[Any, bool]:
        for candidate in spec.get(field, []):
            key = str(candidate).strip().lower()
            if key in normalized and normalized[key] not in (None, ""):
                consumed_keys.add(key)
                return normalized[key], True
        return None, False

    for field in REQUIRED_FIELDS:
        value, found = find_value(field)
        if not found:
            raise MappingError(
                f"หาค่าของ field บังคับ '{field}' ไม่เจอ (mapping='{mapping_name}', "
                f"ลองหา columns: {spec.get(field, [])})"
            )
        resolved[field] = value

    for field in OPTIONAL_INFERRABLE_FIELDS:
        value, _found = find_value(field)
        resolved[field] = value  # None ได้ ถ้าไม่เจอ — ให้ AI Guard จัดการต่อ

    resolved["payload"] = {k: v for k, v in normalized.items() if k not in consumed_keys}
    return resolved
