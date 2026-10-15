# Contributing

This repository is scoped to Synapse-to-Databricks migration skills. Keep all changes aligned to the supported migration paths and avoid broadening the project into unrelated Fabric, BI, or modernization domains.

1. Create a focused branch and keep each skill change independently reviewable.
2. Add or update smoke and full-eval coverage for behavioral changes.
3. Run `python scripts/check_independence.py`.
4. Run `python build/build_plugins.py --check`.
5. Run `python -m pytest -q tests`.
6. Dry-run Vally staging with `pwsh ./tests/run-vally-eval.ps1 -Suite smoke -DryRun`.
7. Do not commit generated plugin trees, Vally output, credentials, or cloud identifiers.
8. Keep the repository limited to the supported Synapse and pipeline migration skills only.

Migration guidance must distinguish source inventory, target design, approval, conversion, deployment, validation, rollback, and cleanup. Sources remain read-only unless the user explicitly authorizes a separately scoped source mutation.
