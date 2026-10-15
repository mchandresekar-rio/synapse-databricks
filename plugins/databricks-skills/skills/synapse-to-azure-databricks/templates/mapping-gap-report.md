# Discovery and Mapping-Gap Report

## Run context

- Migration scope:
- Source workspace/endpoint and databases:
- Target workspace/catalog policy:
- Timestamp and environment:
- Tool names and versions:
- Lakebridge component/version or fallback reason:
- Evidence directory:

## Input evidence

| Input | Type | Revision/environment | Size | SHA-256 | Status |
|---|---|---|---:|---|---|
| | SQL project, ZIP, DACPAC, SQL export, catalog, or scope list | | | | |

## Coverage

| Category | Expected | Artifact | Deployed | Mapped/dispositioned | Not verified |
|---|---:|---:|---:|---:|---:|
| Databases and schemas | | | | | |
| Views, functions, and procedures | | | | | |
| External tables, sources, and formats | | | | | |
| Storage paths and dependencies | | | | | |
| Identities and permissions | | | | | |
| Consumers | | | | | |
| Pipelines, schedules, and control metadata | | | | | |
| Persisted facts/dimensions and serving views | | | | | |
| Writer ownership, watermarks, and restart contracts | | | | | |

## Compatibility classification summary

| Classification | Count | Notes |
|---|---:|---|
| direct | | |
| rewrite | | |
| redesign | | |
| retain | | |
| blocker | | |

## Migration disposition summary

| Disposition | Count | Notes |
|---|---:|---|
| migrate | | |
| retain | | |
| park | | |
| retire | | |

## Workflow status summary

| Status | Count | Notes |
|---|---:|---|
| inventoried | | |
| assessed | | |
| fallback-required | | |
| approved | | |
| converted | | |
| deployed | | |
| validated | | |
| failed | | |
| retained | | |
| blocked | | |
| rolled-back | | |

## Gaps

When none exist, state **NO MAPPING GAPS DETECTED**.

| Gap ID | Severity | Gap type | Source key | Target key | Evidence | Impact/action | Owner | Expiry | Status |
|---|---|---|---|---|---|---|---|---|---|
| GAP-001 | blocker/warning/info | | database.schema.object, path, identity, or consumer | catalog.schema.object or location | | | | | open |

## Dependencies and collisions

| Item | Missing dependency or colliding sources | Proposed resolution | Approval evidence | Owner | Status |
|---|---|---|---|---|---|
| | | | | | |

## Definition drift

| Source key | Artifact evidence | Deployed evidence | Material difference | Authoritative revision | Status |
|---|---|---|---|---|---|
| | | | | | |

## Checks not run

| Check | Missing prerequisite | Affected scope | Next action | Owner |
|---|---|---|---|---|
| | | | | |

## Gate

- Unresolved blockers:
- Approved exceptions and expiry:
- Mapping coverage:
- Conversion gate: `PASS` or `BLOCKED`
- Decision owner/date:
