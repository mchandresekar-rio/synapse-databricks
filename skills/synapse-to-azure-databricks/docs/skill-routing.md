# Skill routing

`synapse-to-azure-databricks` is the only published Synapse migration skill.
Its top-level `SKILL.md` owns common Lakebridge governance, inventory,
approvals, evidence, and lifecycle rules.

The router loads only the required workload reference:

| Source workload | Runtime reference |
|---|---|
| Synapse Serverless SQL | `references/synapse-serverless-sql.md` |
| Synapse Dedicated SQL Pool | `references/synapse-dedicated-sql-pool.md` |
| Synapse Spark | `references/synapse-spark.md` |
| ADF or Synapse pipelines | Companion `pipelines-to-azure-databricks-workflows` skill |
| Staged Bronze modernisation | `references/staged-bronze-migration.md`, then its four ordered stage references |

Mixed estates use one inventory and manifest while preserving explicit
cross-workload dependencies. Workload-specific assumptions never flow into
another track without an explicit mapping decision.

The staged Bronze route is an additional scenario, not a replacement workflow.
It retains the common seven CAF phases, mandatory workbook/manifest, phase
announcements, Lakebridge and inventory statuses, approvals, and evidence. Its
internal stages are external registration, transformation migration, managed
Delta upgrade, and approved ADF ingestion replacement.

The editable architecture is in [skill-routing.drawio](skill-routing.drawio).
