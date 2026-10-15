from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.vally_ci import (
    CoverageError,
    MalformedResultError,
    NoResultsError,
    aggregate_shard_results,
    build_coverage_report,
    build_summary,
    classify_failure,
    compute_roi_verdict,
    detect_changed_skills,
    enforce_coverage,
    normalize_results,
    plan_weighted_shards,
    redact,
    redact_result_tree,
    select_specs,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_spec(
    root: Path,
    directory: str,
    skill: str,
    *,
    tier: str | None = None,
    eval_type: str = "integration",
) -> None:
    tags = {"scope": "offline", "type": eval_type, "skill": skill}
    if tier:
        tags["tier"] = tier
    target = root / directory
    target.mkdir(parents=True)
    (target / "eval.yaml").write_text(
        yaml.safe_dump(
            {
                "name": directory,
                "tags": tags,
                "stimuli": [{"name": "case", "prompt": "test", "tags": tags}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "suites": {
                    "smoke": {"filter": {"tier": "smoke"}},
                    "fulleval": {"filter": {"type": "fulleval"}},
                }
            }
        ),
        encoding="utf-8",
    )


def test_changed_skill_detection_is_normalized_filtered_and_sorted():
    paths = [
        r"skills\zeta\SKILL.md",
        "skills/alpha/references/guide.md",
        "./skills/alpha/scripts/run.py",
        "skills/deleted/SKILL.md",
        "skills/zeta/__pycache__/helper.pyc",
        "tests/evals/alpha/eval.yaml",
        "README.md",
    ]
    assert detect_changed_skills(paths, {"alpha", "zeta"}) == ["alpha", "zeta"]


def test_select_specs_matches_document_or_stimulus_suite_tags(tmp_path):
    eval_root = tmp_path / "tests" / "evals"
    config = tmp_path / ".vally.yaml"
    _write_config(config)
    _write_spec(eval_root, "alpha", "alpha", tier="smoke")
    _write_spec(eval_root, "alpha-fulleval", "alpha", eval_type="fulleval")
    _write_spec(eval_root, "beta", "beta", tier="smoke")

    smoke = select_specs(eval_root, ["alpha"], "smoke", config)
    full = select_specs(eval_root, ["alpha"], "fulleval", config)

    assert [item["eval_dir"] for item in smoke] == ["alpha"]
    assert [item["eval_dir"] for item in full] == ["alpha-fulleval"]
    assert all(item["skill"] == "alpha" for item in smoke + full)


def test_coverage_enforcement_reports_every_missing_suite():
    selected = {
        "smoke": [{"skill": "alpha"}, {"skill": "beta"}],
        "fulleval": [{"skill": "alpha"}],
    }
    with pytest.raises(CoverageError, match=r"beta: fulleval"):
        enforce_coverage(["alpha", "beta"], selected)

    report = enforce_coverage(["alpha"], selected)
    assert report["covered"] is True
    assert report["gaps"] == []


def test_weighted_sharding_is_deterministic_balanced_and_retains_metadata():
    items = [
        {"id": "small-b", "weight": 2, "eval_dir": "b"},
        {"id": "large", "weight": 7, "eval_dir": "large"},
        {"id": "small-a", "weight": 2, "eval_dir": "a"},
        {"id": "medium", "weight": 5, "eval_dir": "medium"},
    ]
    expected = plan_weighted_shards(items, 2)

    assert expected == plan_weighted_shards(reversed(items), 2)
    assert [shard["weight"] for shard in expected] == [9, 7]
    assert expected[0]["items"][1]["eval_dir"] == "b"
    assert sorted(item["id"] for shard in expected for item in shard["items"]) == sorted(
        item["id"] for item in items
    )


@pytest.mark.parametrize(
    "items,count,message",
    [
        ([{"id": "x", "weight": -1}], 1, "non-negative"),
        ([{"id": "x"}, {"id": "x"}], 1, "duplicate"),
        ([], 0, "at least 1"),
    ],
)
def test_weighted_sharding_rejects_invalid_input(items, count, message):
    with pytest.raises(ValueError, match=message):
        plan_weighted_shards(items, count)


def test_weighted_sharding_accepts_selection_json_and_counts_stimuli(tmp_path):
    eval_root = tmp_path / "evals"
    _write_spec(eval_root, "alpha", "alpha", tier="smoke")
    beta = eval_root / "beta"
    beta.mkdir(parents=True)
    (beta / "eval.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "beta",
                "stimuli": [
                    {"name": "one", "prompt": "one"},
                    {"name": "two", "prompt": "two"},
                    {"name": "three", "prompt": "three"},
                ],
            }
        ),
        encoding="utf-8",
    )
    selection = [
        {"path": str(eval_root / "alpha" / "eval.yaml"), "eval_dir": "alpha"},
        {"path": str(beta / "eval.yaml"), "eval_dir": "beta"},
    ]

    shards = plan_weighted_shards(selection, 2)

    assert [shard["weight"] for shard in shards] == [3, 1]
    assert shards[0]["items"][0]["id"] == "beta"
    assert shards[0]["items"][0]["eval_dir"] == "beta"
    assert shards[0]["items"][0]["weight"] == 3


