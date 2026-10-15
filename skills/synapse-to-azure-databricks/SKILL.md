---
name: synapse-to-azure-databricks
description: "Assess and migrate Azure Synapse Analytics workloads to Azure Databricks through phased discovery, inventory, assessment, conversion, deployment, and validation. Routes Serverless SQL, Dedicated SQL Pool, Synapse Spark, pipelines, and staged Bronze modernisation to scenario-specific guidance. Use for 'Synapse to Azure Databricks', 'Synapse Serverless SQL to ADB', 'Dedicated SQL Pool to Databricks', 'Synapse Spark migration', 'OSA migration', 'external Bronze registration', 'UC Upgrade', 'Unity Catalog external-to-managed upgrade', 'ADF ingestion migration', 'staged Bronze modernisation', or mixed Synapse estate planning."
---

# Azure Synapse Analytics to Azure Databricks

Use this skill as the common entry point for every Synapse-to-Databricks
migration. Assume the operator already has working access to Synapse and Azure
Databricks and that Unity Catalog is provisioned. Start with migration
discovery, not access-readiness narration. Load only the workload reference
required for the current request.

## Workload routing

| Source workload | Required reference or companion skill | Do not mix with |
|---|---|---|
| Serverless SQL pool, SQL on-demand, `OPENROWSET`, native external tables, CETAS | [synapse-serverless-sql.md](references/synapse-serverless-sql.md) | Dedicated-pool storage and distribution assumptions |
| Dedicated SQL pool, distributions, columnstore, resource classes, workload groups | [synapse-dedicated-sql-pool.md](references/synapse-dedicated-sql-pool.md) | Serverless metadata-over-files assumptions |
| Spark pools, notebooks, Spark Job Definitions, packages, `mssparkutils` | [synapse-spark.md](references/synapse-spark.md) | SQL-only conversion rules |
| ADF or Synapse pipelines and triggers | `pipelines-to-azure-databricks-workflows` | Automatic one-for-one Workflow conversion |
| OSA, staged Bronze modernisation, external Bronze registration, UC Upgrade, external-to-managed upgrade, or staged ADF ingestion replacement | [staged-bronze-migration.md](references/staged-bronze-migration.md) | A single-step migration, implicit writer transfer, or automatic source cleanup |

For mixed estates, create one shared inventory and migration manifest, classify every artifact by workload, and run the references as coordinated tracks. Preserve dependency edges across tracks without loading unrelated workload detail into each conversion task.

Use these common phase references when needed:

| Common phase | Reference |
|---|---|
| Assessment evidence and compatibility | [assessment.md](references/assessment.md) |
| Target mapping and approval | [target-mapping.md](references/target-mapping.md) |
| Common conversion controls | [conversion.md](references/conversion.md) |
| Deployment, validation, cutover, and rollback | [deployment-validation.md](references/deployment-validation.md) |

Human-facing documentation and editable Draw.io diagrams live in
[docs/](docs/README.md). Keep future skill architecture, prerequisites, and
migration-approach diagrams there; keep runtime instructions in `references/`.

## Assumed platform baseline

Assume Synapse access, Azure Databricks access, a target workspace, and
provisioned Unity Catalog already exist. Do not branch into Azure Arc,
workspace or metastore provisioning, identity onboarding, role assignment,
private-endpoint setup, customer-VDI setup, or general platform-readiness
troubleshooting.

If an actual migration command fails because of a permission or platform
configuration issue:

1. Record the exact failed operation and affected objects in the inventory.
2. Mark only the affected objects `blocked`.
3. State the minimum external remediation needed without performing platform
   setup.
4. Continue independent inventory, assessment, conversion, or validation work.

Do not turn a scoped migration blocker into a new readiness phase.

## Phase communication contract

Make migration progress visible to the user. Before doing work in each phase,
announce:

- `Phase <number> - <name>`.
- Whether the phase is `starting`, `in progress`, `blocked`, `complete`, or
  `paused`.
- What will be done in the phase.
- The evidence or exit criteria that completes the phase.
- The next phase and any operational approval required.

