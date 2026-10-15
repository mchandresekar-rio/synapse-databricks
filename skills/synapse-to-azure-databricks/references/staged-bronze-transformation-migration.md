# Staged Bronze stage 2: transformation migration

Start only after stage 1 is `PASS` and approved. Read Bronze through
parameterized three-part Unity Catalog names.

## Target selection

Build the dependency graph from external Bronze through staging,
transformations, persisted outputs, serving objects, and consumers.

- Use Databricks SQL views for thin stateless logic.
- Use modular Spark SQL or PySpark for complex or procedural rewrites.
- Use Lakeflow Declarative Pipelines for eligible declarative incremental,
  CDC, quality, or persisted-table behavior.
- Use Databricks Jobs for imperative or mixed orchestration.
- Materialize target-owned Silver and Gold as managed Delta.
- Group code by business domain and dependency; do not create one notebook per
  source view.

Preserve joins, filters, null behavior, casts, rounding, time zones, date
boundaries, ordering, aggregation grain, KPIs, keys, watermarks, retries,
idempotency, and error behavior. Keep generated schedules paused. Unsupported
T-SQL must have a source location, impact, disposition, owner, and decision.

## Validate and exit

Compare schema, keys, hashes, counts, nulls, duplicates, aggregates,
partitions, joins, filtering, rounding, dates, KPIs, fact grain, dimensions,
late data, replay, retries, restart, watermark, performance, and consumers.

Pass only when every object has a target/disposition, dependencies and syntax
validate, calculations reconcile, all reads use Unity Catalog names, source
ingestion remains operational, Silver/Gold rebuild deterministically, and
stage 3 progression approval is recorded separately.

