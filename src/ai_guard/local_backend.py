from __future__ import annotations

from typing import Any

from src.enums import AssetType

_KEYWORD_RULES: dict[AssetType, tuple[str, ...]] = {
    AssetType.VM: ("vm", "instance", "ec2", "virtual machine", "compute"),
    AssetType.DATABASE: ("db", "database", "rds", "sql", "postgres", "mysql", "mongo"),
    AssetType.STORAGE_BUCKET: ("bucket", "s3", "blob", "storage"),
    AssetType.NETWORK_CONFIG: ("vpc", "subnet", "firewall", "network", "route"),
    AssetType.APPLICATION: ("app", "service", "application", "container", "pod"),
}

_DEFAULT = AssetType.APPLICATION


class LocalRuleBackend:
    """
    Fallback แบบ deterministic — ไม่ใช้ AI เลย ใช้ keyword matching ธรรมดา
    กับ field ที่มักบอกประเภท asset (name/type/description ใน payload)

    ตั้งใจให้ "โง่กว่า" cloud AI แต่ "พังไม่ได้": ไม่มี network call, ไม่มี
    timeout, ตอบได้เสมอทันที (default เป็น APPLICATION ถ้าไม่ match อะไรเลย)
    นี่คือหัวใจของ "AI Guard ทำงานต่อได้แม้ไฟดับ/เน็ตล่ม" — เพราะเมื่อถึง
    จุดนี้ระบบไม่ได้พึ่งอะไรนอกเครื่องอีกแล้วเลย

    หลักการเดียวกับ registry-as-deterministic-fallback ที่ foundation-
    validation ใช้เมื่อ AI/OPA ตัดสินใจไม่ได้
    """

    def classify_asset_type(self, payload: dict[str, Any]) -> str:
        haystack = " ".join(str(v) for v in payload.values() if v is not None).lower()
        for asset_type, keywords in _KEYWORD_RULES.items():
            if any(kw in haystack for kw in keywords):
                return asset_type.value
        return _DEFAULT.value
