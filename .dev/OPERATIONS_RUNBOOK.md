# Operations Runbook

## Deployment Topology

Production requires a TLS load balancer or ingress, at least two stateless API
instances across failure domains, PostgreSQL 16 with automated failover/backups,
central logs/metrics/alerts and durable object storage before document upload is
enabled. `compose.production.yaml` is a hardened single-host reference, not high
availability infrastructure.

Set `FORWARDED_ALLOW_IPS` to the exact address or comma-separated trusted proxy
addresses. Never use `*`; direct clients must not be able to forge forwarding data.

## First Superadministrator

Accounts and password hashes live only in PostgreSQL; no credential is ever placed
in `.env`, environment variables, command arguments or deployment files.

1. From an interactive terminal on the host, run
   `docker compose -f compose.production.yaml exec api python -m app.cli.create_superadmin`.
2. Type name, email and password when prompted (hidden, confirmed, 16+ characters).
   The command refuses non-interactive input.
3. Confirm the event `superadmin_created`. An existing email returns
   `superadmin_exists` and the account is not modified.
4. Create every other account from `Configuracion > Usuarios`.

## Announcement Drafts For Approval

Announcements, the modality catalog and the database catalog are managed only by
superadministrators in `/configuracion`. To leave a prepared announcement waiting
for approval:

1. Write its content as JSON (`category`, `title`, `summary`, `body`, optional
   `link_url`, `image_url`, `image_alt`); the form rules apply.
2. Run on the host, with the JSON on standard input:
   `docker compose -f compose.production.yaml exec -T api python -m app.cli.create_announcement_draft --author <superadmin-email> < announcement.json`.
3. Confirm `announcement_draft_created`. The draft is never published and a
   repeated title is refused (`announcement_draft_exists`).
4. A superadministrator approves it, adjusts it or rejects it in
   `/configuracion > Comunicados`; every step is recorded in
   `announcement_audit_events`.

## Sessions And Login Lockout

- Sessions live in `sesiones`; only HMAC digests are stored. Production requires
  `SESSION_COOKIE_SECURE=true` and HTTPS.
- Revoke one account: set it `Inactivo` or change its password in
  `Configuracion > Usuarios`; its sessions end immediately.
- Revoke every session (suspected compromise): rotate `SECRET_KEY` and redeploy.
  This also resets login lockout counters.
- Lockout: `LOGIN_MAX_FAILED_ATTEMPTS` failures within `LOGIN_LOCKOUT_MINUTES`
  block that email until the window passes. Rows hold only HMAC digests, so a
  specific account cannot be unlocked early by inspection; wait for the window.
  Many lockouts in a short period are an authentication anomaly (see Incident
  Signals).

## Deploy And Roll Back

1. Back up the database and record the current image digest and Alembic revision.
2. Run migrations as one job: `alembic upgrade head`.
3. Roll out the immutable API image gradually; require readiness before traffic.
4. Validate login, role scope, degree-work happy path, error rate and latency.
5. On regression, stop promotion and restore the previous image. Reverse schema only
   when the reviewed migration explicitly supports downgrade; otherwise roll forward.

Single-host reference command:

```powershell
docker compose --env-file .env.production -f compose.production.yaml up -d --build
```

## Backup And Restore

Use platform-managed point-in-time recovery where available. A portable logical
backup can be created with:

```powershell
docker compose exec -T db pg_dump -Fc -U researchhub_user researchhub_u > researchhub.dump
```

Restore into an isolated database, never over the active database, then validate
row counts, latest audit timestamp, application readiness and representative user
journeys. Record elapsed recovery time and recovered timestamp as RTO/RPO evidence.

## Incident Signals

- Page on readiness failure, 5xx ratio above 0.5% for 10 minutes, exhausted database
  pool, replication lag threatening RPO or repeated authentication anomalies.
- Correlate by `x-trace-id`; do not request passwords, tokens or document contents.
- Declare incident owner, preserve logs/audit evidence, contain, recover, communicate
  and write a blameless review with corrective actions.

## Capacity

Scale API replicas only after checking the connection-budget formula in
`CONSTRAINTS.md`. Measure p50/p95/p99 latency, throughput, errors, CPU, memory,
database locks/connections and slow queries with production-like data volume.
