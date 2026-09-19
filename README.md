# CloudForge Ingest Studio

Studio ตัวแรกของ CloudForge Platform — รับข้อมูลดิบ (CSV/JSON/Excel) ผ่าน AI Guard และ mapping layer แล้วส่งต่อเข้าสู่ pipeline ตาม roadmap:
**Ingest** → Knowledge → Nova → Security → Compliance

## Local Dev

```bash
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/healthz

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| GET | `/healthz` | Health check สำหรับ probes และ monitoring |
| GET | `/` | Root info endpoint |
| POST | `/ingest` | รับข้อมูลดิบเข้า pipeline |
| POST | `/ingest/file` | อัปโหลดไฟล์ (CSV/JSON/Excel) เพื่อ parse และ map เข้าสู่ schema กลาง |
| GET/GET | `/ingest/{ingest_id}` | ดึงสถานะ/ผลลัพธ์ของ ingest job ตาม id |

## สถาปัตยกรรมภายใน (`src/`)

- **`parsers/`** — ตัวแปลงไฟล์ดิบเป็นข้อมูลโครงสร้าง
  - `csv_parser.py`, `excel_parser.py`, `json_parser.py` — parser เฉพาะแต่ละฟอร์แมต
  - `mapping.py` — จับคู่ field จากไฟล์ต้นทางเข้าสู่ schema กลางของ CloudForge
  - `registry.py` — ทะเบียนกลางของ parser ที่รองรับ
- **`ai_guard/`** — ชั้นตรวจสอบ/กรองข้อมูลก่อนเข้า pipeline ด้วย AI
  - `guard.py` — logic หลักของการตรวจสอบ
  - `cloud_backend.py`, `local_backend.py` — รองรับทั้งโมเดลบน cloud และรันในเครื่อง
- **`resilience/`** — backpressure และ retry logic เพื่อรองรับโหลดสูง
- **`auth/`** — JWT authentication (รูปแบบเดียวกับ Foundation pattern มาตรฐาน)

## Auth

ใช้ JWT (RS256) จาก CloudForge Identity Service แบบเดียวกับทุก Studio ในแพลตฟอร์ม (`src/auth/config.py`, `src/auth/jwt.py`, `src/auth/dependencies.py`) — ตรวจ signature/exp/iss/aud ผ่าน JWKS

ตั้งค่าผ่าน environment variables (prefix `CLOUDFORGE_`):

| Variable | Default |
|---|---|
| `CLOUDFORGE_JWT_ISSUER` | `https://auth.cloudforge.internal` |
| `CLOUDFORGE_JWT_JWKS_URI` | `https://auth.cloudforge.internal/.well-known/jwks.json` |
| `CLOUDFORGE_JWT_AUDIENCE` | `cloudforge-ingest-studio` |

## Governance / Foundation Validation

Workflow `.github/workflows/validate-against-foundation.yml` เรียกผ่าน
`niphan1000-cyber1000/foundation-validation/.github/workflows/reusable-gate.yml@v1.0.1`

**ต้องตั้งค่าก่อนใช้งานจริง:**

1. เพิ่ม repo secret `FOUNDATION_PAT` (PAT ที่มีสิทธิ์อ่าน `CloudForge-Platform-Foundation` และ `foundation-validation`) — **มีแล้ว** ✅
2. ยืนยันว่า `openapi.yaml` มี `x-owner` ตามกฎ Foundation `.spectral.yaml` — มีแล้ว: `x-owner: ingest-team` ✅

**หมายเหตุสำคัญ**: `foundation-validation` เป็น public repo ของ user account ที่ต่างเจ้าของกับ org `CloudForge-Platform-Foundation-dev` — การเรียก reusable workflow ข้าม owner แบบนี้ทำได้เฉพาะเมื่อ repo ต้นทางเป็น **public** เท่านั้น (private repo reusable workflow ใช้ข้าม owner ไม่ได้ตาม policy ของ GitHub)

## Roadmap ของโปรเจกต์ (ลำดับ Studio)

1. **Ingest** ← ตอนนี้ (รับข้อมูลดิบ + AI Guard + mapping)
2. Knowledge (RAG pipeline พื้นฐาน)
3. Nova
4. Security
5. Compliance
