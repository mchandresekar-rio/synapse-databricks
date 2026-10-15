#!/usr/bin/env python3
"""Validate and materialize repository-local plugin bundles."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
SKILLS = ROOT / "skills"
MANIFEST_REL = Path(".github/plugin/plugin.json")
GENERATED_DIRS = ("skills", "agents", ".claude-plugin")


def remove_tree(path: Path) -> None:
    """Remove generated content, clearing Windows/OneDrive read-only bits."""
    def make_writable(function, target, _error):
        os.chmod(target, stat.S_IWRITE)
        function(target)

    if path.exists():
        shutil.rmtree(path, onerror=make_writable)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def skill_name(reference: str) -> str:
    normalized = reference.removeprefix("./")
    prefix = "skills/"
    if not normalized.startswith(prefix):
        raise ValueError(f"Invalid skill reference {reference!r}; expected ./skills/<name>")
    return normalized[len(prefix):]


def validate_manifest(plugin_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    required = ("name", "description", "skills")
    for key in required:
        if not manifest.get(key):
            errors.append(f"{plugin_dir.name}: missing {key}")
    if manifest.get("mcpServers"):
        errors.append(f"{plugin_dir.name}: initial bundle must not declare MCP servers")
    for reference in manifest.get("skills", []):
        try:
            name = skill_name(reference)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        source = SKILLS / name / "SKILL.md"
        if not source.is_file():
            errors.append(f"{plugin_dir.name}: missing source {source.relative_to(ROOT)}")
    return errors


def materialize(plugin_dir: Path, manifest: dict) -> None:
    skills_out = plugin_dir / "skills"
    remove_tree(skills_out)
    skills_out.mkdir(parents=True)
    for reference in manifest["skills"]:
        name = skill_name(reference)
        shutil.copytree(SKILLS / name, skills_out / name)

    claude_dir = plugin_dir / ".claude-plugin"
    claude_dir.mkdir(parents=True, exist_ok=True)
    claude_manifest = {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": manifest["name"],
        "description": manifest["description"],
        "version": manifest.get("version", "0.0.0"),
        "license": manifest.get("license", "MIT"),
        "repository": manifest.get("repository"),
        "keywords": manifest.get("keywords", []),
        "skills": manifest["skills"],
        "agents": manifest.get("agents", []),
        "mcpServers": {},
    }
    (claude_dir / "plugin.json").write_text(
        json.dumps(claude_manifest, indent=2) + "\n", encoding="utf-8"
    )
    (plugin_dir / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate and materialize bundles")
    parser.add_argument("--clean", action="store_true", help="Remove generated bundle content first")
    args = parser.parse_args()

    errors: list[str] = []
    manifests: list[tuple[Path, dict]] = []
    for plugin_dir in sorted(PLUGINS.iterdir()):
        manifest_path = plugin_dir / MANIFEST_REL
        if not manifest_path.is_file():
            continue
        manifest = load_json(manifest_path)
        errors.extend(validate_manifest(plugin_dir, manifest))
        manifests.append((plugin_dir, manifest))

    if not manifests:
        errors.append("No plugin manifests found")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1

    for plugin_dir, manifest in manifests:
        if args.clean:
            for relative in GENERATED_DIRS:
                target = plugin_dir / relative
                remove_tree(target)
        materialize(plugin_dir, manifest)
        print(f"Built {manifest['name']} with {len(manifest['skills'])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
