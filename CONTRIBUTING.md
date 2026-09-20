# Contributing to CloudForge Ingest Studio

> Thank you for investing your time in contributing to this project!

---

## Contribution Workflow

```
Issue / Proposal
        |
        v
Implementation + Tests + Documentation
        |
        v
scripts/validate.sh (local) — if present, else run test suite
        |
        v
Pull Request
        |
        v
foundation-validation CI gate must pass
        |
        v
Review & Approval
        |
        v
Merge into main
```

---

## Pull Request Requirements

Before submitting a PR, verify:

- [ ] Code follows the existing `src/` structure and style
- [ ] Tests added/updated under `tests/`
- [ ] Documentation updated in the same PR (README.md, docs/, openapi.yaml if the API changed)
- [ ] CHANGELOG.md updated
- [ ] VERSION bumped (if the change is user-facing)
- [ ] No hardcoded secrets or credentials
- [ ] `foundation-validation` CI gate passes (`validate-against-foundation.yml`)

---

## Architecture Decision Records (ADR)

Any decision that changes the auth pattern, data model, or API contract of this Studio should
be recorded as an ADR under `docs/adr/`, using the template in
[CloudForge-Platform-Foundation/templates/adr-template.md](https://github.com/CloudForge-Platform-Foundation-dev/CloudForge-Platform-Foundation/blob/main/templates/adr-template.md).

---

## Platform Standards

This repository must stay compliant with the Repository Standards Checklist defined in
[CloudForge-Platform-Foundation/README.md](https://github.com/CloudForge-Platform-Foundation-dev/CloudForge-Platform-Foundation#-repository-standards-checklist).
The auth pattern (`src/auth/config.py`, `src/auth/jwt.py`, `src/auth/dependencies.py`) is
standardized across all Studios — do not deviate from it without an ADR at the Foundation level.

---

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

---

## Questions?

Open a GitHub Issue in this repository, or see [SUPPORT.md](SUPPORT.md).
