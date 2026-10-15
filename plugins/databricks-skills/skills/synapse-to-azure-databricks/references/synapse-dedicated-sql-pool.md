# Synapse Dedicated SQL Pool to Azure Databricks

Use this reference only for provisioned or dedicated SQL pools. The source stores and distributes relational data; it is not the Serverless SQL metadata-over-files model.

## Scope and discovery

Inventory schemas, tables, distributions, partitions, indexes, materialized views, statistics, views, functions, procedures, security objects, workload groups, resource classes, result-set caching, loads, exports, consumers, data volumes, concurrency, SLAs, recovery requirements, and source-to-target synchronization needs.

Capture row counts, table sizes, skew indicators, distribution keys, partition boundaries, column data types, constraints, dependencies, query history, and load patterns. Treat source discovery as read-only.

## Lakebridge capability boundary

Apply the common Lakebridge contract from the parent skill. Use supported
Profiler or Analyzer capabilities for assessment, then run the separate
Lakebridge conversion gate before using a transpiler. A Lakebridge `synapse`
transpiler may be considered only when the installed release documents
Dedicated SQL Pool support and a representative conversion pilot covers the
exact DDL, DML, procedural, and query constructs. Assessment success does not
prove transpiler support. Unsupported workload management, distribution,
indexing, transaction, or procedural behavior remains an explicit gap.

## Target mapping

| Dedicated SQL Pool source | Databricks candidate |
|---|---|
| Relational table | Unity Catalog managed Delta table unless an approved external lifecycle is required |
| Distribution and columnstore options | Re-design for Delta layout, liquid clustering, partitioning, and query behavior; do not copy hints |
| CTAS or batch transformation | Databricks SQL, Lakeflow Declarative Pipeline, or Job task selected by state and orchestration |
| Stored procedure or dynamic SQL | Databricks SQL scripting when behavior is supported, otherwise a parameterized Job or notebook |
| Workload group or resource class | SQL warehouse sizing, policies, query controls, and workload separation |
| Security principal and grant | Unity Catalog identity, group, ownership, and least-privilege grant mapping |

## Data migration gate

Dedicated SQL migration normally includes data movement. Before copying data, approve the extraction method, target table design, initial-load window, incremental synchronization, change freeze, source-of-truth transition, encryption, network path, cost, retry behavior, and rollback.

Keep source and target row-level data out of prompts and logs. Preserve immutable load manifests with source partitions, counts, hashes or aggregate checks, target tables, attempts, and failures.

## Conversion and validation

- Remove `HASH`, `ROUND_ROBIN`, `REPLICATE`, and columnstore syntax only after an approved physical-design decision.
- Validate type mappings, identity behavior, defaults, constraints, collations, time zones, transaction boundaries, and error semantics.
- Validate procedures and dynamic SQL behavior, not only emitted syntax.
- Reconcile row counts, aggregates, nulls, keys, duplicates, partitions, and approved row-level samples.
- Test concurrency, performance, workload isolation, recovery, incremental synchronization, security, consumers, and cost.
- Cut over only after the final synchronization and rollback plan are approved.

## Must

- Preserve distribution and workload-management intent as assessment evidence.
- Approve data movement and source-of-truth transition explicitly.
- Use managed Delta by default for target-owned data.
- Keep unsupported procedural behavior visible.

## Prefer

- A bounded representative pilot before estate-wide conversion.
- Partition- or table-level resumable loads with immutable manifests.
- Query-shape-driven Delta optimization rather than copied Synapse physical hints.

## Avoid

- Do not treat a Dedicated SQL Pool as Serverless SQL.
- Do not discard distribution keys before skew and join analysis.
- Do not claim parity from successful DDL creation or aggregate counts alone.
- Do not cut over while synchronization or rollback is unresolved.

## Examples

- "Assess a Synapse Dedicated SQL Pool and design managed Delta targets before moving data."
- "Pilot Lakebridge conversion for representative dedicated-pool tables, views, and procedures."
