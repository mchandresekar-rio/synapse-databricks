#!/usr/bin/env python3
"""Reject dependencies on the source skills repository or cross-repo automation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".json", ".md", ".py", ".ps1", ".sh", ".yaml", ".yml", ".toml", ".txt"}
IGNORE_PARTS = {".git", ".venv", "node_modules", ".pytest_cache", "__pycache__", ".vally-results", ".vally-staging"}
FORBIDDEN = {
    "gim-home/skills-for-fabric": "old repository URL or checkout",
    "github.com/gim-home/skills-for-fabric": "old repository URL",
    "uses: microsoft/skills-for-fabric": "cross-repository reusable workflow",
    "uses: gim-home/skills-for-fabric": "cross-repository reusable workflow",
}
WORKFLOW_REMOTE_USES = re.compile(r"^\s*uses:\s*([^./][^\s]+?)/\.github/(?:workflows|actions)/", re.MULTILINE)
SYNC_TERMS = re.compile(r"\b(repository_dispatch|sync[-_ ]to[-_ ](?:public|fabric)|mirror[-_ ]repo)\b", re.IGNORECASE)


def iter_text_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS and not set(path.parts) & IGNORE_PARTS:
            yield path


def main() -> int:
    failures: list[str] = []
    if (ROOT / ".gitmodules").exists():
        failures.append(".gitmodules is forbidden")

    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "submodule", "status"], cwd=ROOT, capture_output=True, text=True, check=False
        )
        if result.stdout.strip():
            failures.append("Git submodules are forbidden")

    for path in iter_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(ROOT).as_posix()
        if relative == "scripts/check_independence.py":
            continue
        for token, reason in FORBIDDEN.items():
            if token.lower() in text.lower():
                failures.append(f"{relative}: {reason}: {token}")
        if relative.startswith(".github/workflows/"):
            for match in WORKFLOW_REMOTE_USES.finditer(text):
                reference = match.group(1)
                if reference.lower().startswith(("actions/", "github/")):
                    continue
                failures.append(f"{relative}: remote reusable workflow/action is forbidden: {reference}")
            if SYNC_TERMS.search(text):
                failures.append(f"{relative}: repository synchronization automation is forbidden")

    if failures:
        print("Independence audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Independence audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
