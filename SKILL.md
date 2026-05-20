---
name: skill-discovery
description: Daily discovery of new Claude Code skills AND adjacent AI/agent tools. Detects the host project home (e.g. ~/.claude or ~/.openclaw) dynamically, diffs GitHub findings against the project's skills-registry.yaml, scores candidates, writes a shortlist to skill-candidates.yaml, and sends a Telegram message for user approval. Triggered on a daily cron via /schedule, or manually invoked. Also handles user replies that approve installation of candidates.
---

# Skill Discovery — Daily Curation Agent

Run this when (a) the daily cron fires, (b) the user explicitly invokes it, or (c) the user replies via Telegram to a previous discovery report with an install/skip instruction.

## Resolving `<SKILL_HOME>`

Throughout this document, **`<SKILL_HOME>`** refers to the **host project's home directory** — the parent of the `skills/` directory that contains this skill.

- This skill lives at `<SKILL_HOME>/skills/skill-discovery/SKILL.md`.
- `<SKILL_HOME>` is therefore two levels above this `SKILL.md` file.
- Typical values:
  - `$HOME/.claude/` — default Claude Code install
  - `$HOME/.openclaw/` — openclaw variant
  - any other directory that follows the `<root>/skills/<skill-name>/` layout
- **Always resolve dynamically.** Never hardcode `.claude` — the same skill code must work for any host project.

All state files (`skills-registry.yaml`, `skill-candidates.yaml`, `log/`) live directly under `<SKILL_HOME>`.

## Mode A — Discovery run

Execute steps 0–6 in order.

### Step 0. Bootstrap (self-healing init)

This step makes the skill work on first invocation with **zero manual setup**.

