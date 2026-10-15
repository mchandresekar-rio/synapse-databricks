# Staged Bronze modernisation scenario

Use this scenario for OSA migration, staged Bronze modernisation, Synapse
external-table registration, UC Upgrade, Unity Catalog external-to-managed
upgrade, or staged ADF ingestion replacement.

This scenario extends the common CAF workflow. It never replaces its phase
announcements, required Phase 1 Excel workbook and JSON manifest, three
independent Lakebridge and inventory status fields, compatibility
classification, governed fallback, target approvals, evidence, or validation.

## Ordered scenario stages

| Stage | Objective | Required reference |
|---|---|---|
| 1 | Register existing Synapse Bronze as read-only Unity Catalog external tables | [staged-bronze-external-registration.md](staged-bronze-external-registration.md) |
| 2 | Migrate transformations and persisted Silver/Gold production | [staged-bronze-transformation-migration.md](staged-bronze-transformation-migration.md) |
| 3 | Upgrade selected external Bronze to managed Delta | [staged-bronze-managed-upgrade.md](staged-bronze-managed-upgrade.md) |
| 4 | Replace approved ADF ingestion with a Databricks ingestion framework | [staged-bronze-adf-ingestion-migration.md](staged-bronze-adf-ingestion-migration.md) |

Run [staged-bronze-validation-cutover.md](staged-bronze-validation-cutover.md)
at every gate. Do not merge stages. Stage `N` is blocked until stage `N-1` is `PASS`,
its exit criteria are complete, and progression approval is recorded.

## CAF control overlay

- Complete common Phase 1 before executing any scenario stage.
- Announce both the common CAF phase and scenario stage before acting.
- Maintain Lakebridge Assessment Status, Lakebridge Transpiler Status, and
  Migration Inventory Status independently for every applicable item.
- Apply the common Lakebridge capability gate per stage and object; generated
  output is never parity evidence.
- Preserve the source, ADF definitions, and existing ADLS files as read-only
  until the applicable cutover is approved.
- Separate approval for design/conversion, deployment or metadata mutation,
  data movement, writer-ownership transfer, production cutover/schedule
  activation, and source retirement or file cleanup.
- Keep Databricks schedules paused until go-live approval.
- Never permit unapproved ADF and Databricks dual writes to one production
  Bronze target.
- Preserve source files through the rollback and retention periods.

## Inventory and manifest extension

For every applicable object, path, pipeline, or activity, populate:

| Field | Value |
|---|---|
| `scenario_profile` | `staged-bronze-modernisation` |
| `scenario_stage` | `1`, `2`, `3`, or `4` |
| `stage_gate_status` | `not-started`, `blocked`, `validation-pending`, `approval-pending`, or `passed` |
| `writer_ownership` | `synapse-owned`, `adf-owned`, `cutover-pending`, or `databricks-owned` |
| `original_location` | Credential-free source URI or `not-applicable` |
| `managed_target` | Three-part target or `not-applicable` |
| `data_action` | `register-existing`, `convert`, `copy`, `ingest`, `write-managed`, or `none` |
| `rollback_boundary` | Exact reversible boundary and expiry |
| `retention_decision` | Approver, evidence, period, or `pending` |
| `cleanup_decision` | Approved action, `retain`, or `pending` |

Continue to populate all common CAF fields, including stable IDs, hashes,
dependencies, classification, disposition, tool route, three independent
status fields, lifecycle status, generated-artifact hashes, validation
evidence, approvals, failures, and pause/resume state.

## Required deliverables

Create and cross-link the CAF workbook and manifest with the object/pipeline
inventory, lineage graph, source-to-target mapping, external Bronze contract,
Unity Catalog DDL and storage mapping, transformation artifacts, managed
upgrade scripts, ADF activity mapping, ingestion framework, Asset Bundle and
paused Job definitions, exceptions, reconciliation results, validation
reports, cutover/rollback plans, and deferred backlog.

## Completion

Complete only when all four stages pass, Databricks is the approved Bronze
writer, schedule activation is approved, consumers use approved
Bronze/Silver/Gold contracts, rollback remains available for the approved
period, and retained or deferred items have owners. ADF disablement is not
decommissioning.