def test_shard_aggregation_is_ordered_and_accumulates_metrics_and_failures():
    aggregate = aggregate_shard_results(
        [
            {
                "shard": 1,
                "results": [
                    {
                        "id": "b",
                        "passed": False,
                        "score": 0.25,
                        "duration_seconds": 4,
                        "tokens": 20,
                        "error": "threshold missed",
                    }
                ],
            },
            {
                "shard": 0,
                "results": [
                    {
                        "id": "a",
                        "passed": True,
                        "score": 1,
                        "duration_seconds": 3,
                        "tokens": 10,
                    }
                ],
            },
            {"shard": 2, "error": "runner unavailable"},
        ]
    )

    assert aggregate["passed"] is False
    assert aggregate["integrity_passed"] is False
    assert aggregate["shard_count"] == 3
    assert aggregate["case_count"] == 2
    assert aggregate["passed_count"] == 1
    assert aggregate["failed_count"] == 1
    assert aggregate["score"] == pytest.approx(0.625)
    assert aggregate["duration_seconds"] == 7
    assert aggregate["tokens"] == 30
    assert [result["id"] for result in aggregate["results"]] == ["a", "b"]
    assert len(aggregate["failures"]) == 2


def test_shard_aggregation_separates_grader_verdict_from_result_integrity():
    aggregate = aggregate_shard_results(
        [
            {
                "shard": 0,
                "results": [
                    {
                        "id": "grader-failure",
                        "passed": False,
                        "score": 0.8,
                        "error": "evaluation failed",
                    }
                ],
            }
        ]
    )

    assert aggregate["passed"] is False
    assert aggregate["integrity_passed"] is True


@pytest.mark.parametrize(
    "message,category,retryable",
    [
        ("HTTP 429: too many requests", "rate_limit", True),
        ("deadline exceeded", "timeout", True),
        ("401 Unauthorized: invalid token", "authentication", False),
        ("grader threshold missed", "assertion", False),
        ("connection reset by runner", "infrastructure", True),
        ("No eval specifications matched", "configuration", False),
        ("unexpected", "unknown", False),
    ],
)
def test_failure_classification(message, category, retryable):
    assert classify_failure(message, 1) == {
        "category": category,
        "retryable": retryable,
        "exit_code": 1,
    }


def test_recursive_redaction_handles_sensitive_keys_tokens_and_known_values():
    payload = {
        "Authorization": "Bearer should-not-survive",
        "nested": [
            {"message": "token=known-value and ghp_abcdefghijklmnopqrstuvwxyz"},
            ("eyJheader.payload.signature",),
        ],
        "safe": 4,
    }
    result = redact(payload, ["known-value"])

    assert result["Authorization"] == "[REDACTED]"
    assert "known-value" not in result["nested"][0]["message"]
    assert "ghp_" not in result["nested"][0]["message"]
    assert result["nested"][1] == ("[REDACTED]",)
    assert result["safe"] == 4


def test_summary_is_machine_readable_redacted_and_pr_ready():
    aggregate = {
        "passed": False,
        "case_count": 2,
        "passed_count": 1,
        "failed_count": 1,
        "score": 0.5,
        "duration_seconds": 8,
        "tokens": 50,
        "failures": [{"shard": 0, "id": "case-b", "error": "timeout secret-123"}],
    }
    roi = {"verdict": "negative", "reasons": ["score delta -0.500"]}
    machine, markdown = build_summary(
        aggregate, title="CAF full eval", roi=roi, secrets=["secret-123"]
    )

    assert json.loads(json.dumps(machine)) == machine
    assert machine["failures"][0]["category"] == "timeout"
    assert "secret-123" not in json.dumps(machine)
    assert "## CAF full eval: FAIL" in markdown
    assert "`timeout`" in markdown
    assert "Skill ROI" in markdown
    assert "secret-123" not in markdown


