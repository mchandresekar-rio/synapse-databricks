# Conversion

## Notebook and Spark conversion

Preserve source cells and language boundaries while replacing Synapse-only APIs deliberately. Track each changed call in the migration manifest with its source location, target behavior, and validation method.

## Packaging

Prefer wheels, JARs, environment specifications, cluster policies, and Databricks Asset Bundles. Production artifacts must not depend on ad-hoc interactive state.

## SQL and pipelines

Treat SQL dialect conversion and orchestration conversion as semantic migrations. Unsupported transactions, procedures, workload controls, activities, triggers, or integration runtimes remain explicit blockers or retained components.

## Lakebridge conversion gate

Lakebridge assessment and Lakebridge conversion are separate decisions. A
successful Profiler or Analyzer run does not prove that a transpiler supports
the workload. Assessment support does not imply conversion support.

At the start of Phase 6:

1. Announce the conversion phase, work, exit criteria, and next gate.
2. Re-check the installed Lakebridge release and its current capability matrix
   for the exact source dialect, artifact types, constructs, and target.
3. Verify the conversion component with
   `databricks labs lakebridge transpile --help`. If it is unavailable, stop
   and ask before running
   `databricks labs lakebridge install-transpile`.
4. Treat `--include-llm-transpiler true` as a separate approval. Disclose LLM
   use, data handling, input scope, and generated-output review requirements.
5. Run an approved representative pilot before estate-wide conversion. Record
   configuration without secrets, source and output hashes, diagnostics,
   warnings, unsupported nodes, and semantic review results.
6. Expand Lakebridge conversion only after the pilot is approved. Record the
   route and converter evidence per artifact.
7. Route unsupported, ambiguous, partial, or failed artifacts through governed
   fallback only with the recorded fallback approval. Never guess converter
   flags or disguise the source dialect.

Keep source files immutable, retain reports and warnings, and place generated
output in a separate tree. Lakebridge-generated output remains a conversion
candidate until static, semantic, data-contract, and runtime validation pass.

Review these T-SQL areas explicitly:

| Source construct | Databricks review |
|---|---|
| Bracketed identifiers | Use valid unquoted names or backticks; preserve name mapping |
| `TOP` | Rewrite with `LIMIT` or a window and preserve deterministic ordering |
| `ISNULL` | Use an appropriate null function and verify type coercion |
| `GETDATE` and UTC functions | Preserve the declared time-zone contract |
| `DATEADD` and `DATEDIFF` | Test units, boundaries, return types, and overflow |
| `TRY_CAST` and `TRY_CONVERT` | Verify tolerant-cast and formatting behavior |
| `VARCHAR` and `NVARCHAR` | Validate Unicode, lengths, case, accents, and trailing spaces |
| `UNIQUEIDENTIFIER` | Select and validate a stable string or binary representation |
| JSON functions | Map to current JSON/variant functions and test missing paths |
| `CROSS APPLY` and `OUTER APPLY` | Select a lateral join or generator with matching null behavior |
| Dynamic SQL | Redesign around bound values and allowlisted identifiers |
| Temp tables and table variables | Use a CTE, temporary object, or staged Delta design deliberately |
| Stored procedures | Verify current SQL support or redesign as a job/notebook workflow |
| Cross-database names | Resolve through the approved fully qualified Unity Catalog registry |

Bind values as parameters. Resolve dynamic identifiers through an allowlist; never concatenate untrusted input into generated SQL.

## Artifact integrity

Hash source exports and generated artifacts. Deploy only reviewed artifacts whose hashes match the approved manifest.

Store assumptions, unsupported constructs, unresolved identifiers, converter diagnostics, and validation cases beside generated artifacts. Reject output that embeds secrets, fixed environment identifiers, unmanaged mounts, or raw storage access that bypasses approved Unity Catalog governance.
