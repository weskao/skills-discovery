# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Step 0 self-healing bootstrap** — first invocation auto-copies the template registry to `<SKILL_HOME>/skills-registry.yaml` and creates `<SKILL_HOME>/log/`, removing the need for any manual setup.
- **`KNOWN_SKILLS` augmentation from installed state** — discovery now also reads `<SKILL_HOME>/skills/` and `<SKILL_HOME>/plugins/installed_plugins.json`, ensuring skills installed via `git clone` or `claude plugin install` are never re-surfaced as candidates.
- **openclaw-based Telegram delivery** — the daily report is now written to `/tmp/skill_report.md` and sent via openclaw with `--delivery '{"parse_mode":"Markdown"}'`, enabling proper Markdown rendering. Falls back to logging if openclaw is unavailable.
- **Three new default topics in `skills-registry.template.yaml`** — `claude-code-subagents`, `agentic-coding`, and `claude-code-plugin`, covering subagent collections, orchestration frameworks, and plugin-style extensions that were previously invisible to topic-based search.

### Changed

- **Merge algorithm gains a step 3** — existing candidates that were searched-but-not-top-ranked are now refreshed with fresh stars/score/summary instead of being left stale. Untouched entries are still preserved across runs.
- Telegram report format clarified: skill/tool names render as `[name](url)` hyperlinks, and summaries must avoid `_` (underscore) to prevent unintended italics in Markdown parsing.

### Fixed

- **Multi-skill collection repos no longer wrongly penalized** — the `-3` "no SKILL.md" rule now ignores subdirectory SKILL.md files. Repos like `wshobson/agents` that ship dozens of skills as subdirectories used to score 4 (and drop out of top-6); they now score 7 and surface correctly.

## [0.2.0] - 2026-05-19

### Added

- **`skill_keywords` broadened search** — GitHub discovery now accepts a `skill_keywords` list in configuration and scans additional topics and awesome-list sources, surfacing a wider range of relevant tools per run.

### Changed

- **skill-candidates.yaml merge behavior** — instead of overwriting on each run, the skill now merges new candidates into the existing file, deduplicating by source/name. This preserves previously discovered pending candidates across runs.
- Skill names in the Telegram approval message are now rendered as hyperlinks to their GitHub repositories for faster review.

## [0.1.0] - 2026-05-18

### Added

- **Initial skill-discovery release** — daily discovery of new Claude Code skills and adjacent AI/agent tools. Diffs GitHub findings against `skills-registry.yaml`, scores candidates, writes a shortlist to `skill-candidates.yaml`, and sends a Telegram message for user approval.
- **Project-aware skill home** — the skill detects its host project's home directory at runtime, so the same install works under `~/.claude/skills/skill-discovery/`, `~/.openclaw/skills/skill-discovery/`, or any other `<root>/skills/<name>/` layout. State files (`skills-registry.yaml`, `skill-candidates.yaml`, `log/`) always live directly under that resolved home.
- MIT license, `.gitignore` for macOS and Windows system files, and a README usage guide noting the `tg_send` caveat.

[unreleased]: https://github.com/weskao/skill-discovery/compare/v0.2.0...main
[0.2.0]: https://github.com/weskao/skill-discovery/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/weskao/skill-discovery/commits/v0.1.0
