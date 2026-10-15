# Synapse Serverless SQL Pool → Azure Databricks SQL and Lakehouse

Use this mode when the source is a Synapse **serverless SQL pool**. It migrates metadata, SQL logic, security intent, and consumer connectivity to Azure Databricks. It does not treat the source as a dedicated pool and does not imply source-row movement: serverless SQL stores metadata while querying files in external storage.

Assume source and target access works, the Databricks workspace exists, and
Unity Catalog is provisioned. Do not perform Azure Arc, workspace, metastore,
identity, role-assignment, networking, or target-platform setup. When an
operation encounters a permission failure, record the affected object as
blocked with the exact failed operation and continue independent migration
work.

## Reference architecture

For a metadata-over-files migration, begin at the approved existing ADLS Gen2 or Blob boundary. Keep upstream ingestion unchanged when it is outside the approved scope. Register governed Unity Catalog external tables, convert staging and semantic SQL, rebuild approved persisted-output flows with Lakeflow Declarative Pipelines or eligible Databricks SQL materialized views, store target-owned Delta facts and dimensions where required, and serve consumers through a Databricks SQL Warehouse.

- Use Databricks SQL materialized views for selected expensive, repeatedly queried joins or aggregations when an explicit refresh SLA and cost boundary are approved.
- Use Lakeflow Declarative Pipelines for the in-scope staging-to-fact/dimension flow when it is declarative and requires data-quality expectations, incremental state, or durable managed Delta outputs. Use Databricks Jobs for imperative orchestration. This does not move the upstream source-ingestion pipeline into scope.
- Do not replace every Synapse serverless view with a materialized view or Lakeflow pipeline. Thin projections and semantic views normally remain Databricks SQL views over named Unity Catalog tables.

## Non-negotiable phase order

1. Read-only discovery, inventory, and routing.
2. Compatibility assessment and classification.
3. Target mapping and mapping-gap resolution.
4. Conversion and packaging.
5. Non-production deployment.
6. Layered validation.
7. Consumer cutover and closure with rollback readiness.

Do not skip from discovery directly to SQL conversion.

## Lakebridge-first decision gate

Use a two-option strategy and record the decision per phase in the migration manifest.
For every object, record Lakebridge Assessment Status, Lakebridge Transpiler
Status, and Migration Inventory Status using the parent skill's controlled
values. These are separate results, not one combined Lakebridge flag.

### Option 1 — Lakebridge-assisted

Prefer Databricks Labs Lakebridge only for capabilities explicitly supported by the installed release:

- Use the Synapse Profiler for serverless databases, tables, columns, views,
  routines, and workload observations.
- Use Analyzer against exported serverless SQL artifacts for inventory, complexity, and dependency evidence without connecting to the source.
- Use Reconcile only when the installed release documents the required Synapse serverless source, object, and report type, and the user approves the exact source and target queries.
- Use a Lakebridge transpiler only when its current capability matrix explicitly covers Synapse serverless SQL and a representative pilot covers the exact constructs. Capture warnings and unsupported nodes; never treat successful emission as semantic validation.

At the time this guidance was authored, Lakebridge's documented `synapse` transpilers target **dedicated SQL pools**, while its assessment code and guidance include serverless profiling and export. Therefore the default serverless path is Lakebridge for supported assessment, followed by Option 2 for serverless-specific conversion. Re-check the installed release rather than freezing this limitation forever.

At Phase 4, check Lakebridge transpiler capability even when
Lakebridge assessment succeeded. Verify
`databricks labs lakebridge transpile --help`, ask before installing a missing
transpiler component, and use Lakebridge conversion only if the installed
release now documents serverless support for the exact pilot constructs.

Do not install or upgrade Lakebridge automatically. If it is missing or does
not support Serverless SQL, record that fact and continue with governed
fallback; do not turn tool availability into a migration phase. Do not send
code to an LLM-backed component, execute generated SQL, or run Reconcile
without disclosing the action and obtaining the corresponding approval. Record
Lakebridge version, component, configuration without secrets, inputs, report
or artifact hashes, diagnostics, and coverage gaps.

### Option 2 — governed fallback

