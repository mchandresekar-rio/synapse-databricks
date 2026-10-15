from __future__ import annotations

import json
from pathlib import Path

from .reporting import classify_failure


class NormalizationError(ValueError):
    """Base error for invalid or absent Vally result data."""


class MalformedResultError(NormalizationError):
    """Raised when a results.jsonl line is not a usable Vally result."""


class NoResultsError(NormalizationError):
    """Raised when no Vally result records are found."""


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("value", "score", "total"):
            parsed = _number(value.get(key))
            if parsed is not None:
                return parsed
    return None


def _stimulus_id(record: dict, source: Path, line_number: int) -> str:
    trajectory = record.get("trajectory") or {}
    stimulus = trajectory.get("stimulus")
    if isinstance(stimulus, str) and stimulus.strip():
        return stimulus.strip()
    if isinstance(stimulus, dict):
        for key in ("id", "name", "key", "title"):
            value = stimulus.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("id", "name"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{source.parent.name}:{line_number}"


def _grade(record: dict, source: Path, line_number: int) -> tuple[bool, float, str | None]:
    grade = record.get("gradeResult")
    if not isinstance(grade, dict):
        raise MalformedResultError(
            f"{source}:{line_number}: gradeResult must be an object"
        )
    score = None
    for key in ("score", "totalScore", "reward"):
        score = _number(grade.get(key))
        if score is not None:
            break
    if score is None:
        raise MalformedResultError(
            f"{source}:{line_number}: gradeResult has no numeric score"
        )

    passed = grade.get("passed")
    if not isinstance(passed, bool):
        passed = grade.get("success")
    if not isinstance(passed, bool):
        threshold = _number(grade.get("threshold"))
        if threshold is None:
            raise MalformedResultError(
                f"{source}:{line_number}: gradeResult has no boolean passed value"
            )
        passed = score >= threshold

    error = None
    if not passed:
        raw_error = grade.get("error") or record.get("error")
        if raw_error:
            category = classify_failure(str(raw_error))["category"]
            error = f"{category} failure"
    return passed, score, error


def _duration_seconds(record: dict) -> float:
    metrics = ((record.get("trajectory") or {}).get("metrics") or {})
    for key in ("durationSeconds", "duration_seconds", "wallTimeSeconds"):
        value = _number(metrics.get(key))
        if value is not None:
            return value
    for key in ("durationMs", "duration_ms", "wallTimeMs"):
        value = _number(metrics.get(key))
        if value is not None:
            return value / 1000
    for key in ("durationMs", "duration_ms"):
        value = _number(record.get(key))
        if value is not None:
            return value / 1000
    return 0.0


def _tokens(record: dict) -> int:
    metrics = ((record.get("trajectory") or {}).get("metrics") or {})
    usage = metrics.get("tokenUsage") or metrics.get("token_usage") or {}
    if not isinstance(usage, dict):
        return 0
    for key in ("totalTokens", "total_tokens", "total"):
        total = _number(usage.get(key))
        if total is not None:
            return int(total)
    input_tokens = next(
        (
            value
            for key in ("inputTokens", "input_tokens", "promptTokens", "prompt_tokens")
            if (value := _number(usage.get(key))) is not None
        ),
        0,
    )
    output_tokens = next(
        (
            value
            for key in (
                "outputTokens",
                "output_tokens",
                "completionTokens",
                "completion_tokens",
            )
            if (value := _number(usage.get(key))) is not None
        ),
        0,
    )
    return int(input_tokens + output_tokens)


def normalize_results(results_root: Path, shard: int) -> dict:
    """Normalize all recursive Vally 0.13.0 results.jsonl records for one shard.

    Only scalar grade and metric fields are retained. Prompts, responses, tool
    calls, trajectories, and raw failure text are intentionally discarded.
    """

    if shard < 0:
        raise ValueError("shard must be non-negative")
    files = sorted(results_root.rglob("results.jsonl"))
    results: list[dict] = []
    for source in files:
        with source.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise MalformedResultError(
                        f"{source}:{line_number}: malformed JSON ({exc.msg})"
                    ) from exc
                if not isinstance(record, dict):
                    raise MalformedResultError(
                        f"{source}:{line_number}: result must be a JSON object"
                    )
                if record.get("type") == "run-summary":
                    continue
                passed, score, error = _grade(record, source, line_number)
                normalized = {
                    "id": _stimulus_id(record, source, line_number),
                    "passed": passed,
                    "score": score,
                    "duration_seconds": _duration_seconds(record),
                    "tokens": _tokens(record),
                }
                if error:
                    normalized["error"] = error
                results.append(normalized)
    if not results:
        raise NoResultsError(f"No Vally results found under {results_root}")
    results.sort(key=lambda item: item["id"])
    return {"shard": shard, "results": results}
