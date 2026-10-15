# Synapse to Databricks Migration Skills

Private, independently maintained AI coding-assistant skills for modernising
Azure Synapse workloads to Azure Databricks.

This repository is intentionally scoped to Synapse-to-Databricks migration only.
It contains the skills, references, templates, and eval coverage needed to assess
and convert Synapse assets into Databricks-compatible patterns.

## Included capabilities

- Synapse to Azure Databricks migration guidance and assessment.
- Synapse pipeline migration to Azure Databricks Workflows.
- Inventory, mapping, validation, and cutover planning artifacts.
- Offline-first Vally smoke and full-eval coverage for the supported migration flows.
- Independent plugin materialization for Copilot-compatible layouts.

## Repository scope

This repository keeps only the following skill bundles:

- `skills/synapse-to-azure-databricks/`
- `skills/pipelines-to-azure-databricks-workflows/`

Related plugin bundles and validation assets for those same migration skills are
kept in the corresponding `plugins/` and `tests/evals/` folders.

## Independence

This repository does not consume files, workflows, packages, generated
artifacts, or runtime infrastructure from another skills repository. Run:

    python scripts/check_independence.py

## Local validation

Prerequisites: Python 3.11+, PowerShell 7+, and Node.js 22+.

    python -m pip install -r tests/requirements-dev.txt
    python build/build_plugins.py --check
    python -m pytest -q tests skills
    pwsh ./tests/run-vally-eval.ps1 -Suite smoke -DryRun

A real Vally run additionally requires a valid Copilot authentication route
supported by `@microsoft/vally-cli`.

## Repository layout

- `skills/` — canonical migration skills and references.
- `plugins/` — plugin manifests and generated local bundles for the supported skills.
- `tests/evals/` — smoke and full-eval specs for Synapse-to-Databricks migration flows.
- `build/` — deterministic plugin materialization.
- `scripts/` — repository independence and maintenance helpers.

## Cloud testing policy

Migration behavior is tested offline by default. The reserved
`live-databricks` suite remains intentionally empty until a dedicated
non-production workspace, federated identity, isolation policy, and cleanup
process are approved.
