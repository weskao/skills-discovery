# Skills Discovery 🚀

A daily curation agent for [Claude Code](https://claude.com/claude-code) and compatible variants. Discovers new skills and adjacent AI/agent tools from GitHub, scores them by category fit and popularity, and surfaces a top-10 shortlist for one-tap approval.

Run on a cron, or invoke manually with `/skills-discovery`.

## ✨ Features

- **Curated sources**: Polls GitHub orgs, topics, and "awesome" lists known to publish quality skills.
- **Smart de-duplication**: Skips registry entries, skill directories already on disk, and installed plugins — even if they were installed outside this skill.
- **Transparent scoring**: Each candidate scored 0–10 by category fit, stars, and curated source.
- **One-tap approval**: Telegram shortlist with reply commands — `install 1 3 5`, `install all`, `skip all`, or `details 2`.
- **Graceful fallback**: Merges new candidates into `skill-candidates.yaml` locally, carrying previously discovered pending entries forward (up to the 60-entry cap) even when Telegram is unavailable.
- **Stable numbering**: The report's ①–⑩ are the file's `index` 1–10 by construction, so `install 7` always means the candidate you saw at ⑦. A 60-entry retention cap keeps the file rewritable and the numbering honest.

## 🧭 Project-aware by design

The skill detects its host project's home directory at runtime, so the same install works under any `<project>/skills/<skill-name>/` layout.

| Install location | `<project-home>` resolves to |
| --- | --- |
| `~/.claude/skills/skills-discovery/` | `~/.claude/` |
| `~/.openclaw/skills/skills-discovery/` | `~/.openclaw/` |
| `~/.hermes/skills/skills-discovery/` | `~/.hermes/` |
| `<project_root>/.claude/skills/skills-discovery/` | `<project_root>/.claude/` |
| `<anywhere>/skills/skills-discovery/` | `<anywhere>/` |

State files (`skills-registry.yaml`, `skill-candidates.yaml`, `log/`) always live directly under `<project-home>`.

## 🚀 Getting Started

For default Claude Code:

```bash
git clone https://github.com/weskao/skills-discovery.git \
  ~/.claude/skills/skills-discovery
```

For openclaw:

```bash
git clone https://github.com/weskao/skills-discovery.git \
  ~/.openclaw/skills/skills-discovery
```

For hermes:

```bash
hermes skills install https://github.com/weskao/skills-discovery.git \
  --name skills-discovery
```

For a project-local install (scoped to the current project's `.claude/`):

```bash
# Run from your project root
git clone https://github.com/weskao/skills-discovery.git \
  .claude/skills/skills-discovery
```

State files (`skills-registry.yaml`, `skill-candidates.yaml`, `log/`) will live under `<project_root>/.claude/` rather than your global `~/.claude/`.

The first time you run `/skills-discovery`, Step 0 auto-creates `<project-home>/skills-registry.yaml` from the bundled template.

## 📋 Requirements

| Required | Used for | If missing |
| --- | --- | --- |
| Claude Code (or compatible host) | Runs the skill | n/a |
| [`github-mcp-server`](https://github.com/github/github-mcp-server) MCP **or** `gh` CLI | GitHub search & file fetch — pick one (see note below) | Discovery cannot run — install one:<br>• MCP: add `github-mcp-server` via your host's MCP settings<br>• `gh` CLI ([full install docs](https://github.com/cli/cli#installation)):<br>&nbsp;&nbsp;macOS `brew install gh`<br>&nbsp;&nbsp;Linux `sudo apt install gh`<br>&nbsp;&nbsp;Windows `winget install GitHub.cli` |
| `jq` CLI | Parsing: required for `gh`-path; also used when MCP results overflow to a file | `gh`-path blocked without it; MCP-path falls back to slower subagent parsing — [install jq](https://jqlang.github.io/jq/download/):<br>• macOS: `brew install jq`<br>• Linux: `apt install jq`<br>• Windows: `winget install jqlang.jq` |

> **GitHub access paths compared:**
>
> - **`github-mcp-server` MCP** — returns structured JSON directly; `jq` only needed if results overflow to a file.
> - **`gh` CLI** — equivalent coverage (`gh search repos` / `gh api repos/{owner}/{repo}/contents/{path}`), but requires `jq` to parse every response.

## 📣 Telegram notifications (delivery options)

Step 6 delivers the report through a **fallback chain** — it tries each channel below in order and stops at the first that works. Whatever happens, the shortlist is **always** also written to `<project-home>/skill-candidates.yaml`, so results are never lost even if every channel is unavailable.

> **Note:** earlier versions described a `tg_send`-first model. The skill does *not* require `tg_send` — it is only the third fallback. Pick whichever option below matches your setup.

### Option 1 — Telegram MCP plugin (zero setup)

If you have the `telegram` MCP plugin and run the skill inside a Telegram-channel session, it calls the `reply` tool directly. Nothing else to configure — this is the preferred path.

### Option 2 — openclaw (the author's default)

If you use [openclaw](https://github.com/openclaw/openclaw), the skill sends via `openclaw message send`, reading your chat id from `<project-home>/channels/telegram/access.json` (created by openclaw's `/telegram:access` pairing flow). Requires the `openclaw` CLI on `PATH` or in a standard node install location.

openclaw refuses to start on a `node` outside its supported range, which the *current* `node` on a machine often is. The skill therefore probes your installed node versions and uses the first one openclaw actually accepts; if none do, it falls through to the next delivery option instead of failing the run. This matters most for unattended cron runs, where a shell error would otherwise swallow the report.

### Option 3 — Roll your own `tg_send`

If you have neither of the above, define a `tg_send` shell function and the fallback chain will use it:

```bash
# macOS / Linux / Windows WSL — add to ~/.bashrc or ~/.zshrc
# Requires TG_BOT_TOKEN and TG_CHAT_ID env vars
tg_send() {
  curl -s -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TG_CHAT_ID}" \
    --data-urlencode "text=$1" > /dev/null
}
```

Create a bot via [@BotFather](https://t.me/BotFather), get your chat ID from [@userinfobot](https://t.me/userinfobot), and export both as env vars.

### Option 4 — Skip Telegram entirely

The skill is **designed to degrade gracefully**:

- **Mode A (discovery) still works.** The shortlist is always written to `<project-home>/skill-candidates.yaml`. Open and review it manually.
- **A failed delivery is logged** to `<project-home>/log/skills-discovery.log` rather than crashing the run.
- **Mode B (install via reply) becomes manual.** Instead of replying on Telegram, re-invoke the skill with explicit indices — e.g. ask Claude: *"From `<project-home>/skill-candidates.yaml`, install candidates 1, 3, and 5."*

## 🚦 Usage

### Invoking the skill

```text
/skills-discovery
/skills-discovery <keyword>
/skills-discovery remove <name>
```

| Invocation | What happens |
| --- | --- |
| `/skills-discovery` | Full discovery run — searches all watchlist topics, orgs, keywords, and awesome lists, then surfaces a top-10 shortlist. |
| `/skills-discovery memory` | Scoped discovery — searches GitHub for `memory` only (watchlist loops skipped). Useful for exploring a specific domain without waiting for the full sweep. |
| `/skills-discovery remove flutter-helper` | After terminal confirmation, removes the installed skill directory and its `skills-registry.yaml` entry. Terminal-only; Telegram replies cannot remove anything. |

The keyword can be any term: a technology (`flutter`), a concept (`agent`), or a feature area (`workflow`). Steps 4–6 (scoring, candidates file, Telegram report) run identically regardless.

> **Not covered here:** pulling fresh code into an already-installed skill. That's the `update-skills` skill's job — this skill only ever refreshes a known entry's star count, never its content.

### Responding to a discovery report

After a report arrives on Telegram, reply with one of the following commands. The same commands also work when invoking the skill manually via Claude if Telegram is unavailable (see [Skip Telegram entirely](#option-4--skip-telegram-entirely)).

| Reply | Effect |
| --- | --- |
| `install 1 3 5` | Install the selected skills at the report positions. A selected tools-track entry is recorded as evaluated but is never cloned; external tools remain your separate decision. |
| `install all` | Install every skill candidate and track every tool candidate in the current report. |
| `skip all` | Discard the candidate file without installing anything. Skipped candidates are not added to the registry, so the next discovery run may re-surface them. |
| `details 2` | Fetch and display the full `SKILL.md` (skills) or `README.md` (tools) for candidate ②. Does not install. |

Numbers refer to the report you are replying to, not to whatever ran most recently — each report carries a `run:` id and is resolved against its own frozen snapshot. Replying to an older report is safe.

> **Without Telegram:** ask Claude directly — e.g. *"From `~/.claude/skill-candidates.yaml`, install candidates 1 and 3."*

## ⚙️ How it works

### Mode A — Discovery (read-only on registry)

```text
Step 0:  Bootstrap — create <project-home>/skills-registry.yaml from template if missing
Step 1:  Read registry and installed state, build known-item sets
Step 1b: Keyword runs only — expanded search, then assign each repo a track by evidence
Step 2-3: Search GitHub (skills track + tools track)
Step 4:  Diff against known, score 0–10, drop anything below MIN_SCORE (3),
         cap 2 per repo, keep top 6 skills + top 4 tools; refresh known stars
         and check the upstream path of subdirectory skills (report-only)
Step 5:  Merge + rewrite <project-home>/skill-candidates.yaml
         (this run's shortlist at indices 1–10; 60-entry retention cap;
          re-reads the file before writing so a concurrent run isn't clobbered)
Step 6:  Freeze the shortlist to log/shortlist-<run_id>.yaml, then send it
         (or log to file on fallback)
```

### What is filtered, and why

Before scoring, the skill removes duplicates in the smallest useful scope:

- A result is excluded when its GitHub **`owner/repo[/subpath]`** is already recorded in `skills-registry.yaml`. Full source identity, not the bare name, is the primary test — different authors publish same-named repos, so name-only matching would both hide genuinely new repos and let real duplicates through. The subpath counts: a multi-skill collection holds many independent skills, so a registered `owner/repo/skills/a` does **not** hide a newly published `owner/repo/skills/b`. An entry recorded without a subpath does cover its whole repo.
- A result is *additionally* excluded when its **name** is already taken: an entry in the registry, a directory at `<project-home>/skills/<name>/`, or a key in `plugins/installed_plugins.json`. This covers skills installed manually or with `claude plugin install`, and it prevents offering a skill that could not be cloned without overwriting one you already have.
- Anything scoring below **`MIN_SCORE` (3)** is dropped before the top-6/top-4 cutoff, so a narrow search returns a short report rather than a padded one. An empty shortlist is a valid result.
- On a full sweep, a tools result is excluded when it points to the same `owner/repo` as one of the kept skill results, so one repository is never presented twice. Keyword runs skip this: Step 1b has already given every repo exactly one track.
- A single `owner/repo` contributes **at most 2 candidates from any single** repository to one report. A multi-skill collection can produce six new candidates at once, and one publisher filling the shortlist would bury everything else. The rest are deferred to the pending file, not discarded, and a later run offers them.
- The pending candidates file is merged by GitHub source first and name second, so a rediscovered pending item is refreshed instead of duplicated. It keeps at most 60 pending entries; the newest report's entries always come first.

Registry entries whose installed skill directory or plugin is now missing are reported as **stale**. They are never removed automatically; use the terminal-only `remove <name>` command if that cleanup is intended.

Entries that live *inside* a repository are also checked against upstream, because a star count taken from the repo root cannot tell you that one skill in a collection was renamed or deleted. For up to 10 repositories per run (oldest-checked first), the skill lists the parent directory of the paths it tracks and reports three findings:

- **Upstream path gone** — the recorded subdirectory is no longer in the listing. Sibling directories you do not have are listed as rename hints.
- **Parent path moved** — *every* tracked skill in that repository disappeared at once, which is what restructuring a parent directory looks like. One upstream event gets one report line instead of one line per affected skill.
- **Looks superseded** — the subdirectory still exists, but its `SKILL.md` body is at most 2 non-blank lines *and* the first of them names a sibling skill: the shape of a redirect stub left after a rename. Both conditions are required, so a terse skill that merely cross-references another one is not flagged. The report also says whether the skill was hollowed out *after* you installed it or was already a stub when you installed it — that comparison reads your local copy, at no API cost.

All three are advisory lines and nothing more: no uninstall, no rewritten `source`. They remain heuristics, so the decision stays with you.

The check is budgeted. Directory listings are cheap and always run; the `SKILL.md` fetches behind the superseded test are capped at **at most 10 content fetches per run**, and a repository is skipped entirely when its directory listing is byte-identical to the previous run — nothing can have been renamed if nothing in the listing changed. Fingerprints live in `<project-home>/log/upstream-seen.yaml`; any entry that has not been content-checked for 30 days is re-checked regardless, which is what catches a skill hollowed out in place. Deleting that file costs one run of redundant fetches and nothing else.

Skills installed outside the approval flow are included when their origin can be recovered from a `.source` file or a `.repos/<owner>__<repo>/…` symlink target; that recovered origin is used for the check only and is never written to the registry.

### How candidates are selected

The skill searches the configured GitHub topics, organizations, keywords, and awesome lists. `/skills-discovery <keyword>` replaces those loops with a keyword search, but does not discard candidates found by previous runs.

A keyword run expands the term into up to three deterministic queries — the keyword verbatim, `<keyword> skill`, and `topic:<keyword>` for single-token keywords — and merges the results. It then fetches each top repository's root listing and assigns a track by **evidence**: a root `SKILL.md`, `skills/`, `skill/`, or `.claude-plugin/` makes it a skill; everything else is a tool. An MCP server or library is therefore scored as a tool rather than penalized for not being a skill.

Each valid result is categorized and scored: +4 for an interested category, +1–3 for stars, +1 for a curated source, -2 for `other`, and -3 when the expected `SKILL.md`/`README.md` is absent. Anything below `MIN_SCORE` (3) is discarded. Results are then sorted by score, stars, then name; the report keeps up to six skills and four tools. Two survivors sharing a name are shown as `name (owner)` so they can be told apart. Repository names and summaries are validated and sanitized before they are saved or displayed.

### Mode B — Install via approval reply

```text
You: install 1 3 5
Skill: resolve those numbers against that report's frozen shortlist snapshot
Skill: git clone the 3 approved skills into <project-home>/skills/<name>/
Skill: append entries to skills-registry.yaml (so they're skipped next run)
Skill: clear <project-home>/skill-candidates.yaml
Skill: reply ✅ summary
```

**Report numbers stay valid.** Each report is frozen to its own `log/shortlist-<run_id>.yaml` before being sent, and the report footer carries that `run_id`. A reply is resolved against *that* snapshot, so replying to a three-day-old report still installs what that report showed — even though several discovery runs have renumbered the shared candidates file since. Only reports older than the last ten runs fall back to the shared file.

`install all` means only the entries displayed in the report being answered, not every carried-over pending entry. Indices are validated first, so a malformed or unresolvable list is refused rather than targeting the wrong repository. An approved skill whose install path is already occupied is reported as **blocked** rather than overwriting what is there.

### Mode C — Remove an installed skill

`/skills-discovery remove <name>` is separate from discovery and Telegram replies. It validates the name, shows exactly what will be removed, and waits for terminal confirmation. It removes only a matching installed skill and registry entry. A tracked tool cannot be removed this way because tools were never cloned.

## 🛠️ Customization

Edit `<project-home>/skills-registry.yaml` to tune what gets discovered. This is your active default list: it is created from the bundled `skills-registry.template.yaml` on the first run, then preserved. Editing the template later only changes fresh installations; it does not rewrite an existing registry.

| Track  | Default categories                                                                                                      |
|--------|-------------------------------------------------------------------------------------------------------------------------|
| Skills | `flutter`, `ui_ux`, `agent_ai`, `automation_production`, `mindset`, `security`, `hooks`, `workflows`                     |
| Tools  | `agent_frameworks`, `coding_agents`, `workflow_automation`, `developer_tooling`, `security_tooling`, `claude_automation` |

- `watchlist.orgs` — GitHub orgs known to publish skills
- `watchlist.github_topics` — topic tags to search across all of GitHub
- `watchlist.skill_keywords` — free-text keywords for the skills track (catches repos without a standard topic tag)
- `watchlist.tool_keywords` — free-text keywords for the tools track
- `watchlist.awesome_lists` — curated lists to parse
- `watchlist.categories_of_interest` — categories that get a +4 scoring boost

To add a source, add an organization, topic, keyword, or `github:owner/repo` awesome list under `watchlist`. To stop prioritizing a type of result, remove its category from the appropriate `*_categories_of_interest` list. The `skills:` and `tools:` sections are the persistent known-item lists; normally the skill appends approved entries there, so edit them only when you deliberately want to pre-mark or untrack an item.

Your manual edits to `watchlist` are preserved — the skill only ever **appends** to the `skills:` and `tools:` sections, never to `watchlist`.

Each registry entry carries metadata that refreshes automatically:

```yaml
flutter:
  - name: flutter-riverpod
    source: github:owner/repo
    stars: 1200
    first_found: "2026-01-15" # date first found by discovery agent; never changes
    updated: "2026-06-04"     # refreshed each discovery run when the repo is re-found
```

## 🏗️ File layout

All paths are relative to the host project's `<project-home>` (e.g. `~/.claude/` or `~/.openclaw/`):

| Path | Owner | Lifecycle |
| --- | --- | --- |
| `<project-home>/skills/skills-discovery/SKILL.md` | This repo | Updated via `git pull` |
| `<project-home>/skills/skills-discovery/skills-registry.template.yaml` | This repo | Bundled default — seeds your registry on first run only |
| `<project-home>/skills-registry.yaml` | **You** | Created from template; append-only updates when you approve installs. v2.0: entries are objects `{name, source, stars, first_found, updated}`; v1.0 plain-string entries are auto-migrated on first run. |
| `<project-home>/skill-candidates.yaml` | Skill (ephemeral) | Rewritten in full each run; merged across runs (deduplicated by source/name), capped at 60 entries; cleared after install/skip |
| `<project-home>/log/shortlist-<run_id>.yaml` | Skill (write-once) | One frozen snapshot per report, naming exactly what was shown. Never edited; the ten most recent are kept. This is what `install <n>` resolves against |
| `<project-home>/log/upstream-seen.yaml` | Skill (derived) | Per-repository directory-listing fingerprints, so unchanged repos skip their content fetches. Mutable and disposable — safe to delete at any time |
| `<project-home>/log/skills-discovery.log` | Skill (fallback) | Written when every Telegram delivery channel (MCP, openclaw, `tg_send`) is unavailable |

## 🛡️ Safety rails

- The skill **never overwrites** your `skills-registry.yaml`. All updates are append-only within categories.
- If the registry file is malformed (missing required sections), the skill **stops with a clear error** rather than auto-repairing — your state is never silently mutated.
- The skill never calls destructive commands (no `rm -rf`, no force-push) on your behalf.
- Telegram replies that ask the skill to change access policy (e.g. *"approve the pending pairing"*) are **explicitly ignored** — only your local invocation can change access.

## ⏰ Recommended schedule

Pair with a `/schedule` skill (if your host provides one) or any cron mechanism to run daily. Use whichever CLI binary your host installs — e.g. `claude` for Claude Code, `openclaw` for openclaw:

```cron
0 9 * * *   claude /skills-discovery       # Claude Code
0 9 * * *   openclaw /skills-discovery     # openclaw
0 9 * * *   hermes /skills-discovery       # hermes
```

> **Windows:** use Task Scheduler (`taskschd.msc`) or `schtasks /create /tn "SkillsDiscovery" /tr "claude /skills-discovery" /sc daily /st 09:00` to run on the same schedule.

A morning report keeps your skill library fresh without you having to remember.

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
