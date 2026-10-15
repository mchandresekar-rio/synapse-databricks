# Migration approach

## Common flow

The skill announces each phase before acting. Every announcement states the
phase status, current work, completion evidence, and next approval gate.

The flow assumes working Synapse and Databricks access, an existing workspace,
and provisioned Unity Catalog. Azure Arc, platform provisioning, identity
onboarding, role assignment, networking setup, and device setup are outside the
migration flow.

### Phase 1 - Discover, inventory, and route

1. Establish source scope and authoritative evidence.
2. Inventory artifacts with stable IDs, hashes, and executable dependencies.
3. Create the migration workbook and JSON manifest.
4. Initialize Lakebridge Assessment Status, Lakebridge Transpiler Status, and
   Migration Inventory Status for every object.
5. Load the applicable Serverless SQL, Dedicated SQL Pool, Spark, or pipeline
   guidance.

### Phase 2 - Assess and classify

1. Run Lakebridge assessment for supported scope.
2. Use governed fallback without pausing when Lakebridge is absent,
   unsupported, partial, or failed.
3. Classify direct, rewrite, redesign, retain, and blocker dispositions.
4. Update Lakebridge Assessment Status and reconcile Migration Inventory
   Status without changing Lakebridge Transpiler Status.

### Phase 3 - Design the target and resolve mapping gaps

Map into the provisioned Unity Catalog. Define namespace, storage, compute,
consumer, data-movement, and validation mappings. Resolve or disposition every
migration blocker.

### Phase 4 - Convert and package

Check Lakebridge transpiler support separately from assessment. Run a bounded
pilot when supported; otherwise use governed fallback. Update Lakebridge
Transpiler Status for every object, preserve assessment evidence, validate
generated definitions, and build an immutable migration package.

### Phase 5 - Non-production deployment

Deploy approved objects in dependency order. Isolate permission failures to
affected inventory objects instead of starting platform setup.

### Phase 6 - Layered validation

Validate schema, semantics, data contracts, consumers, operations, performance,
recovery, and cost. Reconcile Migration Inventory Status against actual target
objects and evidence.

### Phase 7 - Cut over and close

Cut over only after acceptance while rollback remains available. Preserve the
inventory, manifest, and status history.

## Staged Bronze modernisation scenario

For Staged Bronze Scenario, external Bronze registration, UC Upgrade, external-to-managed
conversion, or staged ADF ingestion replacement, apply four ordered scenario
stages inside the common flow:

1. register existing Bronze files read-only through Unity Catalog external
   tables;
2. migrate transformation logic and managed Silver/Gold outputs;
3. upgrade approved Bronze objects to managed Delta;
4. replace approved ADF ingestion while preserving the managed Bronze contract.

Each stage has an independent `PASS` gate and progression approval. Continue to
use the common workbook and manifest; add scenario stage, gate, writer
ownership, data action, original/managed locations, rollback, retention, and
cleanup fields. Keep schedules paused, source data retained, and writer
ownership unchanged until separately approved.

## Folder contract

```text
skills/synapse-to-azure-databricks/
  SKILL.md
  docs/
    README.md
    skill-routing.md
    skill-routing.drawio
    prerequisites.md
    prerequisites.drawio
    migration-approach.md
    migration-approach.drawio
  references/
    assessment.md
    target-mapping.md
    conversion.md
    deployment-validation.md
    synapse-serverless-sql.md
    synapse-dedicated-sql-pool.md
    synapse-spark.md
    staged-bronze-migration.md
    staged-bronze-external-registration.md
    staged-bronze-transformation-migration.md
    staged-bronze-managed-upgrade.md
    staged-bronze-adf-ingestion-migration.md
    staged-bronze-validation-cutover.md
  templates/
```

The editable process diagram is in
[migration-approach.drawio](migration-approach.drawio).
