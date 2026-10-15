# Synapse Serverless SQL to Databricks Migration Plan

## Scope

- Source workspace/serverless endpoint:
- Databases/schemas and exclusions:
- Target workspace/metastore/environment:
- Catalog/schema policy:
- Data-movement policy:
- Owners/approvers:
- Retained source-ingestion boundary:
- In-scope post-staging transformation boundary:

## Current state

- SQL objects and dependencies:
- External sources, paths, formats, and update processes:
- Identities, grants, and storage access:
- Consumers, drivers, SLAs, and usage baseline:
- Lakebridge evidence and fallback scope:
- Pipelines, activities, schedules, parameters, retries, and failure behavior:
- Control metadata, persistence/aggregation flags, watermarks, and execution ordering:
- Persisted facts/dimensions, producers, writer ownership, serving views, and consumers:

## Target mapping

| Source object/path | Target UC object/location | Pattern | Data action | Runtime identity | Owner |
|---|---|---|---|---|---|
| | | | register/convert/copy/ingest/retain/none | | |

## Pipeline and persisted-output mapping

| Source pipeline/control | Inputs | Produced fact/dimension | State and refresh | Quality rules | Recovery contract | Target pattern | Eligibility evidence and rationale | Writer owner | Serving objects | Disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | full/incremental/snapshot; watermark | | retry/restart/replay/idempotency | SQL view/materialized view/Lakeflow/Job | feature support, orchestration needs, SLA, cost | | | migrate/retain/park/retire |

## Waves

| Wave | Objects/dependencies | Consumers | Build and validation | Cutover window | Rollback |
|---|---|---|---|---|---|
| 1 | | | | | |

## Azure and Unity Catalog changes

- Managed identity or Access Connector:
- Azure RBAC/ACL changes and exact scope:
- Storage credentials and workspace bindings:
- External locations, overlaps, and read-only policy:
- Catalog/schema ownership and grants:
- Network changes:
- SQL Warehouse policy, scaling, auto-stop, tags, and budget:
- Lakeflow or Job configuration, schedule, monitoring, and budget:
- Managed Delta output ownership, locations, schema evolution, and grants:

## Validation and acceptance

- Shared revision/snapshot/watermark:
- Coverage and required comparison modes:
- Security personas and negative tests:
- Performance/concurrency/cost thresholds:
- Consumer acceptance:
- Pipeline idempotency, replay, restart, duplicate, late-arriving-data, and watermark acceptance:
- Fact grain, dimension-key, referential-integrity, aggregate, and serving-view acceptance:
- Checks that may remain `NOT RUN`:

## Risk and rollback

- Risks/mitigations:
- Definition freeze or dual maintenance:
- Data synchronization and writer ownership:
- Retained-ingestion handoff and partial-failure recovery:
- Numeric/binary rollback triggers:
- Endpoint/config rollback:
- Data rollback when target writes occur:
- Source retention window:

## Approval record

| Gate | Approver/evidence | Date/expiry | Status |
|---|---|---|---|
| Architecture and data movement | | | |
| Azure RBAC and UC writes | | | |
| Development deployment | | | |
| Production deployment | | | |
| Consumer cutover | | | |
| Source retirement | | | |
