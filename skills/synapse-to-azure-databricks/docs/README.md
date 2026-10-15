# Synapse to Azure Databricks documentation

This folder contains human-facing documentation and editable Draw.io diagrams
for the single `synapse-to-azure-databricks` routing skill.

| Topic | Markdown | Draw.io |
|---|---|---|
| Skill routing and file structure | [skill-routing.md](skill-routing.md) | [skill-routing.drawio](skill-routing.drawio) |
| Optional platform setup reference, completed before migration | [prerequisites.md](prerequisites.md) | [prerequisites.drawio](prerequisites.drawio) |
| End-to-end migration approach | [migration-approach.md](migration-approach.md) | [migration-approach.drawio](migration-approach.drawio) |

The migration approach includes the staged Bronze modernisation scenario for
external Bronze registration, transformation migration, managed Delta
upgrade, and approved ADF ingestion replacement.

Use
[synapse-to-azure-databricks-prerequisites.xlsx](synapse-to-azure-databricks-prerequisites.xlsx)
to assign owners and track prerequisites, manual execution steps, security
mapping, approvals, and evidence. Its primary `Customer Setup` sheet provides
the customer administrator, Azure or Azure Databricks platform, detailed setup
steps, placeholders to replace, a column for the command or action actually
used, and the expected handoff evidence.

The runtime migration skill assumes this setup is already complete and does not
run platform-readiness or access-remediation phases.

Keep runtime instructions in `../references/`. Put future architecture and
process diagrams in this folder rather than beside `SKILL.md` or inside a
workload reference.