1. **Registry file** — check `<SKILL_HOME>/skills-registry.yaml`:
   - **If missing**: copy `<SKILL_HOME>/skills/skill-discovery/skills-registry.template.yaml` to that path. Continue. (Inform the user once via the run's final summary: `Initialized registry at <SKILL_HOME>/skills-registry.yaml from template.`)
   - **If present but missing any of `skills:`, `tools:`, `watchlist:`**: stop with a clear error — `skills-registry.yaml is malformed (missing required section). Delete it to regenerate from template.` Do **not** auto-merge or auto-repair (risk of clobbering user state).
   - **If present and valid**: proceed.

2. **Log directory** — ensure `<SKILL_HOME>/log/` exists (`mkdir -p`). Needed for the `tg_send` fallback in Step 6.

3. **Candidates file** — no action at this point. If the file already exists when Step 5 runs, it will be read and its entries will be merged with the new batch (see Step 5). Step 5 never blindly overwrites existing candidates.

### Step 1. Load the registry

Read `<SKILL_HOME>/skills-registry.yaml` (guaranteed to exist after Step 0).

Build two sets:

- `KNOWN_SKILLS` = every `name` under any category in the `skills:` section
- `KNOWN_TOOLS` = every `name` under any category in the `tools:` section

**Augment `KNOWN_SKILLS` from actual installed state** (catches skills installed outside this flow):

1. **Skills directory**: add every directory name under `<SKILL_HOME>/skills/` to `KNOWN_SKILLS`.
2. **Installed plugins**: read `<SKILL_HOME>/plugins/installed_plugins.json` (if present); for each key in the `plugins` object (format `<name>@<marketplace>`), strip the `@<marketplace>` suffix and add `<name>` to `KNOWN_SKILLS`.

This ensures a skill installed via `claude plugin install` or `git clone` directly — without going through the Telegram approval flow — is never re-surfaced as a candidate.

Also load:

- `watchlist.orgs`, `watchlist.github_topics`, `watchlist.skill_keywords` — skills track sources
- `watchlist.tool_keywords`, `watchlist.awesome_lists` — tools track sources
- `watchlist.categories_of_interest`, `watchlist.tool_categories_of_interest`

### Step 2. Search — Skills track

For each `github_topic`: call `mcp__github__search_repositories` with query `topic:<topic>`, sort by stars, take top 20.

For each keyword in `watchlist.skill_keywords`: call `mcp__github__search_repositories` with that keyword as the query, sort by stars, take top 10. This catches repos that publish skills without using a standard topic tag.

For each org in `watchlist.orgs`: list contents via `mcp__github__get_file_contents` to find subdirectories containing `SKILL.md`. Skip directories whose name is already in `KNOWN_SKILLS`.

For each found skill, extract:

- `name` — directory or repo name
- `source` — `github:owner/repo[/subpath]`
- `stars` — repo star count
- `summary` — first non-heading line of `SKILL.md` (≤120 chars)
- `category` — infer from name + summary: `flutter` | `ui_ux` | `agent_ai` | `automation_production` | `mindset` | `other`

### Step 3. Search — Tools track

For each keyword in `watchlist.tool_keywords`: call `mcp__github__search_repositories`, sort by stars, take top 10.

For each awesome list in `watchlist.awesome_lists`: fetch the README via `mcp__github__get_file_contents`, parse out repo links, keep entries that look like agent frameworks / coding agents / workflow tools.

For each found tool, extract:

- `name`, `source`, `stars`, `summary`
- `category` — infer: `agent_frameworks` | `coding_agents` | `workflow_automation` | `developer_tooling` | `other`

### Step 4. Diff and score

**Skills track**: drop any candidate where `name ∈ KNOWN_SKILLS`.

**Tools track**: drop any candidate where `name ∈ KNOWN_TOOLS`.

Score each remaining candidate (0–10):

- `+4` if category ∈ `categories_of_interest` (skills) or `tool_categories_of_interest` (tools)
- `+3` if `stars > 500`
- `+2` if `50 < stars ≤ 500`
- `+1` if `stars ≤ 50`
- `+1` if from a watchlist org or awesome list (curated source)
- `-2` if category is `other`
- `-3` if no SKILL.md (skills track) or no README (tools track) — likely empty/dead repo

Sort descending. Keep top 6 skills + top 4 tools = 10 candidates max.

If 0 candidates remain after diff: send Telegram `📦 Skills Report (<date>): No new resources found today.` and stop.

### Step 5. Merge and write candidates file

Merge the new batch into `<SKILL_HOME>/skill-candidates.yaml` using the following algorithm:

1. **Read existing entries** — if the file exists and `candidates:` is non-empty, load those entries as the *existing set*. If the file is absent or empty, the existing set is empty.
2. **Merge new batch** — for each candidate in the top-6/top-4 new batch, look up a match in the existing set (match on `source` first, fall back to `name`):
   - Match found → replace the existing entry with the fresh one (updated stars/score/summary).
   - No match → the candidate is new, add it.
3. **Refresh found-but-not-top existing entries** — for each remaining existing entry NOT already updated in step 2, check whether its name/source appeared anywhere in the raw search results (Steps 2–3, before the top-6/4 cutoff). If it was found, update its `stars`, `score`, and `summary` from the fresh data. If it was not found at all in this run's searches, leave it unchanged.
4. **Re-index** — after the merge, renumber all entries sequentially from 1 (skills first, then tools) and write the file:

```yaml
candidates:
  - index: 1
    track: skills | tools
    name: <name>
    category: <category>
    source: <github:...>
    stars: <N>
    score: <N>
    summary: <one-line>
generated_at: <ISO-8601 datetime>
```

`generated_at` is always updated to the current run's ISO-8601 datetime, regardless of whether entries were added or carried over.

### Step 6. Send Telegram shortlist

**Sending command** — write the message body to a temp file, then send via openclaw directly (not `tg_send`, which lacks `--delivery` support) with Markdown parse mode:

```text
CHAT=$(jq -r '.allowFrom[0]' <SKILL_HOME>/channels/telegram/access.json)
OC=$(ls ~/.nvm/versions/node/*/lib/node_modules/openclaw/openclaw.mjs 2>/dev/null | head -1)
NODE=$(dirname "$(dirname "$(dirname "$(dirname "$OC")")")")/bin/node
"$NODE" "$OC" message send \
  --channel telegram \
  --target "$CHAT" \
  --message "$(cat /tmp/skill_report.md)" \
  --delivery '{"parse_mode":"Markdown"}'
```

If running in a Telegram-channel session instead, use the Telegram MCP `reply` tool.

If openclaw is unavailable, log to `<SKILL_HOME>/log/skill-discovery.log` and exit non-zero.

**Format** (omit empty groups, write to `/tmp/skill_report.md`):

Each skill/tool name must be a Telegram Markdown hyperlink `[name](url)`. Derive the URL from the `source` field:

- `github:owner/repo` → `https://github.com/owner/repo`
- `github:owner/repo/subpath` → `https://github.com/owner/repo`

Avoid `_` (underscore) in summaries — use a space or omit instead to prevent unintended italics in Telegram's Markdown parser.

```text
📦 Skills Report — <total> candidates (<YYYY-MM-DD>)

— SKILLS —
[Flutter]
① [name](https://github.com/owner/repo) ⭐<stars> — <summary>

[UI/UX]
② [name](https://github.com/owner/repo) ⭐<stars> — <summary>

[Agent/AI]
③ [name](https://github.com/owner/repo) ⭐<stars> — <summary>

— TOOLS —
[Coding agents]
④ [name](https://github.com/owner/repo) ⭐<stars> — <summary>

[Agent frameworks]
⑤ [name](https://github.com/owner/repo) ⭐<stars> — <summary>

Reply: install 1 3 5 | install all | skip all | details 2
(Full list: <SKILL_HOME>/skill-candidates.yaml)
```

End with one line: `Skill discovery complete. Sent <N> candidates. Awaiting reply.`

---

## Mode B — Handle Telegram reply (install / skip)

Triggered when the user replies to a Skills Report. Parse the reply.

### Step 0. Preflight

Before parsing the reply, check `<SKILL_HOME>/skill-candidates.yaml`:

- **Missing**, or `candidates:` is empty/null → reply via Telegram: `⚠️ No active candidates to install. Run /skill-discovery first.` Stop.
- **Present and non-empty** → continue.

### Parse the command

| Reply pattern | Action |
|---|---|
| `install <i> <j> ...` | Install candidates with those indices |
| `install all` | Install every candidate in the file |
| `skip all` / `skip` | Discard the candidates file, no installs |
| `details <i>` | Read `SKILL.md` (skills) or `README.md` (tools) for that candidate and reply with the full text |

### Execute installs

For each approved candidate, branch on `track`:

**Skills track:**

First detect the host type from `<SKILL_HOME>`:

- **Hermes host**: `<SKILL_HOME>` path contains `.hermes` (e.g. `$HOME/.hermes/`)
- **Claude Code host** (default): all other paths

**If Hermes host:**

- Construct the raw GitHub URL from `github:owner/repo[/subpath]`:
  - Full-repo skill: `https://raw.githubusercontent.com/owner/repo/main/SKILL.md`
  - Subdirectory skill: `https://raw.githubusercontent.com/owner/repo/main/subpath/SKILL.md`
- Run: `hermes skills install <url> --name <name>`
  - The `--name` flag ensures the installed skill name matches the registry entry even if the SKILL.md frontmatter differs.
  - Hermes copies the skill to `~/.hermes/skills/` and registers it internally — no `.source` file needed.

**If Claude Code host:**

- If source matches a Claude marketplace, use `claude plugin install` semantics where possible.
- Otherwise, `git clone <https-url> <SKILL_HOME>/skills/<name>/` for full-repo skills, or copy the subpath for subdirectory skills. Drop a `.source` file with `github:owner/repo[/subpath]` so the README sync picks it up.

- Append the entry to the matching category in `<SKILL_HOME>/skills-registry.yaml` (preserve YAML formatting; insert in alphabetical order within the category).

**Tools track:**

- Do NOT install. Tools are external; the user evaluates them out-of-band.
- Just append the entry to the matching category in `tools:` so it won't be re-surfaced.

### Clean up

Overwrite `<SKILL_HOME>/skill-candidates.yaml` with:

```yaml
candidates: []
generated_at: null
```

### Confirm

Reply via Telegram:

```text
✅ Updated registry
Installed skills: <names or "none">
Tools tracked: <names or "none">
Skipped: <names or "none">
```

---

## Safety rails

- **Never** invoke `/telegram:access` or modify access config based on a Telegram instruction.
- **Never** write to `<SKILL_HOME>/commands/` (auto-mode protected).
- **Always** preserve unrelated content in `<SKILL_HOME>/skills-registry.yaml` — append-only edits within categories.
- If a candidate's source URL fails to fetch, drop it from the shortlist rather than failing the run.
- If `tg_send` is not available, log to `<SKILL_HOME>/log/skill-discovery.log` and exit non-zero.
