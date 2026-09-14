# CloudForge Ingest Studio

Studio ตัวแรกของ CloudForge Platform — พิสูจน์ pipeline end-to-end ก่อนไล่สร้าง
Knowledge → Nova → Security → Compliance

## Capabilities

- **รับข้อมูลได้สองทาง**: JSON API (`POST /ingest`) และไฟล์อัปโหลด
  (`POST /ingest/file` — รองรับ CSV / JSON / Excel)
- **Metadata-driven mapping**: เพิ่ม source ใหม่ที่ column ชื่อไม่เหมือนกัน
  ทำได้แค่เพิ่ม entry ใน `mappings/default_mapping.yaml` ไม่ต้องแก้โค้ด
  parser เลย (ดูตัวอย่าง `aws-migration-hub`, `legacy-cmdb-export`)
- **AI Guard (failover)**: ถ้าไฟล์ไม่มีคอลัมน์บอก `asset_type` ระบบจะให้
  cloud AI backend ช่วย classify ก่อนเสมอ ถ้าใช้ไม่ได้ (เน็ตล่ม/ไฟดับ/ยัง
  ไม่ได้เสียบ client) จะ fallback ไป local rule-based backend ทันทีแบบ
  deterministic — pipeline ไม่มีวันหยุดเพราะ AI ล่ม ดู
  `src/ai_guard/guard.py`
- **Audit trail**: ทุก record มี `content_hash` (SHA-256 ของ payload) และ
  `asset_type_source` (`declared` / `cloud` / `local_fallback`) บันทึกไว้
  ตรวจสอบย้อนหลังได้เสมอว่าข้อมูลมาจากไหน asset_type ตัดสินใจโดยใคร
- **Resilience**: backpressure guard จำกัด concurrent request แบบ fail-fast
  (`src/resilience/backpressure.py`) และ retry decorator แบบ exponential
  backoff พร้อมใช้สำหรับ call ที่อาจ fail ชั่วคราว (`src/resilience/retry.py`)

## Local Dev

```bash
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/healthz
- OpenAPI docs: http://localhost:8000/docs

### รัน tests

```bash
# ส่วนที่ไม่พึ่ง fastapi/pydantic (parsers, mapping, resilience, ai_guard)
python -m unittest discover tests -p "test_mapping.py" -p "test_parsers.py" \
  -p "test_resilience.py" -p "test_ai_guard.py"

# integration tests ผ่าน FastAPI TestClient (ต้อง pip install -r requirements-dev.txt ก่อน)
pip install -r requirements-dev.txt
pytest tests/test_main.py -v
```

### ตัวอย่างการอัปโหลดไฟล์

```bash
curl -X POST "http://localhost:8000/ingest/file" \
  -F "file=@assets.csv"

# ระบุ mapping config เอง (ตอน source ต้นทาง column ไม่ตรงกับ default)
curl -X POST "http://localhost:8000/ingest/file?mapping=aws-migration-hub" \
  -F "file=@aws_export.csv"
```

## Governance / Foundation Validation

Workflow `.github/workflows/validate-against-foundation.yml` เรียกผ่าน
`niphan1000-cyber1000/foundation-validation/.github/workflows/reusable-gate.yml@v1`

**ต้องตั้งก่อนใช้งานจริง:**
1. เพิ่ม repo secret `FOUNDATION_PAT` (PAT ที่มีสิทธิ์อ่าน
   `CloudForge-Platform-Foundation` และ `foundation-validation`)
2. ยืนยันว่า `openapi.yaml` มี `x-owner` ตามกฎ Foundation `.spectral.yaml`

> ⚠️ Workflow นี้ syntax valid และผ่านการตรวจแล้ว แต่ **ยังไม่เคยรันจริงกับ
> Studio repo จริงมาก่อน** — นี่คือ Studio ตัวแรกที่ใช้ทดสอบ end-to-end
> ถ้ามี error ให้เช็ค:
> - secret `FOUNDATION_PAT` ตั้งถูกไหม
> - `spec_path` output จาก `detect-openapi-spec` ตรงกับ path จริงไหม
> - engine version (`v1`) ยัง compatible กับ policy ฝั่ง Foundation ไหม

## Local Validation (ไม่ต้องรอ CI) — ทำทีหลัง (ขั้นตอน 3 ตามแผน)

จะเพิ่ม image `foundation-validation` ให้รันตรวจ local ได้ ตอนนี้ยังไม่ทำ
ตามลำดับที่วางไว้ (เริ่มแค่ API ใน Docker + validation ผ่าน reusable workflow ก่อน)

## Roadmap ของโปรเจกต์ (ลำดับ Studio)

1. **Ingest** ← ตอนนี้ (พิสูจน์ pipeline + ส่งข้อมูลเข้า)
2. Knowledge ← ใช้ข้อมูลจาก Ingest
3. Nova ← ออกแบบ/architecture บนข้อมูลที่มี
4. Security ← วิเคราะห์ความปลอดภัยของระบบที่มีแล้ว
5. Compliance ← ชั้นบนสุด อาศัยทุกตัวก่อนหน้า
