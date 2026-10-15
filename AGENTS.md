# Synapse to Databricks Development Agent

## Repository scope

This repository is intentionally limited to Azure Synapse to Azure Databricks migration guidance. It contains the supported migration skills for:

- Synapse SQL, Spark, and data platform assessment and conversion.
- ADF and Synapse pipeline migration to Azure Databricks Workflows.
- Inventory, mapping, validation, deployment, and cutover artifacts for the supported migration paths.

Do not add unrelated Fabric or Power BI skills, or broaden this repo beyond the Synapse-to-Databricks scope.

## Architecture

Repository layering is **Agents → Skills → skill-local references**. Shared content should only be added when two or more published skills consume it.

## Requirements

- Every skill lives at `skills/<name>/SKILL.md`.
- Every `SKILL.md` has YAML frontmatter containing `name` and an action-oriented `description` with explicit triggers.
- Skills include Must, Prefer, Avoid, and Examples sections.
- New or materially changed behavior requires Vally smoke and full-eval coverage.
- Smoke routing runs against the complete `databricks-skills` bundle.
- Migration evals are offline unless live cloud state is essential.
- Never hardcode credentials, tokens, workspace URLs, subscription IDs, or tenant IDs.

## Independence

Do not introduce forks, submodules, cross-repository reusable workflows, source-repository checkouts, synchronization jobs, or package/runtime dependencies on another skills repository. Run `python scripts/check_independence.py` before committing.

## Safety

Treat migration sources as read-only by default. Require explicit approval before destructive target operations, costly compute creation, data movement, or cutover. Prefer generated plans and artifacts over immediate execution.