Use the procedures in this reference when Lakebridge is unavailable, unapproved, unsupported for the phase or construct, or returns failed, partial, or ambiguous results. Option 2 uses exported SQL projects/scripts, read-only catalog queries where needed, explicit object-by-object mappings, offline rewrites, and layered validation.

Fallback is not failure: retain Lakebridge evidence already produced, mark each item `fallback-required` with a reason, and continue without re-inventorying completed evidence. Never silently drop an object or substitute dedicated-pool rules.
Set Lakebridge Transpiler Status to `unsupported`, `not-installed`, `partial`,
or `failed` before routing to `fallback`; do not overwrite Lakebridge
Assessment Status.

Use the templates in `templates/` to produce an object inventory, mapping-gap report, migration plan, parity-test manifest, and validation report. Copy them to a migration-specific evidence directory and record their revisions and hashes.

## 1. Read-only discovery

Run the Lakebridge assessment path when it supports the scope. Otherwise use
exported SQL projects, source-controlled SQL, a serverless-compatible
SqlPackage extract, or read-only catalog queries without pausing for an access
or fallback decision. Record stable identifiers and definitions for:

- Databases and schemas.
- External data sources and their root URIs.
- Database-scoped credentials by name and authentication type; never extract secret values.
- External file formats and format options.
- Native external tables, columns, types, nullability, collation, location patterns, and partition conventions.
- Views, including nested dependencies and `OPENROWSET(BULK...)` calls.
- Stored procedures and inline table-valued functions.
- CETAS statements and the files or external tables they materialize.
- Statistics.
- Users, roles, grants, denies, and Microsoft Entra principals.
- TDS clients, BI models, applications, connection strings, query logs, concurrency, latency, and SLA requirements.
- ADLS Gen2 accounts, containers, paths, firewalls, private endpoints, DNS, managed identities, and service principals.
- Pipelines that read staging or transformation views and persist facts, dimensions, snapshots, or aggregates. Record activities, parameters, schedules, dependencies, retries, failure behavior, and runtime identities.
- Control metadata that selects persistence or aggregation behavior, including effective flags, execution ordering, generated SQL, watermarks, and restart semantics.
- Every persisted output's producer, input views, destination path/table, partitioning, refresh mode, writer ownership, serving views, and consumers.

Serverless SQL supports metadata objects such as schemas, views, procedures, functions, external resources, security objects, and external tables; it does not contain ordinary local tables. Preserve that distinction in inventory and reporting.

### SQL project, ZIP, and DACPAC intake

Treat packages as untrusted, immutable evidence:

1. Record filename, size, cryptographic checksum, received time, source revision, environment, and expected database.
2. Inspect ZIP entries before extraction; reject absolute paths, parent traversal, links, encrypted entries, or any entry escaping the staging directory.
3. Extract into a new read-only staging area, separate from reports and converted output.
4. Inventory SQL project includes/excludes, references, SQLCMD variables, pre/post-deployment scripts, publish profiles, target platform, and conditional items without executing them.
5. Inspect a DACPAC only with an approved DacFx-compatible tool after checking its version and help. Never publish during assessment.
6. Treat a successful project build as package consistency evidence, not Databricks compatibility or deployed-state parity.
7. Detect dedicated-pool constructs such as distributions, resource classes, columnstore indexes, workload groups, or DW service objectives and classify them as out of scope or requiring a scope decision.
8. Reconcile expected scope, artifact state, and deployed metadata.

## 2. Feature-wise compatibility assessment

For every object, classify the mapping as `direct`, `rewrite`, `redesign`, `retain`, or `blocker`. Include source evidence, dependencies, proposed target, semantic risks, validation method, and rollback boundary.
Update Lakebridge Assessment Status and Migration Inventory Status in the
workbook and manifest as part of this classification.

Assess at least these differences:

