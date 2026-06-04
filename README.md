# Skills Discovery 🚀

A daily curation agent for [Claude Code](https://claude.com/claude-code) and compatible variants. Discovers new skills and adjacent AI/agent tools from GitHub, scores them by category fit and popularity, and surfaces a top-10 shortlist for one-tap approval.

Run on a cron, or invoke manually with `/skills-discovery`.

## ✨ Features

- **Curated sources**: Polls GitHub orgs, topics, and "awesome" lists known to publish quality skills.
- **Smart de-duplication**: Diffs findings against your local registry so already-known items are skipped.
- **Transparent scoring**: Each candidate scored 0–10 by category fit, stars, and curated source.
- **One-tap approval**: Telegram shortlist with reply commands — `install 1 3 5`, `install all`, `skip all`, or `details 2`.
- **Graceful fallback**: Merges new candidates into `skill-candidates.yaml` locally, preserving previously discovered pending entries even when Telegram is unavailable.

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
| `mcp__github__*` MCP tools | GitHub search & file fetch | Discovery cannot run |

## 📣 Telegram notifications (delivery options)

Step 6 delivers the report through a **fallback chain** — it tries each channel below in order and stops at the first that works. Whatever happens, the shortlist is **always** also written to `<project-home>/skill-candidates.yaml`, so results are never lost even if every channel is unavailable.

> **Note:** earlier versions described a `tg_send`-first model. The skill does *not* require `tg_send` — it is only the third fallback. Pick whichever option below matches your setup.

### Option 1 — Telegram MCP plugin (zero setup)

If you have the `telegram` MCP plugin and run the skill inside a Telegram-channel session, it calls the `reply` tool directly. Nothing else to configure — this is the preferred path.

### Option 2 — openclaw (the author's default)

If you use [openclaw](https://github.com/openclaw/openclaw), the skill sends via `openclaw message send`, reading your chat id from `<project-home>/channels/telegram/access.json` (created by openclaw's `/telegram:access` pairing flow). Requires the `openclaw` CLI on `PATH` or in a standard node install location.

### Option 3 — Roll your own `tg_send`

If you have neither of the above, define a small zsh function and the fallback chain will use it:

```zsh
# Add to ~/.zshrc — requires TG_BOT_TOKEN and TG_CHAT_ID env vars
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

## ⚙️ How it works

### Mode A — Discovery (read-only on registry)

```text
Step 0: Bootstrap — create <project-home>/skills-registry.yaml from template if missing
Step 1: Read registry, build KNOWN_SKILLS / KNOWN_TOOLS sets
Step 2-3: Search GitHub (skills track + tools track)
Step 4: Diff against known, score 0–10, keep top 6 skills + top 4 tools
Step 5: Write <project-home>/skill-candidates.yaml
Step 6: Send Telegram shortlist (or log to file on fallback)
```

### Mode B — Install via approval reply

```text
You: install 1 3 5
Skill: git clone the 3 approved skills into <project-home>/skills/<name>/
Skill: append entries to skills-registry.yaml (so they're skipped next run)
Skill: clear <project-home>/skill-candidates.yaml
Skill: reply ✅ summary
```

## 🛠️ Customization

Edit `<project-home>/skills-registry.yaml` to tune what gets discovered:

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

**Migrating from v1.0:** if your `skills-registry.yaml` has `version: "1.0"` (plain-string entries), the skill upgrades it automatically on first run — no manual action needed.

## 🏗️ File layout

All paths are relative to the host project's `<project-home>` (e.g. `~/.claude/` or `~/.openclaw/`):

| Path | Owner | Lifecycle |
| --- | --- | --- |
| `<project-home>/skills/skills-discovery/SKILL.md` | This repo | Updated via `git pull` |
| `<project-home>/skills/skills-discovery/skills-registry.template.yaml` | This repo | Bundled default — seeds your registry on first run only |
| `<project-home>/skills-registry.yaml` | **You** | Created from template; append-only updates when you approve installs. v2.0: entries are objects `{name, source, stars, first_found, updated}`; v1.0 plain-string entries are auto-migrated on first run. |
| `<project-home>/skill-candidates.yaml` | Skill (ephemeral) | Merged across runs (deduplicated by source/name); cleared after install/skip |
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

A morning report keeps your skill library fresh without you having to remember.

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