Announce a phase transition before its first tool call or migration action.
When work stops, fails, or is interrupted, state the phase and checkpoint that
was reached. Do not report a phase as complete when required evidence is
missing; use `blocked` or `not run` and name the missing migration evidence.

## Tool-routing contract

Use Databricks Labs Lakebridge where the installed release explicitly supports
the source workload, phase, and exact constructs. Detect it once when the first
assessment or conversion step needs it. If it is unavailable or unsupported,
record the reason and continue with governed fallback; absence of Lakebridge
does not create a separate phase or block inventory.

Do not install or upgrade Lakebridge automatically. Ask only when installation
is necessary for the selected route. Treat a transpiler and any LLM-backed
component as separate, disclosed choices. Record tool versions, configuration
without secrets, input/output hashes, diagnostics, warnings, and exclusions.
Treat generated output as a conversion candidate, never parity proof.

For every inventory item, maintain these three independent status fields:

- **Lakebridge Assessment Status** — `not-run`, `supported`, `completed`,
  `partial`, `failed`, `unsupported`, or `fallback`.
- **Lakebridge Transpiler Status** — `not-evaluated`, `available`, `piloted`,
  `used`, `partial`, `failed`, `unsupported`, `not-installed`, or `fallback`.
- **Migration Inventory Status** — `inventoried`, `reconciled`, `drifted`, or
  `blocked`.

Assessment success never implies transpiler support. A missing or unsupported
transpiler routes the object to governed fallback and must not erase completed
assessment evidence.

Governed fallback uses immutable exports or read-only discovery, explicit
mappings, offline rewrites, dependency-ordered deployment, and layered
validation. Route failed, partial, ambiguous, or unsupported Lakebridge results
to fallback without discarding completed evidence.

Workload references contain only workload-specific Lakebridge capability boundaries. This section remains authoritative for common Lakebridge governance.

## Staged Bronze modernisation scenario

When the request matches the staged Bronze route, first complete the CAF
Phase 1 inventory and create the required workbook and companion JSON manifest.
Then apply
[staged-bronze-migration.md](references/staged-bronze-migration.md) as a
four-stage scenario inside the common migration workflow:

1. register existing Bronze files as read-only Unity Catalog external tables;
2. migrate transformation views and persisted Silver/Gold production;
3. upgrade approved external Bronze objects to managed Delta;
4. replace approved ADF ingestion with a Databricks ingestion framework, using
   the companion pipeline skill for pipeline inventory and orchestration
   conversion.

The scenario stages do not replace, renumber, merge, or weaken the common CAF
phases. Announce the current common phase and scenario stage together. Before
starting scenario stage `N`, require stage `N-1` validation to be `PASS`, its
exit criteria to be complete, and its progression approval to be recorded.
Keep these approvals separate: target design and conversion; deployment or
metadata mutation; data movement; writer-ownership transfer; production
cutover and schedule activation; and source retirement or file cleanup.

Extend every applicable inventory and manifest item with the scenario profile,
scenario stage, stage-gate status, writer ownership, original location,
managed target, data action, rollback boundary, retention decision, and cleanup
decision. Continue to maintain the CAF Lakebridge Assessment Status,
Lakebridge Transpiler Status, Migration Inventory Status, lifecycle status,
evidence, and approvals. Use
[staged-bronze-validation-cutover.md](references/staged-bronze-validation-cutover.md)
at every stage gate.

## Common migration workflow

Execute these phases in order and apply the phase communication contract at
every transition.

### 1. Discover, inventory, and route

- Treat Synapse as read-only by default.
- Use stable source identifiers and content hashes.
- Inventory workspaces, workload artifacts, identities, storage, networking, consumers, orchestration, schedules, data contracts, SLAs, and costs.
- Extract executable dependency edges; do not infer dependencies from names or comments.
- Classify each item as `direct`, `rewrite`, `redesign`, `retain`, or `blocker`.
- Route each item to exactly one workload reference and record cross-track dependencies.
- Create a populated `reports/synapse-to-databricks-migration-inventory.xlsx`
  and companion
  `reports/synapse-to-databricks-migration-inventory.manifest.json` during this
  phase. Do not defer inventory creation until conversion or deployment and do
  not treat a narrative summary, the blank CSV template, or a manifest alone as
  the inventory deliverable.