| Synapse serverless construct | Azure Databricks consideration |
|---|---|
| Database and schema | Choose an approved Unity Catalog `catalog.schema` mapping; do not silently collapse databases |
| Database-scoped credential | Replace with an approved Unity Catalog storage credential or other workload identity pattern; never migrate secret text |
| External data source | Map the root URI and identity to a Unity Catalog external location |
| External file format | Translate format and options into table `USING`/`OPTIONS` or `read_files` arguments |
| Native external table | Register an external Unity Catalog table over the existing path when no-copy access is approved |
| `OPENROWSET(BULK...)` | Prefer a named external table; use `read_files` only when ad-hoc file access is an intentional target contract |
| Wildcards and recursive paths | Revalidate glob semantics, partition discovery, schema inference, and file inclusion explicitly |
| View | Rewrite T-SQL to Databricks SQL and bind it to approved three-part names |
| CETAS | Decide whether the output remains an external table or becomes a managed Delta table; data materialization requires explicit approval |
| Stored procedure | Assess against current Databricks SQL scripting/procedure capabilities or redesign as a SQL task/notebook/workflow; never claim mechanical parity |
| Inline TVF | Assess current Databricks SQL function support and rewrite syntax and types |
| T-SQL type/collation behavior | Map types, precision, UTF-8/string comparison, case sensitivity, null behavior, date/time, and implicit conversions |
| TDS consumer | Validate the Databricks SQL Warehouse driver, authentication, catalog/schema defaults, parameters, and result behavior |
| Synapse grants/denies | Redesign as Unity Catalog ownership, privileges, groups, row filters, column masks, or workspace permissions |
| Statistics and performance hints | Do not copy metadata; establish a Databricks SQL performance baseline and target optimizations |
| Thin staging or serving view | Databricks SQL view over named Unity Catalog tables |
| Repeated expensive eligible query | Databricks SQL materialized view after refresh, ownership, feature, and cost approval |
| Declarative fact/dimension build | Lakeflow Declarative Pipeline producing target-owned managed Delta tables |
| Imperative or mixed-activity transformation pipeline | Databricks Job/Workflow, or retained external orchestration when activities do not map safely |
| Persisted Parquet fact/dimension output | Register existing files for no-copy coexistence, or create a managed Delta target when Databricks becomes the approved writer |
| Metadata-driven persistence/aggregation controls | Explicit pipeline configuration or generated deployment artifacts with deterministic source-to-target traceability |

Flag dynamic SQL, temp objects, metadata queries, cross-database names, T-SQL system functions, hints, transactions, error handling, security context, and unsupported file types for explicit review.

Merge Lakebridge reports into this assessment by stable source identity. For every finding, record whether Lakebridge discovered, analyzed, converted, warned, skipped, or failed the item. Option 2 owns the final classification and target mapping when tool output is missing or uncertain.

Preserve the Lakebridge Excel report as the human-readable assessment
deliverable. Add a `Migration Status` worksheet to an enriched copy of the
workbook and reconcile it to the full governed inventory. The worksheet must
show Lakebridge coverage and complexity beside the final classification,
target mapping, conversion route, lifecycle status, deployment and validation
evidence, blocker or review reason, owner, and next action. Append approved
scope items that Lakebridge did not report; never publish a status workbook
containing only the Analyzer subset or only the deployed wave.
It must include the separate Lakebridge Assessment Status, Lakebridge
Transpiler Status, and Migration Inventory Status columns.

Add a `Target Objects` worksheet from actual Databricks metadata, deployment
records, and validation results. Include every created external table, managed
Delta table, view, materialized view, function, and other in-scope catalog
object with catalog/schema/name/type, source mapping, deployment and validation
statement IDs, row count or contract metric, owner, and rollback boundary.

### Mapping-gap gate

Compare three sets independently: approved expected scope, supplied artifact state, and read-only deployed state. Normalize identities as `database.schema.object` while preserving original quoting and case. Classify discrepancies with these stable values:

