# Product Readiness - ResearchHUB

## Purpose

ResearchHUB is developed as an operational product, not as a disposable
prototype. This file records the evidence required to promote a version. It does
not assert that the current incomplete functional scope is already approved for
institutional production.

## Current Baseline

| Area | State | Evidence or remaining work |
|---|---|---|
| Modular FastAPI/PostgreSQL runtime | Implemented | Health probes, Alembic, pooled connections and production Compose profile. |
| Identity bootstrap | Implemented | Explicit one-time command; no request-time seed or password reset. |
| RBAC backend | Partial | Existing permissions are enforced; full role/scope matrix from SPEC-TG-001 remains required. |
| Degree-work workflows | Partial | First operational iteration exists; not all policy modalities and transitions meet acceptance criteria. |
| Documents and evidence | Blocked | Durable object storage, malware scanning, retention and legal requirements are unresolved. |
| Institutional integrations | Blocked | Admisiones y Registro, SACC, SNIES/HECCA and identity provider contracts are unresolved. |
| Observability | Partial | JSON request logs, trace IDs and health probes exist; metrics, dashboards and alert routing remain external work. |
| Continuity | Defined | RPO/RTO and runbook are defined; automated backup and restore evidence are deployment responsibilities. |
| Security validation | Partial | Fail-fast configuration and headers exist; SAST/SCA/DAST and penetration testing are required before GO. |
| Capacity evidence | Pending | Run the agreed load model against production-equivalent infrastructure. |

## Mandatory GO Evidence

1. Product owner accepts all enabled capability acceptance criteria and unresolved
   policy questions do not affect those capabilities.
2. CI is green for lint, types, unit, integration, migration and browser journeys.
3. Threat model, dependency scan and penetration test have no unaccepted Critical
   or High finding.
4. Load test meets `CONSTRAINTS.md` with 30% database connection headroom.
5. Monitoring demonstrates logs, metrics, alerts and trace correlation without
   sensitive payloads.
6. Backup restoration meets RPO 15 minutes and RTO 60 minutes.
7. Rollback and migration rehearsal succeeds in a production-equivalent environment.
8. Data owner approves retention, privacy notice, access matrix and audit retention.
9. Support owner, escalation path and maintenance window are named.

Until every mandatory item has evidence, the release decision is `NO-GO` for
institutional production, even though the software must continue to be engineered
to production standards.
