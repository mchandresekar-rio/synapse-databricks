from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

import yaml


def _selection_weight(item: dict) -> float:
    if "weight" in item:
        return float(item["weight"])
    path = item.get("path")
    if not path:
        return 1.0
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return float(len(document.get("stimuli") or []))


def plan_weighted_shards(items: Iterable[dict], shard_count: int) -> list[dict]:
    """Plan deterministic LPT shards, minimizing the heaviest shard."""

    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    normalized = []
    seen: set[str] = set()
    for item in items:
        item_id_value = item.get("id") or item.get("eval_dir")
        if not item_id_value:
            raise ValueError("each item requires id or eval_dir")
        item_id = str(item_id_value)
        weight = _selection_weight(item)
        if item_id in seen:
            raise ValueError(f"duplicate item id: {item_id}")
        if weight < 0:
            raise ValueError(f"weight must be non-negative: {item_id}")
        seen.add(item_id)
        normalized.append({"id": item_id, "weight": weight, **deepcopy(item)})

    shards = [{"index": index, "weight": 0.0, "items": []} for index in range(shard_count)]
    for item in sorted(normalized, key=lambda entry: (-entry["weight"], entry["id"])):
        shard = min(shards, key=lambda entry: (entry["weight"], entry["index"]))
        shard["items"].append(item)
        shard["weight"] += item["weight"]
    return shards


def aggregate_shard_results(shards: Iterable[dict]) -> dict:
    """Aggregate normalized shard outputs and retain per-case failure evidence."""

    ordered = sorted(deepcopy(list(shards)), key=lambda item: item.get("shard", 0))
    cases: list[dict] = []
    failures: list[dict] = []
    shard_errors: list[dict] = []
    for shard in ordered:
        shard_id = shard.get("shard")
        if shard.get("error"):
            shard_error = {"shard": shard_id, "id": None, "error": shard["error"]}
            failures.append(shard_error)
            shard_errors.append(shard_error)
        for result in shard.get("results") or []:
            case = {"shard": shard_id, **result}
            cases.append(case)
            if not result.get("passed", False):
                failures.append(
                    {
                        "shard": shard_id,
                        "id": result.get("id"),
                        "error": result.get("error") or "evaluation failed",
                    }
                )

    passed = sum(1 for case in cases if case.get("passed", False))
    scores = [float(case["score"]) for case in cases if case.get("score") is not None]
    durations = [float(case.get("duration_seconds", 0)) for case in cases]
    tokens = [int(case.get("tokens", 0)) for case in cases]
    return {
        "schema_version": 1,
        "passed": not failures,
        "integrity_passed": bool(cases) and not shard_errors,
        "shard_count": len(ordered),
        "case_count": len(cases),
        "passed_count": passed,
        "failed_count": len(cases) - passed,
        "score": sum(scores) / len(scores) if scores else None,
        "duration_seconds": sum(durations),
        "tokens": sum(tokens),
        "failures": failures,
        "results": cases,
    }