| Gap | Meaning | Default |
|---|---|---|
| `EXPECTED_NOT_FOUND` | Approved item is absent from artifacts and deployed state | blocker |
| `ARTIFACT_ONLY` | Supplied definition was not observed deployed | warning |
| `DEPLOYED_ONLY` | Deployed item is absent from supplied artifacts | blocker |
| `DEFINITION_DRIFT` | Artifact and deployed definitions differ materially | blocker |
| `UNMAPPED_OBJECT` | In-scope item lacks a target or disposition | blocker |
| `UNMAPPED_DEPENDENCY` | Dependency lacks a mapping or approved external contract | blocker |
| `TARGET_COLLISION` | Multiple sources map to one target without an approved merge | blocker |
| `UNSUPPORTED_TYPE` | Construct has no executable target pattern | blocker |
| `UNMAPPED_STORAGE` | Path/format lacks a data action or governed target | blocker |
| `UNMAPPED_IDENTITY` | Runtime or consumer identity lacks an access mapping | blocker |
| `UNMAPPED_CONSUMER` | Consumer lacks a target endpoint or disposition | blocker |
| `GENERATED_DEFINITION` | Generated object lacks its deterministic source | blocker |
| `OUT_OF_SCOPE_DIALECT` | Dedicated-pool or excluded dialect was detected | blocker |
| `NOT_VERIFIED` | Required evidence or access was unavailable | warning |

Always create a mapping-gap report, including a positive no-gap report. Conversion starts only when no unresolved blockers remain or each exception has an approved disposition, owner, evidence, and expiry.
Do not use the mapping-gap report to launch platform provisioning or permission
remediation. Record such a gap against the affected objects and continue other
work.

## 3. Target mapping proposal

Present choices rather than assuming a topology.

### Namespace

For each source database, propose one of:

- One Unity Catalog catalog per database, preserving source schemas.
- Several source databases consolidated into one catalog with collision-free schemas.
- A domain-oriented catalog redesign with a complete source-to-target mapping.

Require approval for catalog/schema names, ownership, managed-storage roots, grants, and cross-catalog dependencies.

### Storage and table strategy

For existing ADLS Gen2 files, default to **no data copy** during initial migration:

1. Establish least-privilege Azure identity.
2. Create or select a Unity Catalog storage credential.
3. Create the narrowest external location that covers approved paths.
4. Register external tables using stable, non-overlapping paths.
5. During the technical pilot, grant the named migration operator only the
   temporary access required for the approved non-production scope. After
   schema validation, map and grant access to approved groups rather than
   copying source role names or granting end users individually.

Use managed tables for new target-owned data and for later modernization when the user approves data conversion or copying. Never register the same path in conflicting tables, volumes, or external locations.

### Query surface

Use a Databricks SQL Warehouse for TDS/BI query workloads. Select serverless or classic/pro warehouse only after confirming regional availability, networking, identity, policy, feature, concurrency, startup, and cost constraints.

### Post-staging transformation strategy

Treat source ingestion and post-staging materialization as separate ownership boundaries. Retaining ADF, Power Automate, or Synapse ingestion does not imply retaining the pipeline that builds facts and dimensions from landed files.

In every target-mapping response, state the boundary explicitly: **retain the
upstream source ingestion out of scope** unless separately approved, while the
in-scope post-staging producer may use a **Databricks SQL materialized view**,
**Lakeflow Declarative Pipeline**, or **Databricks Job** and write target-owned
**managed Delta** outputs. Do not leave this ownership and retention decision
implicit.

Choose one target per produced dataset:

| Workload shape | Preferred target | Required evidence |
|---|---|---|
| Thin projection, rename, cast, or semantic serving layer | Databricks SQL view | Output schema and consumer-query parity |
| Repeated deterministic query eligible for managed refresh | Databricks SQL materialized view | Current feature eligibility, refresh SLA, incremental behavior, cost, and owner |
| Declarative multi-table fact/dimension flow with durable state or data-quality rules | Lakeflow Declarative Pipeline | Input/output contract, keys, sequencing, expectations, state, and restart behavior |
| Imperative steps, external calls, unsupported SQL, or mixed activities | Databricks Job/Workflow or retained orchestrator | Activity mapping, parameters, retries, dependencies, and failure semantics |

Do not select a materialized view only because a source object is persisted. Do not select Lakeflow only because a pipeline exists. Base the mapping on observable state, orchestration, quality, refresh, and recovery requirements.

### Deployment unit

Prefer a small, ownership-aligned Declarative Automation Bundle (formerly Databricks Asset Bundle) for deployable SQL files, jobs, and supported resources. Track Unity Catalog resources that the bundle references but does not own. Validate the bundle before deployment.

## 4. Conversion and packaging approval

