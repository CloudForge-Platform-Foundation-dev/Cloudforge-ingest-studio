from __future__ import annotations

import csv
import io
from typing import Any

from src.parsers.base import ParseError
from src.parsers.mapping import resolve_row


class CsvParser:
    def parse(self, raw: bytes, mapping_name: str = "default") -> list[dict[str, Any]]:
        try:
            text = raw.decode("utf-8-sig")  # utf-8-sig กัน BOM จาก Excel export
        except UnicodeDecodeError as exc:
            raise ParseError(f"ไฟล์ CSV decode เป็น UTF-8 ไม่ได้: {exc}") from exc

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise ParseError("ไฟล์ CSV ไม่มี header row")

        results: list[dict[str, Any]] = []
        for i, row in enumerate(reader):
            try:
                results.append(resolve_row(row, mapping_name))
            except Exception as exc:
                raise ParseError(f"CSV row {i + 2}: {exc}") from exc  # +2 = header + 1-indexed
        return results
