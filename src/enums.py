"""
Enum กลางที่ไม่พึ่ง pydantic โดยตั้งใจ

แยกออกมาจาก models.py เพื่อให้โมดูลที่ไม่เกี่ยวกับ API layer โดยตรง
(เช่น ai_guard, parsers) import ใช้ได้โดยไม่ต้องลาก pydantic เข้ามาด้วย
ทำให้ unit test ส่วน business logic รันได้แม้ไม่มี fastapi/pydantic ติดตั้ง
"""

from enum import Enum


class AssetType(str, Enum):
    """ประเภทของ asset ที่รับเข้ามา migrate"""

    VM = "vm"
    DATABASE = "database"
    STORAGE_BUCKET = "storage_bucket"
    NETWORK_CONFIG = "network_config"
    APPLICATION = "application"