The target design may proceed without repeatedly confirming assumed access.
Before target mutation, data movement, costly compute, or cutover, require
explicit approval for the affected decisions:

- Source database to Unity Catalog catalog/schema mapping.
- External versus managed table decisions.
- Storage credentials, external locations, identities, networking, and grants.
- SQL Warehouse type, size, scaling, auto-stop, ownership, and budget limits.
- Object-by-object conversion disposition.
- Any CETAS replacement or other operation that writes/copies data.
- Each post-staging pipeline disposition, target writer, managed Delta output, refresh schedule, watermark policy, and coexistence or cutover boundary.
- Consumer connection and cutover sequence.
- Validation fixtures, tolerances, performance targets, rollback, and decommission boundary.

Stop conversion only when path ownership, target naming, writer ownership, or
consumer requirements needed for the selected object are unknown.

### Migration manifest

Create a manifest with:

- Source workspace/serverless endpoint, database, schema, object type, name, definition hash, and dependency list.
- Source storage root and relative path without credentials.
- Pipeline identity, control-record dependency, schedule, refresh mode, watermark, retry/restart behavior, source inputs, produced datasets, serving views, and consumers.
- Approved target workspace, catalog, schema, object, external location, Warehouse, and deployment unit.
- Classification, rationale, conversion status, generated artifact hash, and reviewer approval.
- Data-movement disposition: `none`, `register-existing`, or explicitly approved `copy/convert`.
- Validation checks, evidence, status, rollback action, and consumer cutover status.
- Tool route (`lakebridge` or `fallback`), Lakebridge version/component when used, configuration hash, input/output hashes, diagnostics, unsupported constructs, and fallback reason.

Use statuses `inventoried`, `assessed`, `fallback-required`, `blocked`, `approved`, `converted`, `deployed`, `validated`, `retained`, `failed`, and `rolled-back`. Update atomically after every phase.

### Offline conversion rules

Before conversion, check the installed Lakebridge transpiler capability matrix and run a small representative pilot only if serverless SQL is explicitly supported. If it is not, route serverless objects directly to the rules below. Do not disguise serverless input as dedicated Synapse or generic MSSQL merely to make a transpiler accept it.

### External data sources and credentials

Do not translate credentials as literals. Emit a target requirement for an approved storage credential, then map each source root to an external location. Preserve path boundaries and identify overlapping roots.

### External tables

Translate the effective source URI, file format, schema, and options. Prefer explicit schemas for stable production contracts. Verify column mapping, partition columns, glob expansion, malformed-record behavior, headers, delimiters, quoting, encoding, compression, and recursive discovery.

A typical approved no-copy target pattern is:

```sql
CREATE TABLE target_catalog.target_schema.orders
USING PARQUET
LOCATION 'abfss://container@account.dfs.core.windows.net/curated/orders';
```

The location must already be covered by an approved Unity Catalog external location. Do not embed storage keys or SAS tokens.

### `OPENROWSET`

Convert repeated `OPENROWSET` access into a named external table when possible. For intentionally ad-hoc access, Databricks SQL can use `read_files`, for example:

```sql
SELECT *
FROM read_files(
  'abfss://container@account.dfs.core.windows.net/landing/orders/*.parquet',
  format => 'parquet'
);
```

Do not rely on inferred schema for a stable production interface without approval. Re-test Synapse wildcard and recursive-path behavior against the exact target files.

### Managed-Bronze schema contracts

When an approved target design materializes source files into managed Delta tables:

1. Extract the required downstream column names, types, comparison literals, joins, and null behavior before generating CTAS or ingestion SQL.
2. Declare explicit schemas or `schemaHints` for business-significant columns; do not allow sampled-file inference to define a production contract.
3. Treat `_rescued_data`, malformed records, and unexpected null inflation as schema failures that block downstream promotion.
4. Use bounded, aggregate-only diagnostics to prove whether required values are recoverable. Do not retain raw sensitive rows.
5. Do not create a replacement table until the required business values and target type contract are proven.
6. Remediate the smallest affected dependency chain, then resume validation from an immutable remaining-only manifest.

### Views and functions

