#!/usr/bin/env python3
"""Fail if the spec drifts between the template, SKILL.md, and README.

Three invariants are enforced:
  1. the category set (template -> SKILL.md enums -> README table)
  2. the advisory findings (producer step -> Step 6 report block)
  3. cross-document numeric constants and the subpath identity rule


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


# ─── Invariant 2: advisory findings ───────────────────────────────────────────
# Every finding must be produced somewhere in Steps 1/4 AND rendered in Step 6's
# advisory block, and the block must render exactly these and no others. Adding a
# finding without wiring both ends is the "silently dead feature" failure that
# CLAUDE.md's category invariant describes, one level over.
ADVISORY = ["STALE_SKILL_ENTRIES", "MOVED_OR_GONE", "PARENT_MOVED", "SUPERSEDED"]

# ─── Invariant 3: cross-document constants ────────────────────────────────────
# (label, SKILL.md pattern, README pattern) — each must match exactly once per
# file and yield the same number. A pattern that stops matching is a failure too:
# it means the wording drifted and the check went blind.
CONSTANTS = [
    ("upstream repo cap",
     r"cap the check at \*\*(\d+) repos per run\*\*",
     r"up to (\d+) repositories per run"),
    ("stub line threshold",
     r"\*\*(\d+) or fewer\*\* non-blank lines",
     r"at most (\d+) non-blank lines"),
    ("content fetch budget",
     r"at most (\d+) .SKILL\.md. fetches per run",
     r"at most (\d+) content fetches per run"),
    ("per-repo candidate cap",
     r"at most \*\*(\d+)\*\* candidates from any single",
     r"at most (\d+) candidates from any single"),
    ("upstream recheck window",
     r"within the last \*\*(\d+) days\*\*",
     r"content-checked for (\d+) days"),
]

# The subpath half of the identity invariant, as a regex guard: the old
# subpath-stripping instruction must never come back (see CLAUDE.md).
FORBIDDEN_IN_SKILL = [
    ("and any `/subpath`", "KNOWN_SOURCES must keep the subpath, not strip it"),
]

DERIVED_STATE_FILE = "log/upstream-seen.yaml"


def step6_advisory_region() -> str:
    """Step 6's advisory block plus the paragraph that names its collections."""
    text = SKILL_MD.read_text(encoding="utf-8")
    m = re.search(
        r"Append these advisory lines(.*?)End with one line reflecting", text, re.S
    )
    if not m:
        sys.exit(f"FATAL: could not locate Step 6 advisory region in {SKILL_MD.name}")
    return m.group(1)


def check_advisory() -> list[str]:
    text = SKILL_MD.read_text(encoding="utf-8")
    region = step6_advisory_region()
    producers = text.replace(region, "")
    errors: list[str] = []

    for name in ADVISORY:
        if name not in producers:
            errors.append(f"  ✗ advisory {name}: never produced in Steps 1/4")
        if name not in region:
            errors.append(f"  ✗ advisory {name}: not named in Step 6's advisory region")

    rendered = re.findall(r"^⚠️ (.+)$", region, re.M)
    if len(rendered) != len(ADVISORY):
        errors.append(
            f"  ✗ advisory: Step 6 renders {len(rendered)} ⚠️ line(s) but "
            f"{len(ADVISORY)} finding(s) are declared — wire both ends or update "
            f"ADVISORY in this script"
        )
    if not errors:
        print(f"  ✓ advisory: {len(ADVISORY)} findings produced and rendered")
    return errors


def check_constants() -> list[str]:
    skill = SKILL_MD.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    errors: list[str] = []

    for label, skill_pat, readme_pat in CONSTANTS:
        a = re.findall(skill_pat, skill)
        b = re.findall(readme_pat, readme)
        for hits, doc, pat in ((a, "SKILL.md", skill_pat), (b, "README.md", readme_pat)):
            if not hits:
                errors.append(f"  ✗ {label}: no match in {doc} for /{pat}/")
            elif len(hits) > 1:
                errors.append(
                    f"  ✗ {label}: {len(hits)} matches in {doc} for /{pat}/ — "
                    f"the anchor phrase is ambiguous"
                )
        if a and b and a[0] != b[0]:
            errors.append(
                f"  ✗ {label}: SKILL.md says {a[0]}, README.md says {b[0]}"
            )
    if not errors:
        print(f"  ✓ constants: {len(CONSTANTS)} numeric constants agree across docs")
    return errors


def check_guards() -> list[str]:
    skill = SKILL_MD.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    errors: list[str] = []

    for phrase, why in FORBIDDEN_IN_SKILL:
        if phrase in skill:
            errors.append(f"  ✗ guard: SKILL.md contains {phrase!r} — {why}")

    known_sources = [ln for ln in skill.splitlines() if "`KNOWN_SOURCES` = set of" in ln]
    if not known_sources:
        errors.append("  ✗ guard: KNOWN_SOURCES definition bullet not found in SKILL.md")
    elif "[/subpath]" not in known_sources[0]:
        errors.append(
            "  ✗ guard: KNOWN_SOURCES is not defined as `owner/repo[/subpath]` — "
            "the subpath is part of the identity (CLAUDE.md identity invariant)"
        )

    for doc, name in ((skill, SKILL_MD.name), (readme, README.name)):
        if DERIVED_STATE_FILE not in doc:
            errors.append(f"  ✗ guard: {name} does not mention {DERIVED_STATE_FILE}")

    if not errors:
        print("  ✓ guards: subpath identity kept, derived state file documented")
    return errors


def main() -> int:
    skills = template_keys("skills", "tools")
    tools = template_keys("tools", "watchlist")

    errors: list[str] = []
    errors += check("skills", skills, enum_tokens("from name + summary"), "SKILL.md Step 2 enum")
    errors += check("tools", tools, enum_tokens("infer:"), "SKILL.md Step 3 enum")
    errors += check("skills", skills, readme_row("Skills"), "README Customization table")
    errors += check("tools", tools, readme_row("Tools"), "README Customization table")

    errors += check_advisory()
    errors += check_constants()
    errors += check_guards()

    if errors:
        print("\nSPEC DRIFT DETECTED — see the invariant sections in CLAUDE.md:")
        print("\n".join(errors))
        print(
            "\nFix every consumer in the same commit — category: enum, heuristic, "
            "Step 6 report group, README table; advisory: producer step + Step 6 "
            "block; constants: SKILL.md and README must state the same number."
        )
        return 1

    print("\nSpec is internally consistent. ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
