# Prerequisites

Use three distinct stages and actors.

## Stage 0: customer-administrator setup

Customer administrators complete all privileged setup before migration starts:

1. Create or onboard the named migration-user account with MFA.
2. Prepare the customer VDI with GitHub Copilot in VS Code, repository access,
   Python, Java, Azure CLI, Databricks CLI, and Lakebridge.
3. Supply complete immutable source exports or grant exact read-only source
   discovery access.
4. Grant SQL metadata access and only the source-data reads required by the
   approved validation plan.
5. Add the migration user to the non-production Databricks workspace without
   account-admin, workspace-admin, or metastore-admin entitlement.
6. Create the target catalogs, schemas, initial owners, storage credentials,
   external locations, SQL warehouse, and compute policies.
7. Grant the migration user `CAN USE` only on approved compute.
8. Grant `USE CATALOG`, `USE SCHEMA`, and `CREATE TABLE` only on approved target
   schemas. Add `CREATE FUNCTION`, `CREATE MATERIALIZED VIEW`, `CREATE VOLUME`,
   `SELECT`, or `CREATE EXTERNAL TABLE` only when required by the migration
   scope.
9. Verify OAuth sign-in, allowed operations, denied administrative operations,
   expiry dates, support contacts, and rollback ownership.
10. Approve the handoff to the migration user.

### Install and verify Lakebridge

Lakebridge is a required readiness decision for this skill. Customer
administrators should normally install and verify it on the customer VDI
before handoff. If the skill detects that Lakebridge is missing, it must stop and ask the user whether to install it; it must not install Lakebridge or
silently choose fallback. Before asking, the skill reports the supported
Python and Java versions, Databricks CLI/workspace authentication, network
requirements, and the exact install and verification commands.

The official command-line prerequisites are:

- A reachable Azure Databricks workspace.
- Databricks CLI configured for an approved workspace profile.
- Python 3.10.1 through 3.14.x.
- Java 21 or later when the Morpheus transpiler is in scope.
- Approved outbound access to GitHub, Maven Central, and PyPI.

Verify the prerequisites:

```powershell
python -V
java -version
databricks version
databricks auth profiles
```

After the user or customer administrator approves installation, install and
verify Lakebridge:

```powershell
databricks labs install lakebridge
databricks labs lakebridge --help
```

For an approved non-default Databricks profile:

```powershell
databricks labs install lakebridge --profile <profile_name>
```

Installing a transpiler is a separate approval-gated action:

```powershell
databricks labs lakebridge install-transpile
```

Do not add `--include-llm-transpiler true` unless the user separately approves
the LLM-backed component, its data handling, and the exact input scope. The
Windows/macOS Lakebridge desktop application is an alternative for customers
that prefer a graphical installer; obtain it from the official Lakebridge
GitHub release page and follow the customer software-approval process.

Official installation reference:
https://github.com/databrickslabs/lakebridge/blob/main/docs/lakebridge/docs/installation.mdx

The exact Azure portal, Synapse, ADLS, Microsoft Entra, and Azure Databricks
steps are in the `Customer Setup` sheet of
[synapse-to-azure-databricks-prerequisites.xlsx](synapse-to-azure-databricks-prerequisites.xlsx).
Each row includes placeholders, a column for the actual action used, expected
handoff evidence, status, and completion ownership.

## Stage 1: migration user runs the skill

After handoff, the separate named migration user runs GitHub Copilot from the
customer VDI and performs the migration:

1. Begin Phase 1 discovery using the assumed working source and target access.
2. Build the inventory and dependency graph.
3. Record Lakebridge Assessment Status, Lakebridge Transpiler Status, and
   Migration Inventory Status for every object.
4. Run Lakebridge assessment where supported and governed fallback otherwise.
5. Convert and package approved schema objects, using the Lakebridge transpiler
   only where separately supported.
6. Deploy to the approved non-production target.
7. Validate structure, SQL binding, schemas, data contracts, behavior,
   consumers, performance, operations, recovery, and cost.
8. Persist failures and resume only remaining objects.

At every phase transition, the skill reports the phase name and status, work
being performed, completion evidence, and the gate for the next phase.

The runtime skill does not repeat this setup or branch into Azure Arc,
workspace provisioning, identity onboarding, role assignment, networking, or
device readiness. A permission failure blocks only the affected inventory
objects.

The migration user does not create workspaces, metastores, catalogs, storage
credentials, external locations, warehouses, compute policies, Entra groups,
or administrative role assignments.

## Stage 2: security migration

After technical schema validation:

1. The migration user inventories source groups, users, workload identities,
   ownership, memberships, grants, denies, and scopes.
2. The migration user prepares the security mapping and validation plan.
3. Customer identity and platform administrators approve, create, or reuse
   target principals and apply ownership and grants.
4. The migration user validates both intended access and intended denial.
5. Customer administrators revoke temporary migration access after handoff.

Do not copy source role names mechanically. Reuse existing approved groups when
they preserve the required behavior.

## Readiness gate

Record each customer setup row as `Verified`, `Blocked`, `Not applicable`, or
`Pending approval`. Migration starts only after every required row is
`Completed` or `Verified` and the handoff row is approved. Credentials and
tokens are never written to the workbook.

The editable readiness flow is in [prerequisites.drawio](prerequisites.drawio).
