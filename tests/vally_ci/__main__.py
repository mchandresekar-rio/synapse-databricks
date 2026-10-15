from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .artifacts import redact_result_tree
from .coverage import build_coverage_report
from .normalize import normalize_results
from .reporting import build_summary
from .roi import compute_roi_verdict
from .selection import detect_changed_skills, enforce_coverage, select_specs
from .sharding import aggregate_shard_results, plan_weighted_shards


def _read_json(path: str) -> dict | list:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_outputs(data: dict, markdown: str | None, args) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if getattr(args, "json_out", None):
        Path(args.json_out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if markdown is not None and getattr(args, "markdown_out", None):
        Path(args.markdown_out).write_text(markdown, encoding="utf-8")


def _changed_files(repo: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description="CAF-native Vally CI reliability helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    changed = sub.add_parser("changed-skills")
    changed.add_argument("--repo", type=Path, default=Path.cwd())
    changed.add_argument("--base", required=True)
    changed.add_argument("--head", default="HEAD")

    select = sub.add_parser("select")
    select.add_argument("--eval-root", type=Path, default=Path("tests/evals"))
    select.add_argument("--config", type=Path, default=Path(".vally.yaml"))
    select.add_argument("--skills", required=True, help="Comma-separated skill names")
    select.add_argument("--suite", choices=("smoke", "fulleval"), required=True)

    select_changed = sub.add_parser(
        "select-changed",
        help="Select smoke/full specs and enforce coverage for changed skills",
    )
    select_changed.add_argument("--eval-root", type=Path, default=Path("tests/evals"))
    select_changed.add_argument("--config", type=Path, default=Path(".vally.yaml"))
    select_changed.add_argument("--skills", required=True, help="Comma-separated skill names")

    coverage = sub.add_parser("coverage")
    coverage.add_argument("--skill-root", type=Path, default=Path("skills"))
    coverage.add_argument("--eval-root", type=Path, default=Path("tests/evals"))
    coverage.add_argument("--json-out")
    coverage.add_argument("--markdown-out")

    shards = sub.add_parser("plan-shards")
    shards.add_argument("--input", required=True, help="JSON array of {id, weight}")
    shards.add_argument("--count", type=int, required=True)

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("inputs", nargs="+", help="Shard JSON files")
    aggregate.add_argument("--json-out")
    aggregate.add_argument("--markdown-out")
    aggregate.add_argument("--roi", help="Precomputed ROI JSON")
    aggregate.add_argument("--title", default="Vally evaluation")

    normalize = sub.add_parser(
        "normalize",
        help="Normalize recursive Vally 0.13.0 results.jsonl files",
    )
    normalize.add_argument("--results-root", type=Path, required=True)
    normalize.add_argument("--shard", type=int, required=True)
    normalize.add_argument("--json-out", required=True)

    redact_tree = sub.add_parser(
        "redact-tree",
        help="Create a redacted JSON/JSONL/log/text artifact tree",
    )
    redact_tree.add_argument("--input", type=Path, required=True)
    redact_tree.add_argument("--output", type=Path, required=True)

    roi = sub.add_parser("roi")
    roi.add_argument("--baseline", required=True)
    roi.add_argument("--skill", required=True)

    args = parser.parse_args()
    if args.command == "changed-skills":
        known = [path.parent.name for path in (args.repo / "skills").glob("*/SKILL.md")]
        print(json.dumps(detect_changed_skills(_changed_files(args.repo, args.base, args.head), known)))
    elif args.command == "select":
        skills = [value.strip() for value in args.skills.split(",") if value.strip()]
        print(json.dumps(select_specs(args.eval_root, skills, args.suite, args.config), indent=2))
    elif args.command == "select-changed":
        skills = [value.strip() for value in args.skills.split(",") if value.strip()]
        selected = {
            suite: select_specs(args.eval_root, skills, suite, args.config)
            for suite in ("smoke", "fulleval")
        }
        coverage_report = enforce_coverage(skills, selected)
        print(json.dumps({**selected, "coverage": coverage_report}, indent=2))
    elif args.command == "coverage":
        report, markdown = build_coverage_report(args.skill_root, args.eval_root)
        _write_outputs(report, markdown, args)
    elif args.command == "plan-shards":
        print(json.dumps(plan_weighted_shards(_read_json(args.input), args.count), indent=2))
    elif args.command == "aggregate":
        result = aggregate_shard_results(_read_json(path) for path in args.inputs)
        roi_result = _read_json(args.roi) if args.roi else None
        machine, markdown = build_summary(result, title=args.title, roi=roi_result)
        _write_outputs(machine, markdown, args)
    elif args.command == "normalize":
        output = normalize_results(args.results_root, args.shard)
        _write_outputs(output, None, args)
    elif args.command == "redact-tree":
        print(json.dumps(redact_result_tree(args.input, args.output), indent=2))
    elif args.command == "roi":
        print(json.dumps(compute_roi_verdict(_read_json(args.baseline), _read_json(args.skill)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
