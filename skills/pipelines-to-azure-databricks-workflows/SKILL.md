---
name: pipelines-to-azure-databricks-workflows
description: "Assess, design, convert, validate, and deploy Azure Data Factory (ADF) or Azure Synapse pipeline orchestration to Azure Databricks Jobs and Workflows, with explicit hybrid retention for integration activities. Use for 'ADF pipeline to Databricks Workflow', 'Synapse pipeline to Databricks Jobs', 'pipeline JSON to Asset Bundle', 'orchestration migration', or 'move pipelines to Azure Databricks workflows'."
---

# ADF and Synapse Pipelines to Azure Databricks Workflows

Migrate orchestration from Azure Data Factory or Azure Synapse pipelines to
Azure Databricks Jobs and Workflows without pretending that every integration
activity has a native Databricks task equivalent.

This skill owns pipeline orchestration migration. A workload-specific migration
skill may reference it, but should not duplicate pipeline conversion logic.

## Assumed platform baseline

Assume ADF or Synapse access, Azure Databricks access, the target workspace,
and provisioned Unity Catalog already exist. Do not branch into Azure Arc,
workspace or metastore provisioning, identity onboarding, role assignment,
networking/private-endpoint setup, customer-device setup, or general
target-readiness troubleshooting.

If an actual migration operation fails because of a permission or platform
configuration issue, record the exact operation and affected pipeline
dependencies, mark only those items `Blocked`, and continue independent
inventory, classification, packaging, or validation work.

## Response contract

For an offline design, routing, or synthetic-manifest request, answer directly
from the supplied facts. Do not search for files, create the workbook or JSON
manifest, invoke deployment tools, or ask for inputs the prompt declares
complete. Define the required artifacts and gates in a compact response so the
assessment does not turn into an implementation loop.

Every assessment response must explicitly summarize:

- **Inventory intake** — when discovery is in scope, distinguish ADF Azure
  Resource Manager (`management.azure.com`) from the Synapse data-plane
  (`dev.azuresynapse.net`) audience, and cover pagination, individual full
  definition GETs, read-only limits, redacted immutable snapshots, counts,
  hashes, and reference reconciliation. Compare **live** and **export**
  evidence for **drift**, require an **authoritative** baseline, and name the
  **Excel workbook** and **JSON manifest** outputs.
- **Activity disposition** — classify each activity as native, rewrite, retain,
  hybrid, blocker, or retire, including Copy/SHIR, SSIS, notebook/SQL,
  ExecutePipeline, IfCondition, and ForEach when they are in scope.
- **Workbook** — state that pipeline sheets are added to the authoritative
  Synapse-to-Databricks migration workbook. Name its existing `Migration
  Status`, `Target Objects`, and `Dependencies` sheets and the added
  `Pipelines`, `Activities`, `Pipeline Dependencies`, `Runs and validation`,
  and `Pipeline Summary` sheets.
- **JSON manifest** — name the stable source ID, source hash, lifecycle status,
  package hash, approval, failed-attempt history, and `last_updated_utc` fields.
- **Package and validation** — describe the immutable Asset Bundle, behavioral
  tests, rollback, and evidence.
- **Cutover guard** — identify one retry/schedule owner, prevent circular
  orchestration, and state that source and target schedules must never be
  active together.

When the user asks to execute rather than define the migration, create and
maintain the artifacts described below.

Before completing any assessment, verify that the response names the existing
`Migration Status`, `Target Objects`, and `Dependencies` sheets and the added
`Pipelines`, `Activities`, `Pipeline Dependencies`, `Runs and validation`, and
`Pipeline Summary` sheets, and describes the JSON manifest. Do not replace
this inventory-artifact summary with a generic reference to documentation.
Use the literal labels **Excel workbook** and **JSON manifest** even when the
file names already end in `.xlsx` and `.json`.

## Workflow

### 1. Load the serverless inventory and pipeline source

For Synapse pipeline migration, require the authoritative workbook and JSON
manifest produced by the `synapse-to-azure-databricks` migration. The workbook
must contain:

- `Migration Status`, including separate Lakebridge Assessment Status,
  Lakebridge Transpiler Status, and Migration Inventory Status columns;
- `Target Objects`, populated from actual Databricks target evidence;
- `Dependencies`, containing source dependency edges.

