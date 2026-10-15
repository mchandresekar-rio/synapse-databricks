# Vally evaluations

- `tests/evals/<skill>/eval.yaml` contains bundle-routing smoke coverage.
- `tests/evals/<skill>-fulleval/eval.yaml` contains multi-turn behavioral coverage.
- Smoke specifications omit `environment.skills` so the runner supplies the complete built plugin bundle and routing competes against sibling skills.
- Offline migration evals must not require Azure credentials or mutate cloud resources.
- The `live-databricks` suite is reserved until protected infrastructure and cleanup are implemented.

Run staging without token use:

    pwsh ./tests/run-vally-eval.ps1 -Suite smoke -DryRun

Run one eval directory:

    pwsh ./tests/run-vally-eval.ps1 -Skill synapse-to-azure-databricks -Runs 1

## CI reliability helpers

The repository-local `tests.vally_ci` module provides deterministic helpers without
requiring another skills repository. Its JSON is intended for workflow matrices and
artifacts; generated Markdown is suitable for job summaries and PR comments.

```powershell
# Detect materially changed skills from a three-dot Git diff.
python -m tests.vally_ci changed-skills --base origin/main --head HEAD

# Select spec directories using the same .vally.yaml suite filters as the runner.
python -m tests.vally_ci select --skills synapse-to-azure-databricks --suite smoke

# Select both tiers and fail when a changed skill lacks either tier.
python -m tests.vally_ci select-changed --skills synapse-to-azure-databricks

# Generate machine-readable and Markdown coverage-gap reports.
python -m tests.vally_ci coverage `
  --json-out tests/.vally-results/coverage.json `
  --markdown-out tests/.vally-results/coverage.md

# Plan stable weighted shards from explicit weights or `select` output.
python -m tests.vally_ci plan-shards --input items.json --count 4

# Aggregate normalized shard files and produce redacted summaries.
python -m tests.vally_ci aggregate shard-0.json shard-1.json `
  --roi tests/.vally-results/roi.json `
  --title "CAF full evaluation" `
  --json-out tests/.vally-results/summary.json `
  --markdown-out tests/.vally-results/summary.md

# Normalize all recursive Vally 0.13.0 results.jsonl files for one shard.
python -m tests.vally_ci normalize `
  --results-root tests/.vally-results/raw `
  --shard 0 `
  --json-out tests/.vally-results/shard-0.json

# Copy only supported text results into a recursively redacted artifact tree.
python -m tests.vally_ci redact-tree `
  --input tests/.vally-results/raw `
  --output tests/.vally-results/redacted-artifact

# Compare normalized baseline and with-skill aggregate metrics.
python -m tests.vally_ci roi --baseline baseline.json --skill skill.json
```

Selection output includes `eval_dir`; join these values with commas for
`run-vally-eval.ps1 -EvalDirs`. `plan-shards` keeps the explicit
`{"id": "...", "weight": 1}` contract and also accepts selection entries with
`path` and `eval_dir`, deriving weight from the YAML stimulus count. Shard result inputs use
`{"shard": 0, "results": [{"id": "...", "passed": true, "score": 1,
"duration_seconds": 1, "tokens": 100}]}` and may instead contain a shard-level
`error`. Baseline and skill metrics accept `case_count`, `passed_count`, `score`,
`duration_seconds`, and `tokens`.

Normalization reads every recursive `results.jsonl`, rejects malformed lines and
empty result trees, and emits only stimulus identity, grade, duration, token count,
and a classified failure label. It intentionally drops trajectories, prompts,
responses, tool calls, and raw error text.

`aggregate --roi` includes a precomputed ROI object in both summaries, while
`--title` sets their heading/title. `redact-tree` copies only `.json`, `.jsonl`,
`.log`, and `.txt` files, recursively redacts JSON sensitive keys and common token
patterns, redacts malformed JSONL as text, skips symlinks and unknown/binary files,
and rejects an output path nested under its input.

GitHub Actions grants the smoke, full-eval, and model-watch workflows
`copilot-requests: write` and uses the scoped workflow token by default. A
`COPILOT_GITHUB_TOKEN` repository or organization secret may override that route
when policy requires a dedicated credential. Neither credential is written to
results or uploaded artifacts.

Smoke and full-eval result integrity is always blocking: missing, malformed, or
incomplete shard results fail the workflow. Grader verdicts remain
informational during initial calibration and are still published to the job
summary and pull request. Set the repository variable
`VALLY_ENFORCE_VERDICT=true` only after the suites are calibrated to promote
grader failures to merge-blocking checks.
