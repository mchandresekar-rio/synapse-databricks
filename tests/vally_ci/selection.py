from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path, PurePosixPath

import yaml


class CoverageError(ValueError):
    """Raised when a materially changed skill lacks required evaluation coverage."""


def _normalized_parts(path: str | Path) -> tuple[str, ...]:
    return PurePosixPath(str(path).replace("\\", "/").lstrip("./")).parts


def detect_changed_skills(
    changed_paths: Iterable[str | Path],
    known_skills: Iterable[str] | None = None,
) -> list[str]:
    """Return sorted skill names changed below skills/<name>/.

    Deleted skills are ignored when ``known_skills`` is supplied. Generated caches
    and editor files do not constitute material skill changes.
    """

    known = set(known_skills) if known_skills is not None else None
    ignored_names = {".DS_Store", "Thumbs.db"}
    changed: set[str] = set()
    for path in changed_paths:
        parts = _normalized_parts(path)
        if len(parts) < 3 or parts[0] != "skills":
            continue
        if any(part in {"__pycache__", ".pytest_cache"} for part in parts):
            continue
        if parts[-1] in ignored_names or parts[-1].endswith((".pyc", ".tmp", "~")):
            continue
        skill = parts[1]
        if known is None or skill in known:
            changed.add(skill)
    return sorted(changed)


def _matches_filter(document: dict, filters: dict) -> bool:
    tags = document.get("tags") or {}
    if all(tags.get(key) == value for key, value in filters.items()):
        return True
    return any(
        all((stimulus.get("tags") or {}).get(key) == value for key, value in filters.items())
        for stimulus in document.get("stimuli") or []
    )


def discover_specs(eval_root: Path) -> list[dict]:
    specs: list[dict] = []
    for path in sorted(eval_root.glob("*/eval.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        skill = (document.get("tags") or {}).get("skill")
        if not skill:
            stimulus_skills = {
                (stimulus.get("tags") or {}).get("skill")
                for stimulus in document.get("stimuli") or []
            }
            stimulus_skills.discard(None)
            if len(stimulus_skills) == 1:
                skill = stimulus_skills.pop()
        specs.append(
            {
                "path": path,
                "eval_dir": path.parent.name,
                "skill": skill,
                "document": document,
            }
        )
    return specs


def select_specs(
    eval_root: Path,
    skills: Iterable[str],
    suite: str,
    vally_config: Path | None = None,
) -> list[dict]:
    """Select specs using the same suite-filter semantics as run-vally-eval.ps1."""

    selected_skills = set(skills)
    config_path = vally_config or eval_root.parents[1] / ".vally.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    filters = ((config.get("suites") or {}).get(suite) or {}).get("filter") or {}
    selected = []
    for spec in discover_specs(eval_root):
        if selected_skills and spec["skill"] not in selected_skills:
            continue
        if filters and not _matches_filter(spec["document"], filters):
            continue
        selected.append(
            {
                "path": str(spec["path"]),
                "eval_dir": spec["eval_dir"],
                "skill": spec["skill"],
                "suite": suite,
            }
        )
    return selected


def enforce_coverage(
    changed_skills: Iterable[str],
    selected_by_suite: dict[str, Iterable[dict]],
    required_suites: Iterable[str] = ("smoke", "fulleval"),
) -> dict:
    """Require every changed skill to have a selected spec in each required suite."""

    changed = sorted(set(changed_skills))
    required = list(required_suites)
    covered = {
        suite: {item.get("skill") for item in selected_by_suite.get(suite, [])}
        for suite in required
    }
    gaps = [
        {"skill": skill, "missing_suites": [suite for suite in required if skill not in covered[suite]]}
        for skill in changed
    ]
    gaps = [gap for gap in gaps if gap["missing_suites"]]
    report = {
        "changed_skills": changed,
        "required_suites": required,
        "covered": not gaps,
        "gaps": gaps,
    }
    if gaps:
        details = "; ".join(
            f"{gap['skill']}: {', '.join(gap['missing_suites'])}" for gap in gaps
        )
        raise CoverageError(f"Evaluation coverage is incomplete ({details})")
    return report
