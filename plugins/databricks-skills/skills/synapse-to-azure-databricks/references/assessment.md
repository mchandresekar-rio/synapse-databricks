# Assessment

## Evidence sources

Prefer exported workspace artifacts, ARM metadata, Synapse data-plane definitions, SQL project/DACPAC metadata, dependency manifests, and source-controlled notebooks. Discovery remains read-only.

## Required output

Produce:

1. A populated
   `reports/synapse-to-databricks-migration-inventory.xlsx`, companion
   `reports/synapse-to-databricks-migration-inventory.manifest.json`, inventory
   summary, and dependency graph. Create the artifacts in Phase 1 with
   `scripts/create_migration_inventory.py`; do not return only a narrative,
   blank template, CSV, or JSON manifest. The workbook must contain a populated
   `Migration Status` worksheet and the `Target Objects` and `Dependencies`
   worksheets. Populate those latter worksheets when target evidence or source
   dependency edges exist. The workbook must reconcile to the complete approved
   source scope.
2. Compatibility table with `direct`, `rewrite`, `redesign`, `retain`, or `blocker` status.
3. Security, networking, governance, runtime, data, and orchestration gaps.
4. Decisions required before target design.
5. Proposed validation evidence for each workload.
6. When Lakebridge emits an Excel report, an enriched copy of that workbook
   containing a `Migration Status` worksheet. Use stable source identity to
   merge Lakebridge coverage with the authoritative governed inventory. Include
   every approved-scope item, including fallback-only items absent from the
   Lakebridge report, and record target mapping, lifecycle status, deployment,
   validation, owner, blocker or review reason, and next action.
7. A `Target Objects` worksheet sourced from Databricks deployment and
   validation evidence, listing every created catalog object and its catalog,
   schema, name, type, source mapping, deployment/validation status and
   statement IDs, row count or contract metric, owner, and rollback boundary.

Never suppress an unsupported construct merely because the containing notebook or SQL file parses successfully.
