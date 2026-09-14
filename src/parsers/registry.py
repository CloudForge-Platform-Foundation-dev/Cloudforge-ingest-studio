from __future__ import annotations

from src.parsers.base import RecordParser
from src.parsers.csv_parser import CsvParser
from src.parsers.excel_parser import ExcelParser
from src.parsers.json_parser import JsonParser

_PARSERS: dict[str, RecordParser] = {
    "csv": CsvParser(),
    "json": JsonParser(),
    "xlsx": ExcelParser(),
    "xls": ExcelParser(),
}

SUPPORTED_EXTENSIONS: tuple[str, ...] = tuple(_PARSERS.keys())


def get_parser(filename: str) -> RecordParser:
    """
    เลือก parser จากนามสกุลไฟล์ — เพิ่ม format ใหม่ในอนาคตแค่เพิ่ม entry
    ใน _PARSERS ด้านบน ไม่ต้องแก้ endpoint ใน main.py เลย
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    parser = _PARSERS.get(ext)
    if parser is None:
        raise ValueError(
            f"ไม่รองรับไฟล์นามสกุล '.{ext}' — รองรับเฉพาะ: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return parser