Hash both upstream artifacts and record their paths, hashes, revisions, and
item counts in the pipeline manifest. Reconcile stable source identities
between the workbook and manifest before pipeline classification. Do not
recreate, summarize, or replace the serverless inventory.

Use `Migration Status` and `Target Objects` to resolve Synapse datasets, SQL
objects, views, and ingestion outputs to verified Databricks targets. A
mapping is usable only when the target record is present and Migration
Inventory Status is `reconciled`. Never infer a target from a similar name.
When a required upstream object is missing, `drifted`, or `blocked`, block only
the dependent pipeline activities and continue independent pipelines.

Identify whether each pipeline comes from ADF, Synapse, or both and select one
inventory intake mode:

1. **Live read-only discovery** — connect to the approved ADF factory or
   Synapse workspace and retrieve all requested definitions.
2. **Offline export intake** — read a supplied ARM template, Git-mode export,
   workspace publish export, or folders/files containing pipeline dependencies.

Use supplied exports when the user identifies them as authoritative.
Otherwise use read-only live discovery against the stated factory or workspace.

#### Live read-only discovery

For ADF, authenticate to Azure Resource Manager and enumerate the factory,
pipelines, datasets, linked services, integration runtimes, triggers, global
parameters, managed private endpoints where relevant, and repository
configuration through supported read-only ARM or SDK operations. Follow every
continuation token until the list is complete, then GET each individual
definition so list-response summaries are not mistaken for full JSON.

For Synapse, use the Synapse data-plane audience to enumerate and GET
pipelines, datasets, linked services, triggers, integration runtimes, notebooks,
Spark job definitions, SQL scripts, credentials, and other referenced workspace
artifacts that are required to resolve pipeline dependencies. Use ARM read-only
operations for workspace properties, repository configuration, managed virtual
network/private endpoints, and global parameters when the data-plane response
does not contain them.

Record:

- tenant and subscription context without tokens;
- resource group, factory/workspace name, resource ID, and endpoint;
- authenticated principal/object or application ID;
- API/SDK and version used;
- request scope, retrieval timestamp, pagination completion, item counts, and
  per-type failures;
- canonical JSON SHA-256 for every retrieved definition.

Store immutable raw snapshots outside the source repository and Databricks
workspace. Redact secret values while preserving secret references and
authentication types. Never log access tokens, connection strings, passwords,
keys, SAS tokens, or secure strings. Live discovery permits only GET/list
operations: no publish, create, update, delete, trigger, cancel, debug, or
integration-runtime key operation.

After retrieval, reconcile list counts with full definitions and references.
Retry only bounded transient read failures. Mark incomplete types and unresolved
references as blockers; do not silently continue with a partial inventory.

#### Offline export intake

Accept:

- ADF ARM templates and parameter files;
- ADF Git-mode folders such as `pipeline`, `dataset`, `linkedService`,
  `trigger`, `integrationRuntime`, and `globalParameters`;
- Synapse workspace publish exports or Git-mode folders;
- a bounded archive or directory of individual pipeline and dependency JSON
  files.

Inventory every supplied file before parsing it. Record its relative path,
size, SHA-256, detected source/type, parse result, duplicate/collision status,
and source object name. Resolve references across files and report missing
dependencies. Do not assume that a pipeline-only export is complete when its
datasets, linked services, triggers, notebooks, scripts, or child pipelines are
absent.

Both modes produce the same normalized inventory schema. If live discovery and
an export are both available, preserve both evidence sets, compare hashes and
counts, report drift, and require a declared authoritative baseline rather than
silently merging conflicting definitions.

Inventory pipeline JSON, folders, annotations, parameters, variables, global
parameters, datasets, linked services, integration runtimes, triggers, tumbling
windows, event subscriptions, dependencies, retries, timeouts, concurrency,
secure input/output settings, monitoring, alerts, and operational ownership.

Use exported definitions by default. Live discovery is read-only and requires
approval for the exact factory or workspace. Treat source services as read-only.
Never start, stop, publish, trigger, or modify a source pipeline during
assessment.

Assign a stable source ID and content hash to every pipeline and dependency.
Record whether the export is complete. Missing linked services, datasets,
triggers, parameters, notebooks, scripts, or child pipelines block claims of a
complete migration.

### 2. Extend the authoritative migration inventory

Add pipeline sheets to the authoritative Synapse-to-Databricks migration
workbook instead of creating a competing workbook. Create or update the
companion pipeline section in the existing machine-readable migration manifest.
For ADF-only work with no upstream workload inventory, create the same combined
workbook structure and document that no serverless baseline applies.

