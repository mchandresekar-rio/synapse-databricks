# Synapse Spark to Azure Databricks

Use this reference for Synapse Spark pools, notebooks, Spark Job Definitions, libraries, session configuration, lake databases, Hive metastore dependencies, and Spark-specific connectors.

## Scope and discovery

Inventory Spark pools, runtime and language versions, node families, autoscale, auto-pause, Spark configuration, packages, init behavior, notebooks, Spark Job Definitions, parameters, triggers, schedules, linked services, credentials by reference, storage paths, lake databases, metastore dependencies, connectors, consumers, SLAs, and costs.

Preserve notebook cell order, language boundaries, source hashes, dependency graphs, and pool bindings. Discover through exports or approved read-only APIs.

## Lakebridge capability boundary

Apply the common Lakebridge contract from the parent skill. Use Analyzer or
Profiler only when the installed release explicitly supports the Synapse Spark
assessment scope. Before notebook or code conversion, run the separate
Lakebridge conversion gate for the exact artifact type, language, runtime, and
target, then approve a representative pilot. Assessment support does not imply
conversion support. A successful notebook conversion does not validate
connector behavior, library compatibility, data access, parameters, or job
semantics.

## Target mapping

| Synapse Spark source | Databricks candidate |
|---|---|
| Spark pool | Approved serverless compute, cluster policy, or job cluster |
| Notebook | Databricks notebook or source file in an Asset Bundle |
| Spark Job Definition | Databricks Job task in an Asset Bundle |
| Pool library | Wheel, JAR, requirements lock, or governed environment dependency |
| Lake database or Hive metadata | Unity Catalog catalog, schema, table, external table, or approved federation pattern |
| Linked service | Workload identity, storage credential, external location, secret scope, or governed connection |
| Synapse trigger or pipeline | `pipelines-to-azure-databricks-workflows` |

## Conversion

- Replace `mssparkutils` by behavior, not mechanical namespace substitution.
- Replace Synapse-only Spark connectors and pool configuration explicitly.
- Preserve required and default parameter semantics.
- Replace unmanaged mounts and embedded storage credentials with Unity Catalog-governed access.
- Pin compatible Python, Scala, Java, Spark, Delta, and library versions.
- Package notebooks, jobs, permissions, variables, and environments through Databricks Asset Bundles where practical.
- Keep unsupported .NET for Spark, GPU, external metastore, connector, or runtime behavior as a blocker or approved retained workload.

## Validation

Validate static imports and references, bundle schema, cluster startup, parameter propagation, secrets by reference, library resolution, data access, schemas, transformations, writes, idempotency, retries, schedules, concurrency, recovery, observability, performance, and cost. Compare approved output contracts and representative data evidence; notebook execution success alone is insufficient.

## Must

- Map every notebook and job to an approved compute and identity policy.
- Preserve cell languages, parameters, dependencies, and schedule semantics.
- Validate library and runtime compatibility before deployment.
- Use Unity Catalog for production data governance.

## Prefer

- Serverless job compute where region, networking, policy, and libraries permit it.
- Reproducible wheels, JARs, lock files, and Asset Bundles.
- One workload wave at a time with explicit rollback.

## Avoid

- Do not mechanically rename `mssparkutils`.
- Do not hide production dependencies in interactive `%pip` state.
- Do not hardcode workspace IDs, storage URLs, secrets, or cluster IDs.
- Do not assume successful execution proves behavioral or data parity.

## Examples

- "Assess Synapse Spark pools, notebooks, and Spark Job Definitions for Azure Databricks."
- "Convert exported Synapse notebooks to an Asset Bundle without deploying them."