def test_normalizer_recurses_and_extracts_only_safe_contract_fields(tmp_path):
    first = tmp_path / "suite-a"
    second = tmp_path / "nested" / "suite-b"
    first.mkdir()
    second.mkdir(parents=True)
    (first / "results.jsonl").write_text(
        json.dumps(
            {
                "trajectory": {
                    "stimulus": {"id": "case-a", "prompt": "SECRET-PROMPT"},
                    "metrics": {
                        "durationSeconds": 1.25,
                        "tokenUsage": {"totalTokens": 42, "apiKey": "SECRET-TOKEN"},
                    },
                    "turns": [{"response": "SECRET-RESPONSE"}],
                },
                "gradeResult": {"passed": True, "score": {"value": 1}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (second / "results.jsonl").write_text(
        "\n"
        + json.dumps(
            {
                "trajectory": {
                    "stimulus": {"name": "case-b"},
                    "metrics": {
                        "durationMs": 2500,
                        "tokenUsage": {"inputTokens": 10, "outputTokens": 5},
                    },
                },
                "gradeResult": {
                    "score": 0,
                    "threshold": 1,
                    "error": "Bearer SECRET-BEARER timed out while transcript said SECRET",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    normalized = normalize_results(tmp_path, 7)

    assert normalized == {
        "shard": 7,
        "results": [
            {
                "id": "case-a",
                "passed": True,
                "score": 1.0,
                "duration_seconds": 1.25,
                "tokens": 42,
            },
            {
                "id": "case-b",
                "passed": False,
                "score": 0.0,
                "duration_seconds": 2.5,
                "tokens": 15,
                "error": "timeout failure",
            },
        ],
    }
    serialized = json.dumps(normalized)
    assert "SECRET" not in serialized
    assert "trajectory" not in serialized
    assert "gradeResult" not in serialized


def test_normalizer_reports_file_and_line_for_malformed_json_without_content(tmp_path):
    target = tmp_path / "run"
    target.mkdir()
    (target / "results.jsonl").write_text(
        '{"gradeResult":{"score":1,"passed":true}}\nSECRET malformed\n',
        encoding="utf-8",
    )

    with pytest.raises(MalformedResultError) as error:
        normalize_results(tmp_path, 0)

    assert "results.jsonl:2: malformed JSON" in str(error.value)
    assert "SECRET" not in str(error.value)


def test_normalizer_rejects_missing_or_empty_result_trees(tmp_path):
    with pytest.raises(NoResultsError, match="No Vally results found"):
        normalize_results(tmp_path, 0)
    empty = tmp_path / "empty" / "results.jsonl"
    empty.parent.mkdir()
    empty.write_text("\n", encoding="utf-8")
    with pytest.raises(NoResultsError, match="No Vally results found"):
        normalize_results(tmp_path, 0)


def test_normalizer_ignores_run_summary_and_uses_top_level_duration(tmp_path):
    result_file = tmp_path / "results.jsonl"
    rows = [
        {
            "type": "trial-result",
            "durationMs": 2500,
            "gradeResult": {"passed": True, "score": 1},
            "trajectory": {"stimulus": {"name": "case"}, "metrics": {}},
        },
        {
            "type": "run-summary",
            "passed": True,
            "evals": 1,
            "hadExecutionErrors": False,
        },
    ]
    result_file.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    normalized = normalize_results(tmp_path, 0)

    assert len(normalized["results"]) == 1
    assert normalized["results"][0]["id"] == "case"
    assert normalized["results"][0]["duration_seconds"] == 2.5


def test_normalize_cli_writes_json_artifact(tmp_path):
    result_dir = tmp_path / "raw"
    result_dir.mkdir()
    (result_dir / "results.jsonl").write_text(
        json.dumps(
            {
                "trajectory": {
                    "stimulus": "case",
                    "metrics": {"tokenUsage": {"total_tokens": 3}},
                },
                "gradeResult": {"passed": True, "score": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "shard.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.vally_ci",
            "normalize",
            "--results-root",
            str(result_dir),
            "--shard",
            "2",
            "--json-out",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert json.loads(output.read_text(encoding="utf-8"))["shard"] == 2


def test_aggregate_cli_accepts_precomputed_roi_and_title(tmp_path):
    shard = tmp_path / "shard.json"
    shard.write_text(
        json.dumps(
            {
                "shard": 0,
                "results": [
                    {
                        "id": "case",
                        "passed": True,
                        "score": 1,
                        "duration_seconds": 1,
                        "tokens": 2,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    roi = tmp_path / "roi.json"
    roi.write_text(
        json.dumps({"verdict": "positive", "reasons": ["score delta +1.000"]}),
        encoding="utf-8",
    )
    json_out = tmp_path / "summary.json"
    markdown_out = tmp_path / "summary.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.vally_ci",
            "aggregate",
            str(shard),
            "--roi",
            str(roi),
            "--title",
            "CAF evaluation",
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    machine = json.loads(json_out.read_text(encoding="utf-8"))
    assert machine["title"] == "CAF evaluation"
    assert machine["roi"]["verdict"] == "positive"
    markdown = markdown_out.read_text(encoding="utf-8")
    assert "## CAF evaluation: PASS" in markdown
    assert "**POSITIVE**" in markdown


def test_redact_result_tree_copies_only_safe_types_and_redacts_content(tmp_path):
    source = tmp_path / "raw"
    destination = tmp_path / "artifact"
    nested = source / "nested"
    nested.mkdir(parents=True)
    (source / "result.json").write_text(
        json.dumps(
            {
                "apiKey": "never-copy",
                "nested": {"message": "Bearer abcdefghijklmnop"},
                "safe": "retained",
            }
        ),
        encoding="utf-8",
    )
    (nested / "results.jsonl").write_text(
        json.dumps({"password": "never-copy", "value": 1})
        + "\n"
        + "malformed ghp_abcdefghijklmnopqrstuvwxyz\n",
        encoding="utf-8",
    )
    (source / "run.log").write_text(
        "request Authorization: Bearer abcdefghijklmnop\n", encoding="utf-8"
    )
    (source / "notes.txt").write_text(
        "eyJheader.payload.signature\n", encoding="utf-8"
    )
    (source / "raw.bin").write_bytes(b"\x00Bearer should-not-copy")
    (source / "config.yaml").write_text("token: should-not-copy\n", encoding="utf-8")

    receipt = redact_result_tree(source, destination)

    assert receipt["copied"] == [
        "nested/results.jsonl",
        "notes.txt",
        "result.json",
        "run.log",
    ]
    assert not (destination / "raw.bin").exists()
    assert not (destination / "config.yaml").exists()
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in destination.rglob("*")
        if path.is_file()
    )
    for secret in (
        "never-copy",
        "ghp_abcdefghijklmnopqrstuvwxyz",
        "abcdefghijklmnop",
        "eyJheader.payload.signature",
    ):
        assert secret not in combined
    assert '"apiKey": "[REDACTED]"' in combined
    assert "malformed [REDACTED]" in combined
    assert "retained" in combined


def test_redact_result_tree_rejects_output_nested_under_input(tmp_path):
    source = tmp_path / "raw"
    source.mkdir()
    with pytest.raises(ValueError, match="must not be nested"):
        redact_result_tree(source, source / "artifact")


def test_roi_verdict_distinguishes_quality_gain_neutral_and_cost_regression():
    baseline = {
        "case_count": 4,
        "passed_count": 2,
        "score": 0.5,
        "duration_seconds": 100,
        "tokens": 1000,
    }
    positive = compute_roi_verdict(
        baseline,
        {
            "case_count": 4,
            "passed_count": 4,
            "score": 0.9,
            "duration_seconds": 110,
            "tokens": 1100,
        },
    )
    neutral = compute_roi_verdict(baseline, baseline)
    expensive = compute_roi_verdict(
        baseline,
        {
            "case_count": 4,
            "passed_count": 4,
            "score": 0.9,
            "duration_seconds": 200,
            "tokens": 2000,
        },
    )

    assert positive["verdict"] == "positive"
    assert positive["quality_gate_passed"] is True
    assert positive["cost_gate_passed"] is True
    assert positive["deltas"]["pass_rate"] == pytest.approx(0.5)
    assert neutral["verdict"] == "neutral"
    assert expensive["verdict"] == "negative"
    assert expensive["cost_gate_passed"] is False


def test_coverage_gap_report_finds_missing_and_orphan_specs(tmp_path):
    skill_root = tmp_path / "skills"
    eval_root = tmp_path / "evals"
    for skill in ("alpha", "beta"):
        target = skill_root / skill
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    _write_spec(eval_root, "alpha", "alpha", tier="smoke")
    _write_spec(eval_root, "alpha-full", "alpha", eval_type="fulleval")
    _write_spec(eval_root, "gone", "gone", tier="smoke")

    report, markdown = build_coverage_report(skill_root, eval_root)

    assert report["skill_count"] == 2
    assert report["covered_skill_count"] == 1
    assert report["gaps"] == [{"skill": "beta", "missing_suites": ["smoke", "fulleval"]}]
    assert report["orphan_specs"] == ["gone"]
    assert "| alpha | yes | yes | — |" in markdown
    assert "| beta | no | no | smoke, fulleval |" in markdown


def test_cli_select_contract_returns_eval_dirs_accepted_by_powershell_runner():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.vally_ci",
            "select",
            "--eval-root",
            str(ROOT / "tests/evals"),
            "--config",
            str(ROOT / ".vally.yaml"),
            "--skills",
            "synapse-to-azure-databricks",
            "--suite",
            "smoke",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert [item["eval_dir"] for item in json.loads(result.stdout)] == [
        "synapse-to-azure-databricks"
    ]