Rewrite bracket quoting, `dbo` assumptions, two-part names, T-SQL functions, type conversions, collations, `TOP`, date expressions, JSON handling, metadata references, hints, and error behavior. Use fully qualified `catalog.schema.object` names for deployable definitions. Preserve output column names, order, types, nullability expectations, and duplicate behavior.

Validate executable dependencies from parsed SQL rather than comments or object-name conventions. For generated `PIVOT` rewrites, verify literal values, aliases, output names, and downstream references. Reconcile every normalized target name with every executable reference before deployment.

### CETAS

Separate the two effects:

1. Materializing query results to files.
2. Registering external-table metadata.

A no-copy migration may register existing CETAS output files without rerunning the source query. Re-executing or replacing CETAS with CTAS writes data and requires explicit approval, destination ownership, idempotency, overwrite, recovery, and cost decisions.

### Procedures and orchestration

Inventory parameters, defaults, result sets, dynamic SQL, temp state, transactions, error handling, and side effects. Use current Databricks SQL procedure/scripting support only after feature verification. Otherwise redesign into SQL files, notebooks, or Lakeflow Jobs tasks with explicit parameters and failure behavior. Keep unsupported procedures as blockers or retained source components.

### Fact/dimension pipelines and persisted outputs

Convert the pipeline as a producer contract, not as a loose collection of SQL views:

1. Freeze the source inputs, control rows, output schemas, keys, partitions, refresh mode, schedule, and downstream serving dependencies.
2. Separate retained source ingestion from the in-scope post-staging transformation boundary.
3. Translate staging and reusable semantic logic into deterministic Databricks SQL views where appropriate.
4. Implement declarative stateful fact/dimension production in a Lakeflow Declarative Pipeline; use a Databricks Job/Workflow for imperative or mixed-activity steps.
5. Write target-owned durable outputs as managed Delta tables unless an approved coexistence phase only registers existing Parquet files.
6. Preserve control-driven selection and aggregation through explicit pipeline configuration or generated versioned artifacts. Do not depend on untracked runtime SQL generation.
7. Make writes idempotent and define merge keys, late-arriving-data behavior, watermark advancement, backfill, replay, schema evolution, failure recovery, and duplicate handling.
8. Recreate serving views over the approved target facts and dimensions, then validate consumers before cutover.

## 5. Deployment

- Validate SQL and bundle configuration offline first.
- Deploy to a non-production catalog and Warehouse.
- Confirm target names and locations are unoccupied or explicitly managed.
- Apply bounded retries and polling.
- Record deployed IDs, definitions, hashes, grants, and external locations.
- Never run converted procedures, CETAS replacements, or broad validation queries automatically.

## 6. Validation

Validate in layers:

1. **Structural:** every source object has a manifest disposition and dependency resolution.
2. **SQL:** definitions parse and bind to intended three-part names.
3. **Storage:** approved identities can access only approved paths.
4. **Schema:** column names, order, mapped types, and partition columns match the contract.
5. **Behavioral:** approved fixtures compare row sets, duplicates, nulls, Unicode, dates, decimals, and edge cases.
6. **Technical acceptance:** schema and behavior pass before security migration begins.
7. **Security migration:** source groups, users, identities, ownership, grants, denies, row filters, and column masks are inventoried and explicitly mapped.
8. **Security validation:** approved personas can access intended objects and are denied outside their scope.
9. **Consumer:** JDBC/ODBC/BI clients authenticate and preserve parameter and result behavior.
10. **Performance:** representative scan volume, file pruning, concurrency, latency, startup, and cost meet agreed targets.
11. **Operations:** monitoring, query history, alerts, ownership, retry, and support procedures work.
12. **Pipeline:** retained-ingestion handoff, schedule, control selection, idempotent replay, watermark advancement, retries, restart from partial failure, and writer ownership work.
13. **Persisted outputs:** fact grain, dimension keys, referential integrity, aggregates, duplicate behavior, late-arriving records, partitions, and serving-view results meet the approved contract.

Use bounded `SELECT ... LIMIT 0` semantic checks where parsing or `EXPLAIN` does not force expression analysis. Validate Boolean, numeric, and string comparison semantics explicitly. Do not use row counts alone as semantic proof. Do not query sensitive production data without explicit approval.

