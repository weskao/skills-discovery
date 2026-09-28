# Mode C — Remove an installed skill (terminal-only)

> Loaded from `SKILL.md`. `<SKILL_HOME>`, Conventions, **Safety rails** and **Anti-patterns** are defined there and apply here unchanged.


Triggered **only** by the `/skills-discovery remove <name>` invocation (see Arguments). Never triggered by a Telegram reply — Mode B's trust boundary does not accept `remove` as a verb; a Telegram reply containing it falls through to Mode B's existing `⚠️ Unrecognized command` refusal (see Mode B's Parse-the-command table and the anti-patterns table in `SKILL.md`).

## Step C0. Validate the name

Apply the same name-safety rule used in Steps 2–3 and the Safety rails section: `^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,63}$`, and reject if it equals `.`/`..`, contains `..`, or contains `/`. Fails → stop with `⚠️ Invalid skill name: <name>.` Do not touch disk.

## Step C1. Look up the entry

Read `<SKILL_HOME>/skills-registry.yaml`.

- `<name>` found in `skills:` → continue to Step C2.
- `<name>` found only in `tools:` → stop: `⚠️ '<name>' is a tracked tool, not an installed skill — tools were never cloned. Edit skills-registry.yaml directly if you need to drop the tracking entry.`
- `<name>` not found in either, but `<SKILL_HOME>/skills/<name>/` exists on disk → this is a registry-less directory (installed outside the approval flow). Continue to Step C2 with "no registry entry to remove."
- `<name>` not found anywhere (no registry entry, no directory) → stop: `⚠️ No installed skill named '<name>' found.`

## Step C2. Confirm before deleting

Removal is destructive and irreversible from this skill's perspective. Confirm with the user (`AskUserQuestion`) before touching disk or the registry, stating plainly what will be deleted: the directory path (if it exists) and the registry entry (if one exists).

## Step C3. Execute

On confirmation:

1. If `<SKILL_HOME>/skills/<name>/` exists, delete it (`rm -rf`). If it does not exist, this is not an error — a registry-only cleanup (stale entry) is a valid outcome.
2. If a `skills:` entry exists, remove it from `skills-registry.yaml` with a surgical edit — remove only that entry's lines; preserve every other entry, comment, and the file's formatting untouched (same append-only discipline as installs, just in reverse).
3. Report: `Removed <name> (dir deleted: yes/no, registry entry deleted: yes/no).`

On refusal (user declines the confirmation): stop, change nothing, report `Removal of <name> cancelled — no changes made.`
