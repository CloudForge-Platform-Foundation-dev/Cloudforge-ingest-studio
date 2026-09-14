import io
import unittest

from openpyxl import Workbook

from src.parsers.base import ParseError
from src.parsers.csv_parser import CsvParser
from src.parsers.excel_parser import ExcelParser
from src.parsers.json_parser import JsonParser
from src.parsers.registry import get_parser


class TestCsvParser(unittest.TestCase):
    def setUp(self):
        self.parser = CsvParser()

    def test_parses_valid_csv(self):
        raw = b"source_system,asset_type,external_id,region\naws-prod,vm,i-1,ap-1\naws-prod,database,db-1,ap-1\n"
        rows = self.parser.parse(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["source_system"], "aws-prod")
        self.assertEqual(rows[0]["asset_type"], "vm")
        self.assertEqual(rows[0]["payload"], {"region": "ap-1"})

    def test_missing_header_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.parser.parse(b"")

    def test_bad_row_wraps_mapping_error_as_parse_error(self):
        raw = b"asset_type\nvm\n"  # ไม่มี source_system/external_id เลย
        with self.assertRaises(ParseError):
            self.parser.parse(raw)

    def test_utf8_bom_handled(self):
        raw = "source_system,asset_type,external_id\naws,vm,1\n".encode("utf-8-sig")
        rows = self.parser.parse(raw)
        self.assertEqual(len(rows), 1)


class TestJsonParser(unittest.TestCase):
    def setUp(self):
        self.parser = JsonParser()

    def test_direct_shape_list(self):
        raw = b'[{"source_system": "aws", "asset_type": "vm", "external_id": "1", "payload": {"a": 1}}]'
        rows = self.parser.parse(raw)
        self.assertEqual(rows[0]["source_system"], "aws")
        self.assertEqual(rows[0]["payload"], {"a": 1})

    def test_records_wrapper_shape(self):
        raw = b'{"records": [{"source_system": "aws", "asset_type": "vm", "external_id": "1"}]}'
        rows = self.parser.parse(raw)
        self.assertEqual(len(rows), 1)

    def test_invalid_json_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.parser.parse(b"{not valid json")

    def test_non_list_non_dict_raises(self):
        with self.assertRaises(ParseError):
            self.parser.parse(b'"just a string"')

    def test_missing_asset_type_stays_none_for_ai_guard(self):
        raw = b'[{"source_system": "aws", "external_id": "1"}]'
        rows = self.parser.parse(raw)
        self.assertIsNone(rows[0]["asset_type"])


class TestExcelParser(unittest.TestCase):
    def setUp(self):
        self.parser = ExcelParser()

    def _make_xlsx_bytes(self, header, rows):
        wb = Workbook()
        ws = wb.active
        ws.append(header)
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_parses_valid_excel(self):
        raw = self._make_xlsx_bytes(
            ["source_system", "asset_type", "external_id"],
            [["aws-prod", "vm", "i-1"], ["aws-prod", "database", "db-1"]],
        )
        rows = self.parser.parse(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["source_system"], "aws-prod")

    def test_skips_blank_rows(self):
        raw = self._make_xlsx_bytes(
            ["source_system", "asset_type", "external_id"],
            [["aws-prod", "vm", "i-1"], [None, None, None]],
        )
        rows = self.parser.parse(raw)
        self.assertEqual(len(rows), 1)

    def test_corrupt_file_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.parser.parse(b"not an excel file at all")


class TestRegistry(unittest.TestCase):
    def test_selects_csv_by_extension(self):
        parser = get_parser("assets.csv")
        self.assertIsInstance(parser, CsvParser)

    def test_selects_json_by_extension(self):
        parser = get_parser("assets.json")
        self.assertIsInstance(parser, JsonParser)

    def test_selects_excel_by_extension_case_insensitive(self):
        parser = get_parser("Assets.XLSX")
        self.assertIsInstance(parser, ExcelParser)

    def test_unsupported_extension_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_parser("assets.pdf")

    def test_no_extension_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_parser("assets")


if __name__ == "__main__":
    unittest.main()
