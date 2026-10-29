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

1. Set the three `BOOTSTRAP_SUPERADMIN_*` values through the secret manager and set
   `BOOTSTRAP_SUPERADMIN_ENABLED=true`.
2. Run `python -m app.cli.bootstrap_superadmin` as a one-off deployment job.
3. Confirm the event `superadmin_bootstrap_created`; the command returns `existing`
   without modifying an account when the email already exists.
4. Set `BOOTSTRAP_SUPERADMIN_ENABLED=false`, remove the bootstrap password and
   redeploy. Rotate the initial account password through the approved channel.

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
