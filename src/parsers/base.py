"""
Interface กลางที่ parser ทุกตัว (CSV/JSON/Excel) ต้องเดินตาม

หลักการ: endpoint (main.py) ไม่ควรรู้เลยว่าไฟล์ที่รับมาเป็น format ไหน —
แค่ขอ parser จาก registry ตามนามสกุลไฟล์ แล้วเรียก .parse() เหมือนกันหมด
เพิ่ม format ใหม่ในอนาคต = เพิ่ม class ที่ implement RecordParser ตัวเดียว
ไม่ต้องแก้ endpoint เลย
"""

from typing import Any, Protocol


class ParseError(Exception):
    """ไฟล์ที่ส่งมา parse เป็น record ไม่ได้ (format ผิด/mapping หาไม่เจอ)"""


class RecordParser(Protocol):
    def parse(self, raw: bytes, mapping_name: str = "default") -> list[dict[str, Any]]:
        """
        แปลงไฟล์ดิบ (bytes) เป็น list ของ dict มาตรฐาน โดยแต่ละ dict มี key:
        source_system, external_id, payload เสมอ และ asset_type อาจเป็น
        None ได้ถ้า mapping ไม่ได้ระบุคอลัมน์นี้ไว้ (ให้ AI Guard classify ต่อ)

        ต้อง raise ParseError ถ้าข้อมูลผิดรูปแบบจนกู้คืนไม่ได้
        """
        ...
