from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .selection import discover_specs


def build_coverage_report(
    skill_root: Path,
    eval_root: Path,
    required_suites: Iterable[str] = ("smoke", "fulleval"),
) -> tuple[dict, str]:
    """Build machine-readable and Markdown coverage-gap reports."""

    required = list(required_suites)
    skills = sorted(path.parent.name for path in skill_root.glob("*/SKILL.md"))
    coverage = {skill: {suite: [] for suite in required} for skill in skills}
    orphan_specs: list[str] = []
    for spec in discover_specs(eval_root):
        document = spec["document"]
        tags = document.get("tags") or {}
        suites = []
        if tags.get("tier") == "smoke" or any(
            (stimulus.get("tags") or {}).get("tier") == "smoke"
            for stimulus in document.get("stimuli") or []
        ):
            suites.append("smoke")
        if tags.get("type") == "fulleval" or any(
            (stimulus.get("tags") or {}).get("type") == "fulleval"
            for stimulus in document.get("stimuli") or []
        ):
            suites.append("fulleval")
        if spec["skill"] not in coverage:
            orphan_specs.append(spec["eval_dir"])
            continue
        for suite in suites:
            if suite in coverage[spec["skill"]]:
                coverage[spec["skill"]][suite].append(spec["eval_dir"])

    gaps = [
        {"skill": skill, "missing_suites": [suite for suite in required if not suites[suite]]}
        for skill, suites in coverage.items()
    ]
    gaps = [gap for gap in gaps if gap["missing_suites"]]
    report = {
        "schema_version": 1,
        "skill_count": len(skills),
        "covered_skill_count": len(skills) - len(gaps),
        "required_suites": required,
        "coverage": coverage,
        "gaps": gaps,
        "orphan_specs": sorted(orphan_specs),
    }
    lines = [
        "# Evaluation coverage gaps",
        "",
        f"Covered **{report['covered_skill_count']} of {report['skill_count']}** skills.",
        "",
        "| Skill | Smoke | Full eval | Missing |",
        "|---|---|---|---|",
    ]
    gap_map = {gap["skill"]: gap["missing_suites"] for gap in gaps}
    for skill in skills:
        lines.append(
            f"| {skill} | {'yes' if coverage[skill].get('smoke') else 'no'} | "
            f"{'yes' if coverage[skill].get('fulleval') else 'no'} | "
            f"{', '.join(gap_map.get(skill, [])) or '—'} |"
        )
    if orphan_specs:
        lines.extend(["", "Orphan specs: " + ", ".join(sorted(orphan_specs))])
    return report, "\n".join(lines) + "\n"
