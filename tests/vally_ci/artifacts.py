from __future__ import annotations

import json
from pathlib import Path

from .reporting import redact


ALLOWED_SUFFIXES = {".json", ".jsonl", ".log", ".txt"}


def _redact_json_text(text: str) -> str:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return redact(text)
    return json.dumps(redact(value), indent=2, sort_keys=True) + "\n"


def _redact_jsonl_text(text: str) -> str:
    output = []
    for line in text.splitlines():
        if not line.strip():
            output.append("")
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            output.append(redact(line))
        else:
            output.append(json.dumps(redact(value), sort_keys=True))
    return "\n".join(output) + ("\n" if text.endswith("\n") else "")


def redact_result_tree(input_root: Path, output_root: Path) -> dict:
    """Copy a safe, redacted subset of a result tree for artifact upload."""

    source = input_root.resolve()
    destination = output_root.resolve()
    if not source.is_dir():
        raise ValueError(f"input result tree does not exist: {input_root}")
    if destination == source or destination.is_relative_to(source):
        raise ValueError("output artifact root must not be nested under input result root")

    copied: list[str] = []
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(input_root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        suffix = path.suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            continue
        relative = path.relative_to(input_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".json":
            safe_text = _redact_json_text(text)
        elif suffix == ".jsonl":
            safe_text = _redact_jsonl_text(text)
        else:
            safe_text = redact(text)
        target.write_text(safe_text, encoding="utf-8")
        copied.append(relative.as_posix())
    return {"input_root": str(source), "output_root": str(destination), "copied": copied}
