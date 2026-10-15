# Deployment, validation, and rollback

Deploy to non-production first. Assume source and target access, the workspace,
and provisioned Unity Catalog are already available. Validate Asset Bundle
configuration and target collisions before mutation.

Do not perform Azure Arc, workspace/metastore provisioning, identity
onboarding, role assignment, private-endpoint setup, customer-device setup, or
general target-readiness remediation. If deployment encounters a permission or
platform-configuration failure, record the exact failed operation and affected
inventory objects, mark only those objects `blocked`, and continue independent
migration work.

Do not require source security groups, end users, ownership, or role grants to
be migrated before technical schema validation. After schema validation passes,
inventory and map those principals and privileges, apply the approved target
security model, validate intended access and denial, transfer ownership, and
remove the migration operator's temporary grants before production cutover.

## Validation ladder

Run each applicable layer and mark unavailable checks `NOT RUN` with the
specific blocker and next action:

1. **Coverage:** every inventory item has a target or disposition, owner, dependency resolution, and test status.
2. **Static:** SQL parses and has no unresolved identifiers, converter TODOs, embedded credentials, or governance bypasses.
3. **Deployment:** bundle/configuration validates; target DDL and collision checks are reviewed before mutation.
4. **Metadata:** names, order, mapped types, precision/scale, nullability, comments, and partitions match the approved contract.
5. **Data:** compare more than counts—include nulls, distinct keys, min/max, aggregates, duplicates, and business invariants at a shared watermark.
6. **Query:** compare representative and edge-case parameter sets with deterministic keys or ordering.
7. **Technical acceptance gate:** confirm the migrated schema and behavior are stable enough to begin security migration.
8. **Security migration:** inventory and map groups, users, workload identities, ownership, grants, denies, and scopes without copying role names mechanically.
9. **Security validation:** verify both intended access and intended denial for each approved persona.
10. **Performance:** compare equivalent parameters, compute policy, concurrency, cache state, duration, bytes scanned, and cost signal against agreed thresholds.
11. **Consumer:** run application, JDBC/ODBC, and BI smoke/regression tests through the target endpoint.
12. **Operations:** verify retries, schedules, monitoring, alerts, ownership, runbooks, failure handling, and rollback.

## Comparison evidence

For serverless SQL, use the skill's parity-test manifest and validation-report templates. A validator should have separate manifest loading, read-only Synapse and Databricks adapters, and a comparison engine. Support `metadata`, `aggregate`, `partition`, `keyed_rows`, `query_result`, `business_rule`, `performance`, and `pipeline_contract` modes as needed. The `pipeline_contract` mode validates declared `pipeline_checks` such as idempotent replay, watermark advancement, partial-failure restart, duplicate prevention, fact grain, dimension referential integrity, late-arriving data, and serving-view results.

- Establish one source revision, snapshot, or watermark visible to both engines.
- Normalize only declared nondeterminism. Keep null, empty string, whitespace, zero, and missing values distinct unless the contract says otherwise.
- Compare decimals at contract precision and timestamps at the declared time zone and precision.
- Require unique keys for keyed comparisons and stable ordering for query results.
- Bound and protect diagnostic samples; do not export sensitive rows by default.
- Treat failed queries, missing prerequisites, and unavailable checks as failures or blockers—not successful parity.
- Record accepted differences with reason, owner, approval evidence, and expiry.

Lakebridge Reconcile may contribute evidence only when the installed release documents the exact source and report mode and the queries are approved. It does not replace SQL binding, security, consumer, performance, or operational checks.

## Coexistence and consumer waves

Before cutover, freeze or dual-maintain source definitions, synchronize data where applicable, activate target monitoring and cost controls, and test endpoint rollback. During coexistence, run both surfaces against the same watermark and stop when drift invalidates prior evidence.

For each consumer, record its owner, source endpoint/database, dependencies, driver, and authentication; update the Warehouse endpoint, HTTP path, catalog/schema defaults, and identity through approved configuration; run connectivity, metadata, query, refresh, and performance tests; obtain acceptance; then switch and monitor the wave.

Define rollback triggers before cutover, including critical-query failure, reconciliation breach, unauthorized access, refresh failure, latency/concurrency breach, or uncontrolled cost.

Rollback must identify how to disable new schedules, restore consumer routing, remove or quarantine newly created resources, and preserve diagnostic evidence. Never delete source resources as part of target deployment.

Retirement is a separate approved phase after all waves and the retention window. Confirm no consumer remains, archive evidence, revoke access reversibly before dropping metadata, monitor missed connections, and remove temporary migration grants. Never delete shared ADLS data merely because Synapse metadata is retired.
