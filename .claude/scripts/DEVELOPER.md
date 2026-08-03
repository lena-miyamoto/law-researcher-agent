---
description: >
  Internal law-db directory structure and conventions. Only relevant when extending the script stack
  in .claude/scripts/ — never when using uv run entry points.
---

# law-db Developer Notes

Internal directory structure and conventions. **Only relevant when extending the law-db script
stack.** Agents and skills must never manipulate `law-db/` directly — all access goes through the
`uv run` entry points documented in `../agents/rules/law-db-commands.md`.

## Directory Structure (`./law-db/`)

Lowercase kebab-case names. `./law-db/index.json` mandatory — every entry listed there.
Update `index.json` with every new or moved archive.

**IMPORTANT:** `law-db/` is gitignored and ephemeral — auto-created on first use, never
shipped with the repo. **All instruction files must live in `.claude/` (VCS-tracked).**
Do not manually create or edit files in `law-db/` — that is the exclusive domain of the
`uv run law-db*` Python tools. The `guidelines/` directory inside `law-db/` holds
machine-generated guideline data produced by the tooling, **not** human-authored
reference documents. Human-authored source reference documents belong in
`.claude/agents/rules/` (with `-guidelines.md` suffix).

Required top-level categories:

- `searches/<topic-slug>/` — machine-readable JSON (`uncategorized/` when no topic specified).
- `documents/<topic-slug>/<identifier>-<title-slug>/` — `metadata.json` + `abstract.txt`. Never split across dirs.
- `fulltext/<topic-slug>/<identifier>-<title-slug>/` — `source.md` with YAML frontmatter + `metadata.json`.
- `guidelines/<topic-slug>/<title-slug>/` — `source.<lang>.md` with YAML frontmatter.
- `web/<topic-slug>/` — archived web pages or reproducible search definitions.
- `contracts/<topic-slug>/<identifier-slug>/` — `metadata.json` + optional `source.pdf` + optional `source.md`.
  Supports `contract`, `agb`, and `template` types. PDF originals stored alongside extracted Markdown
  for full-text search. Never split across dirs.

## Conventions

- **Document standard:** `documents/`: `metadata.json` + `abstract.txt`. `fulltext/`: `source.md` + `metadata.json`.
  No intermediate artifacts.
- **YAML frontmatter** on every source file: `title`, `authors`, `source`, `source_url`, `access_date`
  (YYYY-MM-DD), `language`, `extraction_notes`.
- **Source priority:** `index.json` → `searches/` → fetch. Google Scholar → DOAJ / open-access directories.
- Flag authority per `law-researcher` Legal Authority Hierarchy (`../agents/law-researcher.md`).
  Reusable write-ups → `tmp/`, not overwriting source briefs or archived records.