The workbook must use a professional font, preserve any existing template, and
contain at least:

- **Pipelines** — source system, factory/workspace, folder, stable source ID,
  source name, source hash, target job name/ID, architecture, lifecycle status,
  approval gate, owner, blocker, package hash, deployment/run IDs, validation
  result, rollback boundary, and last-updated UTC;
- **Activities** — pipeline source ID, activity path, activity type,
  dependencies and conditions, policy/retry/timeout/concurrency, referenced
  datasets/linked services/notebooks/child pipelines, disposition, target task,
  conversion status, validation status, blocker, and evidence;
- **Pipeline Dependencies** — datasets, linked services, integration runtimes, global
  parameters, triggers, notebooks, scripts, child pipelines, identities,
  connections, and whether each is present, mapped, retained, or blocked;
- **Runs and validation** — immutable package hash, approval, deployment/run
  IDs, timestamps, outcomes, failed task, retry/restart evidence, schedule
  state, cleanup state, and evidence links;
- **Pipeline Summary** — formula-driven counts by source, disposition, lifecycle state,
  blocker, deployment, and validation status;
- **Metadata and Lists** — source locations and hashes, tool versions, status
  definitions, evidence paths, and controlled values for data validation.

Use these lifecycle states consistently:

`Inventoried`, `Assessed`, `Mapped`, `Blocked`, `Approved`, `Converted`,
`Packaged`, `Deployed`, `Validated`, `Cutover Ready`, `Cut Over`, `Retained`,
`Retired`, `Failed`, and `Rolled Back`.

Update the workbook and JSON manifest after every pipeline/activity decision,
package change, approval, deployment attempt, test run, failure, cleanup,
pause, resume, cutover, or rollback. Preserve failed attempts; never replace
history with the latest success. Reconcile workbook formulas with manifest
counts and verify zero formula errors before delivery.

The JSON manifest is authoritative for automation and contains the same stable
IDs, hashes, dispositions, lifecycle states, dependencies, approvals, evidence,
and current/previous package hashes. The workbook is the human review and
progress view. Neither artifact authorizes deployment by itself.

### 3. Classify every activity

Classify each activity as:

- `workflow-native`: maps to a Databricks task while preserving behavior;
- `rewrite`: behavior can move to a notebook, Python wheel, SQL, dbt, JAR, or
  `run_job_task`, but requires reviewed target code;
- `retain-external`: ADF or Synapse remains the system of orchestration for the
  activity;
- `hybrid-boundary`: a retained pipeline calls a Databricks job, or a
  Databricks task calls an approved external API;
- `blocker`: semantics, connectivity, identity, or evidence are unresolved;
- `retire`: separately approved removal of unused orchestration.

Typical mappings:

| ADF / Synapse construct | Databricks disposition |
|---|---|
| Databricks notebook, Python, JAR | Native notebook, Python wheel, or JAR task |
| Synapse notebook or Spark job | Rewrite to approved Databricks notebook, wheel, or JAR task |
| Stored procedure or SQL script | Databricks SQL task only when dialect, transaction, identity, and result semantics are preserved |
| Execute Pipeline | `run_job_task` or retained child pipeline, with parameter and failure propagation |
| If Condition | Workflow branching through task values, conditions, or reviewed controller code |
| ForEach | `for_each_task` when item, concurrency, ordering, and failure behavior match |
| Until | Reviewed controller task; never assume a direct equivalent |
| Wait | Controller/notebook task only when timing and cost are acceptable |
| Web / Azure Function | Approved HTTP/controller task with secret-backed authentication |
| Copy / Data Flow | Retain externally unless an approved Databricks ingestion rewrite preserves connector, IR, schema, fault, and throughput contracts |
| Lookup / Get Metadata | SQL, notebook, or controller task after result-shape and empty-result validation |
| Validation | Explicit precondition task and failure path |
| Set / Append Variable | Job parameters or task values with type and scope validation |
| SSIS / Azure Batch / Custom | Retain, redesign, or block; no automatic native mapping |

Do not classify from activity type alone. Inspect expressions, datasets,
linked services, integration runtimes, policies, dependencies, parameters, and
downstream consumers.

### 4. Design native or hybrid orchestration

Preserve:

