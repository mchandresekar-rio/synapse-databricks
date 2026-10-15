# Target mapping and approval

Map source items by stable identity and dependency order. Assume the workspace
and Unity Catalog are provisioned. A mapping must state the selected existing
catalog/schema, compute, storage location, deployment environment, retained
external orchestrator, validation method, and rollback action.

Present migration choices when target mappings are incomplete. Do not branch
into workspace, identity, networking, or permission provisioning.

Approval must cover naming, compute cost, data movement, orchestration
boundaries, deployment order, acceptance criteria, and rollback.

## Namespace mapping

Choose and document one mapping policy per migration boundary:

| Source boundary | Common Unity Catalog target | Appropriate when |
|---|---|---|
| Database | Catalog | Source databases represent durable domains or environments |
| Database | Schema in an environment catalog | The organization mandates catalog-per-environment |
| Several databases | Domain catalog with collision-free schemas | Consolidation is approved and every name is mapped explicitly |
| Schema/object | Schema/table, view, or function | The target type preserves the approved contract |

Maintain a registry from every source name to a fully qualified `catalog.schema.object` name. Record collisions, reserved words, quoted identifiers, case sensitivity, ownership, cross-catalog dependencies, and consumers before conversion.

## Data-placement decision

Choose one disposition for every source path:

- **Register existing data:** create the narrowest approved external location and a Unity Catalog external table. Use for stable, supported formats whose lifecycle remains external. Make raw or shared zones read-only where possible.
- **Convert in place:** change eligible files to Delta only after approving writer coordination, protocol compatibility, downstream readers, rollback, and the fact that this mutates storage.
- **Copy or clone:** move data into target-owned Delta when lifecycle transfers to Databricks or the source layout is unsuitable. Define initial load, incremental synchronization, reconciliation, and source-of-truth transition.
- **Ingest continuously:** use an approved batch or streaming pipeline for recurring files, schema evolution, quarantine, and operational ownership.
- **Retain or park:** preserve an external contract when migration would be unsafe or is outside the current wave.

Default the first serverless SQL migration wave to registration without copying. Any conversion, copy, clone, overwrite, or recurring ingestion requires explicit data-owner approval.

## Format and workload choices

| Source | Default candidate | Required checks |
|---|---|---|
| Delta | External table or managed clone | Protocol/features, concurrent writers, ownership |
| Parquet | External table or approved Delta conversion | Schema, partitions, file layout, write ownership |
| CSV | Explicit-schema external table or ingestion to Delta | Encoding, delimiter, quoting, headers, nulls, rejects |
| JSON/semi-structured | Explicit-schema ingestion to Delta | Malformed records, evolution, rescued data |
| Interactive SQL | Databricks SQL Warehouse | Region, networking, authentication, concurrency, startup, cost |
| Stable semantic object | Unity Catalog view or function | Dialect, output contract, privileges, dependencies |
| Repeated transformation | Job or Lakeflow Spark Declarative Pipeline | Idempotency, scheduling, quality, recovery |
| Procedural logic | Current SQL scripting/procedure support, job, or notebook | Parameters, transactions, side effects, failure semantics |

Parameterize environment-specific catalogs, schemas, warehouses, locations, and identities. Bind production credentials and storage only to approved workspaces and deployable targets.
