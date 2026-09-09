# ResarchHUB Quality Contract

This contract applies to every production-bound change. A constraint may only be
weakened through an explicit product and engineering decision recorded in an ADR.

## Product Integrity

- Business behavior must trace to an approved requirement in `.dev`.
- Authorization is enforced in the backend by permission and data scope; hidden UI
  is never an authorization control.
- Published workflows, decisions, evaluations and audit records are immutable.
- No demo users, shared passwords or automatic credential resets exist in runtime
  code, images or operational documentation.
- A release must not claim a capability whose acceptance criteria are incomplete.

## Quality Gates

- `python -m ruff check app tests` has zero errors.
- `python -m mypy app` has zero errors.
- `python -m pytest` has zero failures and includes positive and negative tests for
  every changed authorization or workflow rule.
- Database changes use reviewed Alembic migrations and are tested from an empty
  database and from the previous supported revision.
- Critical user journeys are verified at 320, 768 and 1440 CSS pixels with keyboard
  access, no horizontal overflow and WCAG 2.2 AA contrast.
- No Critical or High known dependency vulnerability is accepted without a dated,
  approved exception and mitigation.

## Reliability And Performance

- Monthly availability SLO: 99.9%, excluding approved maintenance.
- API 5xx ratio SLO: below 0.5% over 30 minutes.
- At the initial capacity baseline of 100 concurrent sessions, p95 is below 500 ms
  for reads and 800 ms for writes, excluding file transfer and external systems.
- PostgreSQL connection capacity must satisfy:
  `replicas * workers * (pool_size + max_overflow) <= 70% max_connections`.
- Production backup objectives: RPO 15 minutes and RTO 60 minutes. Restore is
  rehearsed at least quarterly and before a destructive migration.

## Security And Privacy

- Production starts fail-fast when debug/docs/HSTS/secrets are unsafe.
- Secrets are supplied by the deployment platform, never committed to Git.
- Tokens, passwords, document content and sensitive personal data are never logged.
- TLS terminates at the trusted ingress, authentication endpoints are rate-limited
  there, and database access is restricted to private networks.
- Security headers, trusted hosts, least privilege and immutable audit records remain
  release requirements.

## Release Decision

Production promotion requires evidence for all gates in
`.dev/PRODUCT_READINESS.md`. Any unmet mandatory gate makes the decision `NO-GO`;
it is not converted into a documentation-only warning.
