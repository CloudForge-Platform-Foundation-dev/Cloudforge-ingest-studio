import unittest

from src.parsers.mapping import MappingError, resolve_row

TEST_MAPPINGS = {
    "default": {
        "source_system": ["source_system", "source"],
        "asset_type": ["asset_type", "type"],
        "external_id": ["external_id", "id"],
    },
    "no-asset-type-column": {
        "source_system": ["src"],
        "external_id": ["ci_id"],
    },
}


class TestResolveRow(unittest.TestCase):
    def test_direct_column_names_resolve(self):
        row = {"source_system": "aws-prod", "asset_type": "vm", "external_id": "i-123", "extra": "x"}
        result = resolve_row(row, "default", TEST_MAPPINGS)
        self.assertEqual(result["source_system"], "aws-prod")
        self.assertEqual(result["asset_type"], "vm")
        self.assertEqual(result["external_id"], "i-123")
        self.assertEqual(result["payload"], {"extra": "x"})

    def test_alternate_column_names_resolve_case_insensitive(self):
        row = {"Source": "on-prem", "Type": "database", "ID": "db-1"}
        result = resolve_row(row, "default", TEST_MAPPINGS)
        self.assertEqual(result["source_system"], "on-prem")
        self.assertEqual(result["asset_type"], "database")
        self.assertEqual(result["external_id"], "db-1")

    def test_missing_required_field_raises(self):
        row = {"source_system": "aws-prod", "asset_type": "vm"}  # ไม่มี external_id
        with self.assertRaises(MappingError):
            resolve_row(row, "default", TEST_MAPPINGS)

    def test_missing_optional_asset_type_returns_none_not_error(self):
        row = {"src": "legacy-cmdb", "ci_id": "CI-9001", "name": "billing-service"}
        result = resolve_row(row, "no-asset-type-column", TEST_MAPPINGS)
        self.assertIsNone(result["asset_type"])
        self.assertEqual(result["payload"], {"name": "billing-service"})

    def test_unknown_mapping_name_raises(self):
        with self.assertRaises(MappingError):
            resolve_row({"a": "b"}, "does-not-exist", TEST_MAPPINGS)

    def test_extra_columns_collected_into_payload(self):
        row = {"source_system": "x", "asset_type": "vm", "external_id": "1", "region": "ap-southeast-1", "tags": "prod"}
        result = resolve_row(row, "default", TEST_MAPPINGS)
        self.assertEqual(result["payload"], {"region": "ap-southeast-1", "tags": "prod"})


if __name__ == "__main__":
    unittest.main()
