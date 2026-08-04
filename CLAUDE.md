# CLAUDE.md

Legal research agent configuration. `.claude/` is the sole source of truth.

## Command Invocation Contract

Every repo Python tool must run via `uv run <entry-point>` from the repo root.
`python*`, `node -e`, `perl -e`, and direct filesystem access to `law-db/` are
forbidden — the `uv run` entry points validate, normalize, and cross-reference on
every operation. Bypassing them introduces silent data corruption.

- `uv run test` after editing any `*.py` file. Full suite must pass.
- `uv run lint-md` after batch-editing tracked `*.md` files. Never `uv run pymarkdownlnt` directly.

## Architecture

- Skills: `.claude/skills/<name>/SKILL.md` owns the full procedure; `.github/skills` are thin wrappers.
- Agents: `.claude/agents/<name>.md` owns the behavior; `.github/agents` are thin wrappers.
- German prose: standard orthography (umlauts, `ß`), not ASCII substitutions.

### Coding Style

Read `.claude/agents/rules/coding-style.md` before editing any Python file.
No abbreviations in names. Functional programming by default — classes only with concrete justification.

### Law DB (`./law-db/`)

All access through the law-db skill (`.claude/skills/law-db/SKILL.md`). Invoke via
`Skill: "law-db"`. Command reference: `.claude/agents/rules/law-db-commands.md`.

### Agent Dispatch

Invoke via Agent tool with `subagent_type: "<name>"` per YAML frontmatter `name` field.
Skills that say "dispatch the X agent" → Agent tool with `subagent_type: "X"`.

### Guidelines

Reference documents live in `.claude/agents/rules/` with `-guidelines.md` suffix —
VCS-tracked. Do not place guideline files in `law-db/guidelines/` (gitignored, ephemeral).

### Script Development

Read `.claude/scripts/DEVELOPER.md` before modifying `.claude/scripts/`.

## Skill Procedure Completion

Post-work steps in a skill are part of the procedure. A skill is not complete until
every step in its SKILL.md is done.
