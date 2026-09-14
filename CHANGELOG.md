# Changelog

## v0.3.0 - 2026-09-14

### Added
- `POST /ingest/file` — รับไฟล์ CSV/JSON/Excel เข้าสู่ pipeline เดียวกับ `POST /ingest`
- Parser registry (`src/parsers/`) เลือก parser ตามนามสกุลไฟล์ เพิ่ม format ใหม่ได้โดยไม่แก้ endpoint
- Metadata-driven field mapping (`mappings/default_mapping.yaml`) — เพิ่ม source ใหม่ที่ column ไม่ตรงกันได้โดยไม่แก้โค้ด
- AI Guard (`src/ai_guard/`) — failover ระหว่าง cloud backend กับ local rule-based backend สำหรับ classify `asset_type` เมื่อไฟล์ไม่มีคอลัมน์นี้
- Resilience layer (`src/resilience/`) — backpressure guard (fail-fast) และ retry decorator (exponential backoff)
- Field ใหม่ `asset_type_source` ใน `IngestedRecord` สำหรับ audit trail ว่า asset_type มาจาก `declared` / `cloud` / `local_fallback`
- อัปเดต `openapi.yaml` ให้ครอบคลุมทุก endpoint จริง (`/ingest`, `/ingest/file`, `/ingest/{ingest_id}`) พร้อม description/tags ครบตาม governance policy

### Changed
- `AssetType` enum ย้ายไป `src/enums.py` (ไม่พึ่ง pydantic) เพื่อให้ business logic module อื่น import ใช้ได้โดยไม่ลาก pydantic เข้ามา
- `IngestStore.save()` รับ `asset_type_source` เพิ่มเติม
- `requirements.txt` เพิ่ม `python-multipart`, `PyYAML`, `openpyxl`

## v0.2 - 2026-09-04
Test commit
