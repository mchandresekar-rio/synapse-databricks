# Migration Validation Report

## Context

- Source endpoint/database and identity:
- Target workspace/Warehouse/catalog/schema and identity:
- Source and target revisions:
- Shared snapshot/watermark/time zone:
- Manifest checksum:
- Validator/tool versions and run time:

## Coverage

| Category | In scope | Passed | Failed | Retained | Not run |
|---|---:|---:|---:|---:|---:|
| Objects | | | | | |
| Storage paths | | | | | |
| Permissions/personas | | | | | |
| Consumers | | | | | |
| Pipelines and schedules | | | | | |
| Control metadata and watermarks | | | | | |
| Persisted facts/dimensions | | | | | |

## Validation ladder

| Layer | Status | Evidence | Difference or next action |
|---|---|---|---|
| Coverage | NOT RUN | | |
| Static | NOT RUN | | |
| Deployment | NOT RUN | | |
| Metadata | NOT RUN | | |
| Data | NOT RUN | | |
| Query | NOT RUN | | |
| Security/negative | NOT RUN | | |
| Performance | NOT RUN | | |
| Consumer | NOT RUN | | |
| Operations/rollback | NOT RUN | | |
| Pipeline/restart | NOT RUN | | |
| Persisted-output parity | NOT RUN | | |

## Parity cases

| Test ID | Source/target | Mode | Status | Mismatch summary | Evidence |
|---|---|---|---|---|---|
| | | metadata/aggregate/partition/keyed_rows/query_result/business_rule/performance/pipeline_contract | NOT RUN | | |

## Deployment and runtime evidence

- Bundle/configuration validation:
- Changed target resource IDs and hashes:
- SQL Warehouse/job/pipeline evidence:
- Monitoring and alert evidence:
- Retained-ingestion handoff and target writer evidence:
- Pipeline runs, retries, restart, replay, and watermark evidence:
- Managed Delta facts/dimensions and serving-view evidence:

## Performance

- Workload, parameters, repetitions, and concurrency:
- Compute and cache conditions:
- Source duration/throughput/bytes/cost signal:
- Target duration/throughput/bytes/cost signal:
- Threshold and verdict:

## Decision

- Unresolved blockers:
- Accepted differences, owners, evidence, and expiry:
- Checks not run and prerequisites:
- Rollback readiness:
- Consumer acceptance:
- Cutover verdict: `PASS`, `FAIL`, or `BLOCKED`
