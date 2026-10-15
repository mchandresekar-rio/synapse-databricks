from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy


SENSITIVE_KEY = re.compile(
    r"(?i)(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|credential)"
)
TOKEN_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
)


def _redact_string(value: str, secrets: Sequence[str]) -> str:
    redacted = value
    for secret in sorted((secret for secret in secrets if secret), key=len, reverse=True):
        redacted = redacted.replace(secret, "[REDACTED]")
    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact(value, secrets: Sequence[str] = ()):
    """Recursively redact sensitive keys, known secret values, and common tokens."""

    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]" if SENSITIVE_KEY.search(str(key)) else redact(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item, secrets) for item in value)
    if isinstance(value, str):
        return _redact_string(value, secrets)
    return value


def classify_failure(message: str, exit_code: int | None = None) -> dict:
    text = message.lower()
    classifications = (
        ("authentication", ("unauthorized", "forbidden", "authentication", "invalid token"), False),
        ("rate_limit", ("rate limit", "too many requests", "429"), True),
        ("timeout", ("timed out", "timeout", "deadline exceeded"), True),
        ("configuration", ("no eval specifications", "unresolved token", "invalid config", "schema"), False),
        ("assertion", ("grader", "threshold", "assertion", "evaluation failed"), False),
        ("infrastructure", ("connection reset", "service unavailable", "runner", "econnreset"), True),
    )
    for category, markers, retryable in classifications:
        if any(marker in text for marker in markers):
            return {"category": category, "retryable": retryable, "exit_code": exit_code}
    return {"category": "unknown", "retryable": False, "exit_code": exit_code}


def build_summary(
    aggregate: dict,
    *,
    title: str = "Vally evaluation",
    roi: dict | None = None,
    secrets: Sequence[str] = (),
) -> tuple[dict, str]:
    """Return a redacted JSON-compatible summary and PR-ready Markdown."""

    machine = redact(deepcopy(aggregate), secrets)
    machine["schema_version"] = 1
    machine["title"] = title
    classified = []
    for failure in machine.get("failures") or []:
        classified.append({**failure, **classify_failure(str(failure.get("error", "")))})
    machine["failures"] = classified
    if roi is not None:
        machine["roi"] = redact(deepcopy(roi), secrets)

    status = "PASS" if machine.get("passed") else "FAIL"
    score = machine.get("score")
    score_text = "n/a" if score is None else f"{score:.3f}"
    lines = [
        f"## {title}: {status}",
        "",
        "| Cases | Passed | Failed | Score | Duration (s) | Tokens |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            f"| {machine.get('case_count', 0)} | {machine.get('passed_count', 0)} | "
            f"{machine.get('failed_count', 0)} | {score_text} | "
            f"{machine.get('duration_seconds', 0):.1f} | {machine.get('tokens', 0)} |"
        ),
    ]
    if classified:
        lines.extend(["", "### Failures", ""])
        for failure in classified:
            identifier = failure.get("id") or f"shard {failure.get('shard')}"
            lines.append(
                f"- **{identifier}** `{failure['category']}`: {failure.get('error', '')}"
            )
    if roi is not None:
        lines.extend(
            [
                "",
                "### Skill ROI",
                "",
                f"**{machine['roi'].get('verdict', 'unknown').upper()}** — "
                + "; ".join(machine["roi"].get("reasons") or []),
            ]
        )
    return machine, "\n".join(lines) + "\n"


def dump_summary(machine: dict, markdown: str) -> tuple[str, str]:
    return json.dumps(machine, indent=2, sort_keys=True) + "\n", markdown
