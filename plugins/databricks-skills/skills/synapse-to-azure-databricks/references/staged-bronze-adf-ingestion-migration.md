# Staged Bronze stage 4: ADF ingestion migration

Start only after stage 3 is `PASS` and approved. Replace only approved ADF
ingestion and write the same managed Bronze contract already consumed by
Silver and Gold.

## Inventory and map

Use the [pipeline workflow skill](../../pipelines-to-azure-databricks-workflows/SKILL.md)
to inventory ADF pipelines and dependencies, classify activities, and design
or convert orchestration. Apply its disposition and package within this stage's
Bronze ownership and cutover gates.

Map approved file ingestion to Auto Loader, bounded `COPY INTO`, or Lakeflow;
approved relational ingestion to Lakeflow Connect or a governed connector;
transformations to reviewed Spark or declarative pipelines; and durable control
state to managed Unity Catalog tables. Keep inaccessible or unsupported
ingestion components `retain`, `redesign`, or `blocker`. Never record secret
values.

## Ingestion contract

Generate versioned mappings, schema and quarantine rules, idempotent write
behavior, duplicate prevention, run/audit logging, bounded retry and restart,
alerts, environment parameters, secret references, grants, Asset Bundle
resources, paused schedules, reconciliation, cutover, rollback, and a deferred
backlog.

Advance a watermark only after a successful target commit and required audit
work. A replay must not duplicate accepted records.

## Ownership and exit

Parallel tests may use separate approved targets. ADF and Databricks must not
write one production Bronze target concurrently without an explicit tested
concurrency and ownership design.

After validation and transfer approval, quiesce ADF schedules, capture the final
watermark, catch up, and reconcile. Then assign `databricks-owned` and activate
only approved Databricks schedules. Do not decommission ADF until rollback,
consumer acceptance, and retention obligations pass.

Pass only after full/incremental, watermark, replay, restart, duplicates,
schema, late data, concurrency, alerting, performance, and reconciliation
tests pass and rollback remains proven.

