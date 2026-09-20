# Master Index — CloudForge Ingest Studio

> Navigation hub for this repository. For platform-wide standards, see
> [CloudForge-Platform-Foundation](https://github.com/CloudForge-Platform-Foundation-dev/CloudForge-Platform-Foundation).

---

## Getting Started

| Document | Status | Description |
|----------|--------|-------------|
| [README.md](README.md) | ✅ Approved | Local dev, endpoints, internal architecture, auth setup |
| [openapi.yaml](openapi.yaml) | ✅ Approved | API contract |

## Source (`src/`)

| Module | Status | Description |
|---|---|---|
| [src/main.py](src/main.py) | ✅ Approved | FastAPI app entrypoint, route wiring |
| [src/parsers/](src/parsers/) | ✅ Approved | CSV/JSON/Excel parsers, field mapping, format registry |
| [src/ai_guard/](src/ai_guard/) | 🔄 Partial | AI-based validation layer — `local_backend.py` works; `cloud_backend.py` is an intentional stub (`NotImplementedError`) |
| [src/resilience/](src/resilience/) | ✅ Approved | Backpressure and retry logic |
| [src/storage.py](src/storage.py) | 🔄 Draft (stub) | In-memory ingest job storage (MVP) |
| [src/models.py](src/models.py) / [src/enums.py](src/enums.py) | ✅ Approved | Shared data models and enums |
| [src/auth/](src/auth/) | ✅ Approved | JWT auth pattern (standard across all Studios — do not modify without an ADR) |

## Testing

| Document | Status | Description |
|---|---|---|
| [tests/](tests/) | ✅ Approved | Test suite |

## Governance & Contribution

| Document | Status | Description |
|---|---|---|
| [ROADMAP.md](ROADMAP.md) | ✅ Approved | Planned work by phase |
| [CHANGELOG.md](CHANGELOG.md) | ✅ Approved | Release history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | ✅ Approved | Contribution workflow |
| [SECURITY.md](SECURITY.md) | ✅ Approved | Security policy |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | ✅ Approved | Code of conduct |
| [SUPPORT.md](SUPPORT.md) | ✅ Approved | Where to get help |
| [docs/adr/](docs/adr/) | 🔄 Empty | No ADRs recorded yet for this Studio |

## Known Gaps (tracked, not blocking)

- No `schemas/` directory yet — see [ROADMAP.md](ROADMAP.md) Phase 3
- `CloudAIBackend` is an intentional stub, not yet connected to a real provider
- Ingest job storage is in-memory (MVP), not persistent

---

## Version

Current version: see [VERSION](VERSION). Compatible with
CloudForge-Platform-Foundation as declared in `validate-against-foundation.yml`.

**Note:** this repository's name on GitHub currently has a leading `-`
(`-cloudforge-ingest-studio`), inconsistent with the naming convention in
CloudForge-Platform-Foundation's `docs/standards/naming-conventions.md`
(`cloudforge-{domain}-{type}`). Planned rename: `cloudforge-ingest-studio`.
