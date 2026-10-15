# Staged Bronze stage 3: managed Delta upgrade

Start only after stage 2 is `PASS` and approved. This stage changes physical
ownership; it is not metadata-only.

## Current-product gate

Immediately before executable commands, verify current official Azure
Databricks documentation. Record URL, retrieval date, runtime, permissions,
object/format restrictions, limitations, rollback behavior, and selected
mechanism. Stale examples are not authorization.

## Decision rules

1. For an eligible Unity Catalog external Delta table whose current
   prerequisites pass, use only the currently documented conversion.
2. Reject direct `SET MANAGED` for Parquet. Use an approved governed
   Parquet-to-managed-Delta migration with schema, partitioning, catch-up,
   validation, switch, rollback, retention, and cost controls. This requires
   data-movement approval.
3. Route other formats, foreign tables, and Hive Metastore objects to their
   current object-specific process or classify them `redesign`, `retain`, or
   `blocker`.
4. Emit no executable conversion when a prerequisite, ownership transfer, or
   data movement is unapproved.

Never add `MOVE` or `COPY` to a Unity Catalog external-table `SET MANAGED`
operation.

## Scripts, ownership, and validation

Generate separate pre-conversion, conversion, post-conversion, and rollback
scripts. Preserve and validate names, grants, comments, properties,
dependencies, consumers, and approved rollback boundaries.

Keep the current `writer_ownership` after conversion; use `cutover-pending`
only while the table conversion is in progress. Stage 4 performs the writer
transfer to `databricks-owned`. Preserve original files through the rollback and
retention periods; never issue automatic `VACUUM` or cleanup.

Pass only when selected objects are managed Delta, evidence is complete,
Silver/Gold regressions pass, rollback remains available, cleanup is
separately governed, and no unapproved concurrent writer exists.