After a failed validation gate, persist the failure and pause state, cancel unneeded diagnostics, stop temporary compute, and prevent later phases from starting. Resume only the failed and not-yet-validated objects from a verified immutable package; never silently rerun already accepted objects.

If Lakebridge Reconcile is supported and approved for the exact serverless scenario, it may produce part of the schema, row, or data comparison evidence. It does not replace structural, SQL binding, security, consumer, performance, or operational validation, and discrepancies must stop cutover until dispositioned.

## Cutover and rollback

Cut over consumers in controlled waves. Freeze conflicting definition changes, deploy approved hashes, validate target health, update one consumer cohort, monitor, and continue only after acceptance.

Rollback must preserve the source endpoint and definitions, restore previous client connection settings, disable target schedules or writes, retain evidence, and avoid deleting shared external data. Decommissioning Synapse is a separate approved phase after the rollback window.

## Failure report

When blocked or failed, report:

- Phase and object.
- Evidence and compatibility classification.
- Whether any target mutation or data write occurred.
- Partial-success counts by status.
- Cleanup or rollback performed.
- Required decision or prerequisite.
- Safe next action.

Never include credential values, tokens, connection-string secrets, or sampled sensitive rows.

## Must

- Preserve the metadata-over-external-files model and distinguish it from Dedicated SQL Pool storage.
- Reconcile every source object to an explicit migration disposition and dependency order.
- Approve storage access, any no-copy registration design, target writes, and cutover separately.
- Validate Serverless SQL behavior and downstream persisted outputs beyond syntax.

## Prefer

- Lakebridge Profiler or Analyzer for supported assessment scope before governed fallback.
- Named Unity Catalog tables and views over repeated raw `read_files` access.
- Managed Delta for target-owned persisted outputs.
- Remaining-only resume from an immutable manifest after failure.

## Avoid

- Do not use a dedicated-pool transpiler against an entire Serverless SQL estate.
- Do not translate `OPENROWSET`, CETAS, credentials, procedures, or grants by textual substitution.
- Do not infer schema when downstream SQL requires a stronger contract.
- Do not claim parity from parsing, deployment, row counts, or `EXPLAIN` alone.

## Examples

- "Migrate Serverless SQL `OPENROWSET` views without copying existing ADLS data."
- "Retain upstream ingestion but migrate the post-staging fact and dimension producer."

## Official references

- [Serverless SQL pool overview](https://learn.microsoft.com/azure/synapse-analytics/sql/on-demand-workspace-overview)
- [Synapse serverless SQL feature matrix](https://learn.microsoft.com/azure/synapse-analytics/sql/overview-features)
- [Query storage files with serverless SQL](https://learn.microsoft.com/azure/synapse-analytics/sql/query-data-storage)
- [Synapse external tables](https://learn.microsoft.com/azure/synapse-analytics/sql/develop-tables-external-tables)
- [Synapse `OPENROWSET`](https://learn.microsoft.com/azure/synapse-analytics/sql/develop-openrowset)
- [Synapse CETAS](https://learn.microsoft.com/azure/synapse-analytics/sql/develop-tables-cetas)
- [SqlPackage support for Synapse serverless SQL pools](https://learn.microsoft.com/sql/tools/sqlpackage/sqlpackage-for-azure-synapse-analytics)
- [Unity Catalog best practices](https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/best-practices)
- [Create an external location for ADLS Gen2](https://learn.microsoft.com/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-adls)
- [Databricks SQL `read_files`](https://learn.microsoft.com/azure/databricks/sql/language-manual/functions/read_files)
- [Declarative Automation Bundles](https://learn.microsoft.com/azure/databricks/dev-tools/bundles/)
- [Databricks Labs Lakebridge overview](https://databrickslabs.github.io/lakebridge/docs/overview/)
- [Lakebridge Synapse Profiler](https://databrickslabs.github.io/lakebridge/docs/assessment/profiler/synapse)
- [Lakebridge Analyzer](https://databrickslabs.github.io/lakebridge/docs/assessment/analyzer/)
- [Lakebridge supported transpilation dialects](https://databrickslabs.github.io/lakebridge/docs/transpile/)
