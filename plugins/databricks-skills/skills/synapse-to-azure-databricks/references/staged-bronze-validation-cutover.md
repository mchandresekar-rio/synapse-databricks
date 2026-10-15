# Staged Bronze validation, cutover, and rollback

Use this reference at every scenario-stage gate. Successful execution is not
semantic parity.

## Immutable gate record

Record stage, artifact hashes, predecessor `PASS` and progression approval,
coverage, test evidence, writer ownership before/during/after, schedule state,
separate approvals, rollback trigger/steps/owner/expiry, and verdict of
`PASS`, `FAIL`, or `BLOCKED`. A changed hash, target, path, mechanism, writer,
tolerance, or rollback boundary invalidates the affected approval.

## Minimum validation

- Stage 1: inventory, storage approval, schema, counts, nulls, duplicates,
  aggregates, partitions, permissions, unchanged ingestion, and no file change.
- Stage 2: syntax, dependency closure, semantic calculations, persisted
  outputs, incremental behavior, and deterministic rebuild.
- Stage 3: type/format prerequisites, before/after table state, schema, hashes,
  performance, downstream regression, and rollback.
- Stage 4: full/incremental/CDC, watermarks, replay, restart, duplicates,
  schema, concurrency, alerting, performance, and parallel-cycle comparison.

Use a shared revision, snapshot, or watermark and declare decimal, timestamp,
case/collation, whitespace, null, and nondeterminism rules. Missing or failed
queries are failures or blockers.

## Cutover and rollback

Keep schedules paused and the current writer active until target approval.
At cutover, freeze definitions, verify health and approvals, quiesce the
current writer, capture the final watermark, catch up, reconcile, transfer
ownership, activate only approved schedules, and move consumers in controlled
waves.

Rollback on agreed reconciliation, duplication, watermark, consumer,
authorization, SLA, restart, or cost breaches. Disable target writes, restore
the prior writer and routing, preserve evidence, and update the manifest
atomically. Never delete source files or decommission ADF/Synapse during
rollback.
