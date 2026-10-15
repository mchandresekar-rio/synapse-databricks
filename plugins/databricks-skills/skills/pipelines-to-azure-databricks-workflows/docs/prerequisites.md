# Pipeline migration prerequisites

This is an optional setup reference for environments that are not already
ready. The runtime migration skill assumes ADF/Synapse and Databricks access,
an existing target workspace, and provisioned Unity Catalog. It does not create
a prerequisite phase or populate a `Pre Reqs` sheet during migration.

## Workbook columns

Use these columns:

`Category`, `Tool / Component`, `Requirement Level`, `Supported / Minimum
Version`, `Tested Baseline`, `Detected Version`, `Purpose`, `Verification
Command`, `Install / Source`, `Status`, `Evidence`, `Blocker / Next Action`,
and `Last Checked UTC`.

Allowed requirement levels are `Required`, `Conditional`, `One of`, and
`Skill validation only`. Allowed statuses are `Verified`, `Blocked`, `Not
installed`, `Pending approval`, and `Not applicable`.

## Version baseline

| Category | Tool / component | Requirement | Supported / minimum version | Tested baseline | Verification |
|---|---|---|---|---|---|
| Operator | Visual Studio Code | Required | Current customer-approved supported release | Record customer version | `code --version` |
| Operator | GitHub Copilot extension and authenticated route | Required | Current customer-approved supported release | Record customer version | `code --list-extensions --show-versions` |
| Execution | Python | Required | 3.11 or later | 3.12.10 | `python --version` |
| Execution | PowerShell | Required | 7.0 or later | 7.6.6 | `pwsh --version` |
| Source discovery | Azure CLI | Conditional for approved live discovery; not required for export-only intake | 2.83.0 or later tested-compatible release | 2.83.0 | `az version --output json` |
| Target packaging and deployment | Databricks CLI | Conditional until target validation or deployment | 0.269.0 or later tested-compatible release | 0.269.0 | `databricks version` |
| Package integrity | Git | Required | 2.40 or later | 2.55.0 | `git --version` |
| Workbook | openpyxl | Required | 3.1 or later, below 4.0 | Record installed version | `python -c "import openpyxl; print(openpyxl.__version__)"` |
| Workbook recalculation | Microsoft Excel Desktop | One of | Current customer-supported Microsoft 365 Apps release | Record customer version | Record Excel About/build evidence |
| Workbook recalculation | LibreOffice | One of | 24.2 or later | Record installed version | `soffice --version` |
| Conditional workload | Java Development Kit | Conditional for Java/JAR tasks or Java-based conversion tools | Version supported by the selected Databricks Runtime or tool; prefer 17 or 21 | Record selected version | `java -version` |
| Conditional package | dbt Core / Databricks adapter | Conditional when dbt tasks are selected | Pin in the approved package lock file and match the Databricks adapter compatibility matrix | Record locked version | `dbt --version` |
| Conditional infrastructure | Terraform and Databricks provider | Conditional when Terraform is the approved deployment route | Pin Terraform and provider versions in the package | Record locked versions | `terraform version` |
| Skill validation only | Node.js | Skill validation only | 22 or later | 24.15.0 | `node --version` |
| Skill validation only | npm | Skill validation only | 11.11.1 or later | 11.11.1 | `npm --version` |
| Skill validation only | PyYAML | Skill validation only | 6.0 or later, below 7.0 | Record installed version | `python -c "import yaml; print(yaml.__version__)"` |
| Skill validation only | Microsoft Vally CLI | Skill validation only | 0.13.0 | 0.13.0 | `npx --yes --ignore-scripts @microsoft/vally-cli@0.13.0 --version` |

`Skill validation only` rows support repository smoke and full-eval execution;
they are not customer migration-runtime prerequisites.

## Access and compatibility rows

Also add non-versioned rows for:

- approved Azure tenant/subscription context and read-only ADF or Synapse
  discovery scope;
- the correct authentication audience:
  `management.azure.com` for ADF ARM discovery and `dev.azuresynapse.net` for
  Synapse data-plane discovery;
- an approved Databricks workspace profile and least-privilege identity;
- outbound access required by approved package sources;
- an approved evidence folder outside the source service and Databricks
  workspace;
- an approved secret-handling path that stores references, never secret values;
- source and target network/private-endpoint reachability when live operations
  are approved.

Treat a missing required row, an incompatible version, failed authentication,
or an unavailable recalculation engine as `Blocked`. Do not install, upgrade,
authenticate, deploy, or change access without the corresponding approval.
