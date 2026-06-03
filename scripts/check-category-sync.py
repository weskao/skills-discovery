#!/usr/bin/env python3
"""Fail if the category set drifts between the template, SKILL.md, and README.

The skill/tool *categories* are duplicated across several files with no automated
link between them (see CLAUDE.md). When a category is added to the template's
`skills:` / `tools:` buckets but NOT to SKILL.md's inference enum, a candidate of
that category silently falls through to `other`, loses its +4 boost, takes a -2
penalty, and never surfaces. This script makes that drift a CI failure instead of
a silent runtime bug.

Source of truth: the `skills:` / `tools:` keys in skills-registry.template.yaml.
Consumers that must list every one of those keys:
  - SKILL.md  Step 2 (skills inference enum) and Step 3 (tools inference enum)
  - README.md Customization table (Skills / Tools rows)

No third-party dependencies — pure regex extraction so it runs identically in CI
and on a fresh laptop.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "skills-registry.template.yaml"
SKILL_MD = ROOT / "SKILL.md"
README = ROOT / "README.md"

# `other` is an intentional catch-all in the enums; it is never a template bucket.
IGNORE = {"other", "category"}


def template_keys(section: str, stop_at: str) -> set[str]:
    """Top-level keys under `section:` up to the next `stop_at:` line."""
    text = TEMPLATE.read_text(encoding="utf-8")
    block = re.search(rf"^{section}:\n(.*?)^{stop_at}:", text, re.S | re.M)
    if not block:
        sys.exit(f"FATAL: could not locate `{section}:` … `{stop_at}:` in {TEMPLATE.name}")
    return set(re.findall(r"^  ([A-Za-z0-9_]+):", block.group(1), re.M))


def enum_tokens(needle: str) -> set[str]:
    """Backtick-quoted snake_case tokens on the SKILL.md line containing `needle`."""
    for line in SKILL_MD.read_text(encoding="utf-8").splitlines():
        if needle in line and "infer" in line:
            return {t for t in re.findall(r"`([a-z0-9_]+)`", line)} - IGNORE
    sys.exit(f"FATAL: could not find inference line containing {needle!r} in {SKILL_MD.name}")


def readme_row(label: str) -> set[str]:
    """Backtick-quoted tokens in the README Customization table row `| label |`."""
    for line in README.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(f"| {label}"):
            return {t for t in re.findall(r"`([a-z0-9_]+)`", line)} - IGNORE
    sys.exit(f"FATAL: could not find README customization row for {label!r}")


def check(name: str, expected: set[str], actual: set[str], where: str) -> list[str]:
    missing = sorted(expected - actual)
    if missing:
        return [f"  ✗ {name}: {where} is missing {missing}"]
    print(f"  ✓ {name}: {where} lists all {len(expected)} template categories")
    return []


def main() -> int:
    skills = template_keys("skills", "tools")
    tools = template_keys("tools", "watchlist")

    errors: list[str] = []
    errors += check("skills", skills, enum_tokens("from name + summary"), "SKILL.md Step 2 enum")
    errors += check("tools", tools, enum_tokens("infer:"), "SKILL.md Step 3 enum")
    errors += check("skills", skills, readme_row("Skills"), "README Customization table")
    errors += check("tools", tools, readme_row("Tools"), "README Customization table")

    if errors:
        print("\nCATEGORY DRIFT DETECTED — see CLAUDE.md 'category-consistency invariant':")
        print("\n".join(errors))
        print(
            "\nAdd the missing category to every consumer (enum, heuristic, Step 6 "
            "report group, README table) in the same commit."
        )
        return 1

    print("\nAll category sets are in sync. ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
