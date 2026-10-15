# Staged Bronze stage 1: read-only external registration

Recreate existing Synapse Bronze metadata in Unity Catalog without changing
ADLS data or its writer.

## Discover and classify

Use immutable exports or approved read-only discovery. Capture stable IDs,
definition hashes, format, credential-free URI, path/glob and partition
semantics, ordered schema, producer, writer, refresh/watermark, consumers,
lineage, and approved storage mapping.

Classify physical external tables separately from simple access wrappers,
business-logic views, generated objects, and ambiguous objects. Register
physical tables; collapse simple wrappers into clear contracts; route
transformations to stage 2; classify unsupported behavior as `redesign`,
`retain`, or `blocker`.

## Controls

- Require approval for the no-copy design, credential, narrow external
  location, three-part name, and grants before metadata deployment.
- Use explicit, format-appropriate DDL and preserve compatible schema and
  partitions.
- Record `writer_ownership` as `synapse-owned` or `adf-owned` and
  `data_action` as `register-existing`.
- Do not write, optimize, compact, convert, repair, vacuum, copy, move, delete,
  rename, or rewrite source files.
- Keep existing ADF/Synapse ingestion as the only writer.

## Validate and exit

At a shared snapshot or watermark, validate metadata, schema, partitions,
counts, nulls, keys, duplicates, aggregates, representative queries, grants,
write denial, continued ingestion, and evidence that no file changed.

Pass only when all objects are inventoried and classified, storage mappings
are approved, tables query successfully, reconciliation passes, ingestion and
files remain unchanged, and stage 2 progression approval is recorded.