- success, failure, completion, and skip dependencies;
- retry count, retry interval, timeout, cancellation, and idempotency;
- pipeline, trigger, and activity parameters, defaults, types, expressions, and
  secure values;
- sequential versus parallel execution, batch count, concurrency, and ordering;
- child-pipeline parameter passing and returned values;
- schedule, timezone, daylight-saving, tumbling-window, backfill, event, and
  rerun behavior;
- source pipeline and trigger display names exactly by default, including
  casing, spaces, and underscores; add environment or user prefixes/suffixes
  only when the user explicitly approves a target naming convention;
- managed identity, service-principal, secret, network, and private-endpoint
  boundaries;
- monitoring, alerting, correlation IDs, run history, lineage, and ownership.

Choose one architecture per pipeline:

1. **Databricks-native** — every required activity is safely mapped.
2. **External-primary hybrid** — ADF/Synapse retains integration and invokes an
   approved Databricks job for compute.
3. **Databricks-primary hybrid** — Databricks orchestrates compute and calls an
   approved external endpoint for retained integration.
4. **Retained external** — migration risk exceeds value or required capability
   has no approved Databricks equivalent.

Prevent circular orchestration. Define one owner for retries and schedules at
each boundary so neither side duplicates a run.

### 5. Generate an immutable migration package

Prefer a Databricks Asset Bundle for jobs, environments, permissions, and
deployment targets. The package must contain:

- source IDs and hashes;
- activity and dependency inventory;
- native/rewrite/retain/block decisions with reasons;
- job/task definitions and target code hashes;
- parameters, task values, schedules, notifications, identities, clusters,
  serverless settings, libraries, environments, and permissions;
- retained external pipeline and call-boundary definitions;
- rollback boundary and cutover guard;
- validation cases and unresolved blockers.

Validate bundle syntax and task references offline. Resolve environment values
through bundle variables or approved secret scopes. Never hardcode tokens,
passwords, workspace URLs, subscription IDs, tenant IDs, factory names, or
workspace-specific resource IDs in reusable definitions.

Any package edit requires a new hash and renewed approval before deployment.

### 6. Deploy only after approval

Require explicit approval before creating or updating jobs, clusters, policies,
secret scopes, service principals, permissions, schedules, webhooks, or source
callers. Apply least privilege and separate deployment from runtime identities.

Deploy without enabling schedules. Validate target objects and permissions,
then run bounded non-production tests. Schedule activation and source-trigger
disablement are separate cutover actions and must never occur in the same
implicit step.

When schedule definitions are part of an approved deployment, create them in
the `PAUSED` state with the exact source trigger names, recurrence, timezone,
daylight-saving behavior, parameters, and target workflow. If one source
pipeline has multiple triggers, preserve each trigger as a separately named
paused scheduler definition rather than flattening or dropping schedules.
Do not add Databricks development-mode user prefixes or environment suffixes
to source-derived job or trigger names unless the user approved that naming
policy.

A deployment is not complete until the **Excel workbook** and **JSON manifest**
are updated from the verified target state. Record the actual target job and
scheduler IDs, exact deployed names, workspace URLs, package hash, deployment
timestamp and attempt ID, approval, paused/active schedule state, validation
result, and evidence location. Preserve failed attempts alongside the final
success. Reconcile workbook formulas and manifest counts after the update; do
not report deployment success while either artifact still says `Mapped`,
contains null target IDs, or describes schedules as absent when paused
schedules were deployed.

### 7. Validate behavior

Validate more than successful task completion:

- graph structure and dependency outcomes;
- parameter and expression parity;
- retry, timeout, cancellation, skipped-task, and failure propagation;
- sequential/parallel and concurrency behavior;
- idempotent replay, duplicate prevention, watermark advancement, backfill,
  partial-failure restart, and late-arriving data;
- retained external call boundaries and correlation IDs;
- identity, secret, network, and private connectivity;
- schedule/timezone/DST behavior without activating duplicate schedules;
- monitoring, alerts, lineage, duration, compute utilization, and cost;
- rollback while the source schedule remains available.

Cut over only after acceptance evidence and explicit approval. Activate the
Databricks schedule and disable the source trigger through a guarded,
reversible sequence. Never leave both schedules active.

## Must

- Support both Azure Data Factory and Azure Synapse pipeline exports.
- Assume working source and target access and provisioned Unity Catalog; do not
  enter Azure Arc, platform provisioning, identity onboarding, permission
  setup, networking setup, or device-readiness flows.