- Populate `templates/object-inventory.csv` with every discovered approved-scope
  object and its definition hash, then run:

  ```powershell
  python skills\synapse-to-azure-databricks\scripts\create_migration_inventory.py `
    --inventory-csv <populated-object-inventory.csv> `
    --output reports\synapse-to-databricks-migration-inventory.xlsx `
    --manifest reports\synapse-to-databricks-migration-inventory.manifest.json
  ```

  When Lakebridge produced an Excel report, preserve and enrich that report by
  also passing `--lakebridge-workbook <lakebridge-report.xlsx>`.
- Verify that the workbook opens and contains a populated `Migration Status`
  worksheet plus `Target Objects`, `Dependencies`, `Summary`, `Decisions and
  Approvals`, `Evidence`, and `Metadata and Lists`. Populate `Dependencies`
  when source edges exist and populate `Target Objects` only from approved
  target mappings and actual deployment evidence. Verify that the JSON manifest
  item count and stable source identities reconcile exactly to
  `Migration Status`.
- Initialize and report Lakebridge Assessment Status, Lakebridge Transpiler
  Status, and Migration Inventory Status for every item. These columns are
  mandatory even when their initial value is `not-run` or `not-evaluated`.
- Phase 1 is incomplete or `blocked` until these two artifacts exist and cover
  the full approved source scope. If no source artifacts are available, report
  the missing input instead of creating an empty success-shaped workbook.

### 2. Assess and classify

- Use Lakebridge assessment when supported; otherwise continue with governed
  analysis without creating a prerequisite detour.
- Tell the user: "Lakebridge assessment and conversion are separate gates;
  assessment support does not imply conversion support."
- Report which Lakebridge component ran, its coverage, warnings, exclusions,
  and whether fallback is required before doing fallback analysis.
- Update Lakebridge Assessment Status per object and reconcile Migration
  Inventory Status after merging Lakebridge and governed-analysis findings.
- Keep Lakebridge output and governed-fallback output distinguishable in the
  evidence set.

### 3. Design the target and resolve mapping gaps

- Select Databricks targets from behavior, state, ownership, recovery, and consumer requirements rather than source names.
- Map into the provisioned Unity Catalog, including catalogs, schemas, storage
  locations, ownership, monitoring, cost controls, and retained systems.
- Default to no data movement. Any copy, conversion in place, recurring ingestion, or destructive target change requires explicit approval.

### 4. Convert and package

- Apply only the selected workload reference.
- Keep source evidence immutable and generated artifacts separate.
- Check Lakebridge conversion support independently from assessment support.
- If the required transpiler component is not installed, stop and ask before
  running `databricks labs lakebridge install-transpile`. Obtain separate
  approval for an LLM-backed transpiler.
- Run an approved representative conversion pilot, preserve diagnostics and
  unsupported nodes, and obtain approval before expanding conversion scope.
- Record the conversion route per artifact as Lakebridge-generated,
  governed-fallback, retained, or blocked.
- Update Lakebridge Transpiler Status per object after the capability check,
  pilot, conversion attempt, or fallback decision.
- Validate converted artifacts offline and preserve unsupported items as
  blockers or approved retained components.

### 5. Deploy to non-production

- Deploy dependency-ordered, remaining-only packages to non-production first.
- Stop on drift, target collisions, semantic failures, schema-contract failures, or unapproved privilege requirements.

### 6. Validate

- Validate static structure, runtime behavior, data contracts, security,
  consumers, performance, recovery, and cost.
- Update the inventory and manifest with every result and failure.
- Reconcile Migration Inventory Status to `reconciled`, `drifted`, or `blocked`
  from actual Databricks objects and validation evidence.

### 7. Cut over and close

- Cut over only after acceptance passes and rollback remains available.

## Continuous inventory and evidence

Maintain the Phase 1 workbook and JSON manifest through all phases. Track
`inventoried`, `assessed`, `fallback-required`, `approved`, `converted`,
`packaged`, `deployed`, `validated`, `failed`, `retained`, `blocked`,
`cut-over`, and `rolled-back`. Preserve hashes, mappings, dependencies,
decisions, attempts, evidence, rollback actions, and pause/resume state.

When Lakebridge emits an Excel report, preserve it and enrich it with the
full-scope `Migration Status` and evidence-backed `Target Objects` worksheets.
Never replace the authoritative inventory or limit it to Lakebridge-reported or
currently deployed objects.

## Must

- Route Serverless SQL, Dedicated SQL Pool, Spark, and pipelines to separate guidance.
- Route staged Bronze modernisation through its ordered four-stage profile
  while retaining every common CAF phase, inventory, status, evidence, and
  approval control.
- Announce every phase, its work, exit criteria, and next gate before acting.
- Assume working Synapse and Databricks access and provisioned Unity Catalog;
  begin with migration discovery rather than access-readiness checks.
- Do not perform or troubleshoot Azure Arc, workspace/metastore provisioning,
  identity onboarding, role assignment, networking setup, or customer-device
  setup as part of this skill.
- Isolate permission failures to affected inventory objects and continue
  independent migration work.
- Use governed fallback without blocking the migration when Lakebridge is
  absent or unsupported; ask only before installing or upgrading tooling.
- Gate Lakebridge assessment and conversion independently; never infer
  conversion support from successful profiling or analysis.
- Keep Lakebridge Assessment Status, Lakebridge Transpiler Status, and
  Migration Inventory Status explicit and current for every object.
- Keep Lakebridge governance, inventory, approvals, evidence, and lifecycle state common.
- Require explicit approval before target mutation, costly compute, data movement, or cutover.
- Preserve source-to-target traceability and cross-workload dependencies.
- Create the populated Excel migration inventory and companion JSON manifest in
  Phase 1, verify full-scope reconciliation, and block later phases when either
  artifact is absent or empty.
- Preserve the Lakebridge workbook as assessment evidence and enrich it with a
  full-scope `Migration Status` worksheet and evidence-backed `Target Objects`
  worksheet; do not replace it with a manifest-only inventory.
- Use Unity Catalog governance and least-privilege workload identities.
- Persist failures and pauses; do not advance later phases after a failed gate.
- Keep target schedules paused until go-live approval; do not transfer writer
  ownership, allow unapproved dual writes, retire ADF/Synapse, or clean up
  source files implicitly.

## Prefer

- Export-first or approved read-only discovery.
- Small representative Lakebridge pilots before broader conversion.
- Databricks Asset Bundles for repeatable deployment.
- Incremental waves with explicit rollback boundaries.
- Existing-file registration over data copying when the approved workload permits it.
- Managed Delta for target-owned Bronze, Silver, and Gold after format,
  product-version, data-movement, ownership, and rollback checks pass.

## Avoid

- Do not apply dedicated SQL assumptions to Serverless SQL or SQL-only rules to Spark.
- Do not claim Lakebridge support based on a different Synapse workload.
- Do not silently skip Lakebridge, silently install it, or silently select
  governed fallback.
- Do not force every Synapse pipeline into Databricks Workflows.
- Do not copy data, provision compute, mutate the source, or cut over implicitly.
- Do not claim parity from parsing, transpilation, deployment success, or `EXPLAIN` alone.
- Do not use `SET MANAGED` for Parquet or an ineligible object, add `MOVE` or
  `COPY` to a Unity Catalog external-table conversion, disable the current
  writer before the target writer is approved, or delete original files
  automatically.

## Examples

- "Assess this mixed Synapse estate and route Serverless SQL, Dedicated SQL Pool, Spark, and pipelines to separate migration tracks."
- "Migrate Synapse Serverless SQL `OPENROWSET` views to Databricks without copying ADLS data."
- "Plan a Dedicated SQL Pool migration to Unity Catalog managed Delta tables and Databricks SQL."
- "Convert Synapse Spark notebooks and jobs to Databricks Asset Bundles."
- "Inventory this Synapse estate and begin the phased migration to the
  provisioned Unity Catalog."
- "Apply the staged Bronze modernisation scenario: register existing Bronze
  read-only, migrate transformations, upgrade approved tables to managed
  Delta, and then assess ADF ingestion replacement."
