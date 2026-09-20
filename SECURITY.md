# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (see VERSION) | ✅ Yes |

## Reporting a Vulnerability

Please **DO NOT** open a public issue for security vulnerabilities.

Instead:
1. Email: security@cloudforge.example.com (replace with actual)
2. Or use GitHub Security Advisories on this repository

We will respond within 48 hours.

## Security Standards

This Studio implements the CloudForge Platform Foundation security baseline
(see `CloudForge-Platform-Foundation/docs/security/security-baseline.md`):

- [x] JWT (RS256) authentication via JWKS, validated per request
- [x] Scope-based authorization per endpoint (`require_scope(...)`)
- [ ] Encryption in Transit (TLS 1.3+) — enforced at the ingress/load balancer, not in-app
- [ ] Secrets Management — no hardcoded secrets; all config via environment variables
- [ ] Dependency Scanning
- [ ] Static Code Analysis (SAST)
- [ ] Audit Logging
- [ ] Continuous Security Monitoring

## Security Review Process

Security reviews are mandatory for:
- Changes to `src/auth/` (authentication/authorization)
- Data model or schema changes affecting PII
- New external dependencies

## Threat Model

See the platform-wide threat model in
[CloudForge-Platform-Foundation/docs/security/security-baseline.md](https://github.com/CloudForge-Platform-Foundation-dev/CloudForge-Platform-Foundation/blob/main/docs/security/security-baseline.md).
