# Roadmap — CloudForge Ingest Studio

## Phase 1: MVP (Current)
- [x] CSV/JSON/Excel parsers
- [x] Field mapping layer to the canonical schema
- [x] AI Guard with local fallback backend
- [x] Resilience (backpressure/retry) layer
- [x] JWT auth pattern aligned with Foundation standard
- [x] Test suite
- [x] foundation-validation CI gate integration

## Phase 2: Cloud AI Backend
- [ ] Implement `CloudAIBackend` (currently a stub raising `NotImplementedError`
      intentionally) — connect to a real cloud AI Guard provider
- [ ] Config-driven backend selection (local vs. cloud) with fallback on failure

## Phase 3: Schema & Storage
- [ ] Add `schemas/` directory with Ingest-specific schema extensions
      (ingest job, mapping rule) on top of the Foundation canonical entity/event schemas
- [ ] Persistent storage for ingest job status (currently in-memory / MVP)

## Phase 4: Platform Integration
- [ ] Direct hand-off contract with Knowledge Studio for parsed output
- [ ] Additional parser formats as new Studios require them

## Phase 5: Production Hardening
- [ ] Rate limiting per auth scope
- [ ] Audit logging for ingest jobs
- [ ] Dead-letter queue for failed ingest jobs
