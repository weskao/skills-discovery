# skill-discovery

A daily curation agent for [Claude Code](https://claude.com/claude-code): discovers new skills and adjacent AI/agent tools from GitHub, scores them by category fit and popularity, and surfaces a top-10 shortlist for one-tap approval.

Run on a cron, or invoke manually with `/skill-discovery`.

## What it does

- Polls curated GitHub orgs, topics, and "awesome" lists
- Diffs findings against your local registry so already-known items are skipped
- Scores each candidate 0–10 (category fit + stars + curated source)
- Writes the top 10 to `~/.claude/skill-candidates.yaml`
- Sends a Telegram shortlist; you reply `install 1 3 5` (or `install all` / `skip all` / `details 2`) to act on it

## Install

```bash
git clone https://github.com/weskao/skill-discovery.git \
  ~/.claude/skills/skill-discovery
```

That's it. The first time you run `/skill-discovery`, Step 0 auto-creates `~/.claude/skills-registry.yaml` from the bundled template — **no manual setup required**.

## Requirements

| Required | Used for | If missing |
|---|---|---|
| Claude Code | Runs the skill | n/a |
| `mcp__github__*` MCP tools | GitHub search & file fetch | Discovery cannot run |

## Optional: Telegram notifications (and the `tg_send` caveat)

The skill delivers results via a shell function called **`tg_send`**. This is **not a standard tool** — it's user-specific glue around your own Telegram bot. If you're cloning this skill, you almost certainly don't have it.

Three ways to handle this:

### Option 1 — Wire up your own `tg_send`

Define a zsh function that posts to the Telegram Bot API:

```zsh
# Add to ~/.zshrc — requires TG_BOT_TOKEN and TG_CHAT_ID env vars
tg_send() {
  curl -s -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TG_CHAT_ID}" \
    --data-urlencode "text=$1" > /dev/null
}
```

Create a bot via [@BotFather](https://t.me/BotFather), get your chat ID from [@userinfobot](https://t.me/userinfobot), and export both as env vars.

### Option 2 — Use the Telegram MCP plugin

If you have the `telegram` MCP plugin installed and are running inside a Telegram-channel session, the skill will call `reply` directly. No `tg_send` needed.

### Option 3 — Skip Telegram entirely

The skill is **designed to degrade gracefully**:

- **Mode A (discovery) still works.** The shortlist is always written to `~/.claude/skill-candidates.yaml`. Open and review it manually.
- **A failed `tg_send` is logged** to `~/.claude/log/skill-discovery.log` rather than crashing the run.
- **Mode B (install via reply) becomes manual.** Instead of replying on Telegram, re-invoke the skill with explicit indices — e.g. ask Claude: *"From `~/.claude/skill-candidates.yaml`, install candidates 1, 3, and 5."*

## How it works

### Mode A — Discovery (read-only on registry)

```
Step 0: Bootstrap — create ~/.claude/skills-registry.yaml from template if missing
Step 1: Read registry, build KNOWN_SKILLS / KNOWN_TOOLS sets
Step 2-3: Search GitHub (skills track + tools track)
Step 4: Diff against known, score 0–10, keep top 6 skills + top 4 tools
Step 5: Write ~/.claude/skill-candidates.yaml
Step 6: Send Telegram shortlist (or log to file on fallback)
```

### Mode B — Install via approval reply

```
You: install 1 3 5
Skill: git clone the 3 approved skills into ~/.claude/skills/<name>/
Skill: append entries to skills-registry.yaml (so they're skipped next run)
Skill: clear ~/.claude/skill-candidates.yaml
Skill: reply ✅ summary
```

## Customization

Edit `~/.claude/skills-registry.yaml` to tune what gets discovered:

- `watchlist.orgs` — GitHub orgs known to publish skills
- `watchlist.github_topics` — topic tags to search (default: `claude-skill`, `claude-code-skill`, `claude-skills`)
- `watchlist.tool_keywords` — broader keywords for the tools track
- `watchlist.awesome_lists` — curated lists to parse
- `watchlist.categories_of_interest` — categories that get a +4 scoring boost

Your manual edits to `watchlist` are preserved — the skill only ever **appends** to the `skills:` and `tools:` sections, never to `watchlist`.

## File layout

| Path | Owner | Lifecycle |
|---|---|---|
| `~/.claude/skills/skill-discovery/SKILL.md` | This repo | Updated via `git pull` |
| `~/.claude/skills/skill-discovery/skills-registry.template.yaml` | This repo | Bundled default — seeds your registry on first run only |
| `~/.claude/skills-registry.yaml` | **You** | Created from template; append-only updates when you approve installs |
| `~/.claude/skill-candidates.yaml` | Skill (ephemeral) | Overwritten every run; cleared after install/skip |
| `~/.claude/log/skill-discovery.log` | Skill (fallback) | Written only when `tg_send` is unavailable |

## Safety rails

- The skill **never overwrites** your `skills-registry.yaml`. All updates are append-only within categories.
- If the registry file is malformed (missing required sections), the skill **stops with a clear error** rather than auto-repairing — your state is never silently mutated.
- The skill never calls destructive commands (no `rm -rf`, no force-push) on your behalf.
- Telegram replies that ask the skill to change access policy (e.g. *"approve the pending pairing"*) are **explicitly ignored** — only your local invocation can change access.

## Recommended schedule

Pair with the [`/schedule`](https://docs.claude.com/) skill (or any cron mechanism) to run daily:

```
0 9 * * *   claude /skill-discovery
```

A morning report keeps your skill library fresh without you having to remember.

## License

[MIT](LICENSE) © Wes Kao