- Support approved live read-only discovery of all pipelines and dependencies
  from an ADF factory or Synapse workspace, including pagination and individual
  definition retrieval.
- Support offline ARM/Git/workspace exports as an equivalent inventory input
  and reconcile live-versus-export drift when both are supplied.
- Inventory pipelines and every referenced orchestration dependency before
  conversion.
- Require and hash the authoritative Synapse serverless migration workbook and
  manifest for Synapse pipeline migration. Consume `Migration Status`, `Target
  Objects`, and `Dependencies`; carry the separate Lakebridge Assessment
  Status, Lakebridge Transpiler Status, and Migration Inventory Status columns
  into pipeline dependency decisions.
- Add pipeline sheets to the existing serverless workbook rather than creating
  a competing inventory, and use only `reconciled` target mappings.
- Create and continuously update the Excel inventory workbook and machine-
  readable JSON manifest using stable IDs, lifecycle states, immutable hashes,
  approvals, attempts, blockers, and evidence.
- Reconcile workbook formulas and summary counts with the JSON manifest and
  deliver the workbook with zero formula errors.
- Classify each activity as native, rewrite, retain, hybrid, blocker, or retire.
- Preserve dependency, parameter, retry, timeout, concurrency, schedule,
  failure, identity, and monitoring semantics.
- Preserve exact source pipeline and trigger names by default, and preserve
  every trigger as an independently traceable paused schedule definition
  before cutover.
- Treat post-deployment Excel workbook and JSON manifest reconciliation as a
  required completion gate, using verified target IDs, names, URLs, schedule
  states, package hash, attempts, timestamps, approvals, and evidence.
- Produce a hybrid decision whenever only part of a pipeline belongs in
  Databricks.
- Keep source pipelines read-only until separately approved cutover.
- Validate generated Asset Bundle and job definitions offline before deployment.
- Require separate approvals for deployment, live tests, schedule activation,
  source-trigger disablement, destructive cleanup, and cutover.
- Prevent duplicate scheduling and circular orchestration.
- Preserve source IDs, hashes, target hashes, decisions, and evidence.

## Prefer

- Databricks Asset Bundles for jobs and environment-specific configuration.
- Jobs API 2.1 task types and explicit job parameters/task values.
- Existing approved Databricks compute policies and serverless jobs where
  compatible.
- External-primary hybrid orchestration when ADF/Synapse owns connectors,
  private integration runtimes, or data movement that Databricks cannot safely
  replace.
- Synthetic and non-production failure-path tests before any schedule cutover.

## Avoid

- Do not claim every ADF or Synapse activity has a Databricks equivalent.
- Do not issue source write/publish/run/debug/cancel/delete operations during
  live inventory discovery.
- Do not treat list-response summaries or pipeline-only exports as complete
  definitions.
- Do not merge conflicting live and exported definitions without reporting
  drift and selecting an authoritative baseline.
- Do not track only pipeline-level status; preserve activity, dependency,
  package, deployment-attempt, validation, and cutover history.
- Do not overwrite failed attempts or let the workbook and JSON manifest drift.
- Do not convert Copy, Data Flow, SSIS, SHIR-only, Azure Batch, or Custom
  activities automatically.
- Do not flatten success/failure/completion dependencies into success-only
  ordering.
- Do not replace expressions or variables without type, null, and result-shape
  validation.
- Do not embed credentials or environment-specific resource identifiers.
- Do not deploy or enable schedules from an assessment request.
- Do not silently add personal IDs, development prefixes, environment
  suffixes, or normalized display names to migrated jobs or triggers.
- Do not omit, merge, or activate source schedules during deployment; preserve
  approved schedule definitions in a paused state until separately approved
  cutover.
- Do not disable source triggers until target acceptance and rollback approval.
- Do not run both source and target schedules without an explicit duplicate-
  prevention test boundary.
- Do not treat reconstructed orchestration as original exported pipeline
  evidence.

## Examples

- “Assess these ADF pipelines and identify which activities can move to Azure
  Databricks Workflows.”
- “Convert exported Synapse pipeline JSON into a Databricks Asset Bundle job,
  retaining Copy activities in Synapse.”
- “Design a hybrid ADF-to-Databricks orchestration with one schedule owner and
  idempotent retries.”
- “Validate parameter, failure-path, restart, and schedule parity before
  cutting over these pipelines.”
