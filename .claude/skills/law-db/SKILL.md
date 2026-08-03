---
name: law-db
description: >
  Access the law-db archive — search, query, archive, validate, or bootstrap.
  Every read and write to the local archive must go through this skill.
  Never touch law-db/ files directly.
user-invocable: false
---

# law-db

Cross-harness source of truth for the `law-db` skill. Owns all archive access rules, the
command contract, bootstrap logic, and the quick-reference command table.

## When to Use

Any operation that reads from or writes to the local `./law-db/` archive tree. This includes:
checking whether a document is archived; searching the archive by keyword or topic; reading
metadata; listing contents; archiving documents; syncing or validating the index; and running
integrity checks.

Other skills and agents (law-researcher) delegate archive operations to this skill.

## Black-Box Rule

- **Never read, write, or manipulate any file under `./law-db/` directly.** This includes
  `cat`, `head`, `tail`, `jq`, `grep`, `sed`, `awk`, `python3 -c`, `python3` scripts,
  `node -e`, and every other ad-hoc snippet or shell tool.
- The archive is a black box: **every read** goes through `uv run law-db-query ...` or
  `uv run law-db-lookup ...` and **every write** goes through `uv run law-db ...`.
  There are zero exceptions.
- Do not run repo scripts with `python`, `python3`, direct script paths, absolute paths,
  or shebang execution. All repo Python tools run through `uv run ...` from the repo root.
- **If the `uv run` tools don't support a query pattern you need, report it — do not work
  around it with inline code.**
- **`law-db/` is gitignored and ephemeral.** Never create, write, or edit any file under
  `law-db/` manually — not even `mkdir`, `cp`, `mv`, or `rm`. All `law-db/` contents are
  created and managed exclusively by the `uv run law-db*` Python tools. Human-authored
  reference files (source descriptions, guidelines, policies) belong in
  **`.claude/agents/rules/`** (with `-guidelines.md` suffix, e.g. `ris-guidelines.md`) — VCS-tracked directory that ships with the
  repo and is always present on every checkout.

### Forbidden Patterns — Never Do Any of These

These patterns violate the Command Invocation Contract. Each one has been observed
in real sessions. **None of them are acceptable.**

| Forbidden | Why | Use Instead |
|---|---|---|
| `python3 -c "import json; ..."` reading `index.json` | Bypasses validation layer | `uv run law-db-query --search-keyword "..."` |
| `python3 -c "..."` for any law-db operation | Direct file access, no integrity checks | `uv run law-db-lookup --document ...` |
| `jq` / `cat` / `grep` on `law-db/index.json` | Bypasses the tool layer | `uv run law-db-query --list-topics` |
| `python3` or `python` in any form | Forbidden by CLAUDE.md contract | `uv run <entry-point>` |
| `node -e`, `perl -e` touching law-db files | Same bypass, different language | `uv run law-db-*` tools |

## Bootstrap

- `./law-db/` is gitignored and does not ship with the repo.
- Do not create `law-db/` or its subdirectories by hand; the tooling creates the archive
  tree and initial `index.json`.
- To bootstrap a fresh checkout: run any archival command (e.g.
  `uv run law-db --document LEGAL-REF --validate`). The tooling auto-creates the full tree
  (`searches/`, `documents/`, `fulltext/`, `guidelines/`, `web/`) plus `index.json`.
- To verify bootstrap: `uv run law-db-integrity-check --law-db law-db`. An empty archive
  passes if all five directories and `index.json` exist.
- Query and lookup tools are read-only. If they report that `law-db/` is missing, run an
  archival command first.

## Source Policies

Archive access is governed by these reference files. Consult them before archiving,
querying, or analyzing documents from the archive:

| Domain                                              | Reference                                                     |
| --------------------------------------------------- | ------------------------------------------------------------- |
| law-db command reference with every parameter       | `.claude/agents/rules/law-db-commands.md`                     |
| Legal authority standards and search protocol       | `.claude/agents/law-researcher.md`                            |
| Legal text database: Austrian law (jusline.at)      | `.claude/agents/rules/jusline-at-guidelines.md` |
| Legal text database: Austrian law — official (RIS)  | `.claude/agents/rules/ris-guidelines.md`    |
| Legal text database: EU law (EUR-Lex)               | `.claude/agents/rules/eur-lex-guidelines.md` |
| Insurance contract analysis framework              | `.claude/agents/rules/contract-analysis-framework.md`         |
| Insurance and EU regulatory reference              | `.claude/agents/rules/insurance-at-eu-guidelines.md`          |
| Script development conventions                      | `.claude/scripts/DEVELOPER.md`                                |
| Overall integration and CLI contract                | `CLAUDE.md`                                                   |

## Archival Conventions

- Always include `--topic <name>` on archival commands (human-readable name, e.g. `datenschutz`,
  `mietrecht`). The tool derives the kebab-case slug automatically.
- Use `--topic-slug` only when automatic derivation fails.
- For contracts and AGB: use `uv run law-db-contract --type contract|agb|template --file|--url ...`.
  PDFs are stored alongside auto-extracted Markdown (requires `pdftotext` on PATH). See
  `.claude/agents/rules/law-db-commands.md` for the full parameter reference.
- Integrity check runs automatically after every archival operation.
  Errors block completion (exit code 1) and must be fixed immediately.

## During-Session / Real-Time Use

When operating in a live session, only **read-only, local, no-network** commands are
permitted during the session:

| Permitted during session | Must wait until after session |
|---|---|
| `uv run law-db-query --search-keyword "..."` | `uv run law-db --source ... --query "..."` (archival — writes) |
| `uv run law-db-query --list-topics` | `uv run law-db --source ... --query "..."` (network search) |
| `uv run law-db-query --read-metadata "..."` | `uv run law-db --archive-url "..."` (archival — writes) |
| `uv run law-db-lookup --document "..."` | `uv run law-db-integrity-check` (harmless but unnecessary mid-session) |
| `uv run law-db-lookup --url "..."` | `WebSearch`, `WebFetch` for new documents (network) |
| Reading `.claude/agents/rules/*-guidelines.md` | Dispatching `law-researcher` agent (writes to law-db/) |

Read-only commands are sub-second, local, and equivalent to consulting a reference shelf.
Network searches and archival are between-session work.

## Command Reference

All scripts must be invoked via `uv run` from the repo root. Query and lookup scripts
default to JSON; use `--format text` for human-readable output.

For the complete parameter reference with every flag, type, and default, see
`.claude/agents/rules/law-db-commands.md`. The table below is a quick reference for
common operations.

### Archive (`law-db`)

| Operation          | Command                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| Google Scholar     | `uv run law-db --source google-scholar --query '<query>' --topic '<name>'`                       |
| DOAJ search        | `uv run law-db --source doaj --query '<query>' --topic '<name>'`                                 |
| Open Science Dir   | `uv run law-db --source open-science-directory --query '<query>' --topic '<name>'`               |
| Archive URL        | `uv run law-db --archive-url '<URL>' --topic '<name>'`                                           |
| Archive first N    | `uv run law-db --source google-scholar --query '<query>' --archive-first <N> --topic '<name>'`  |
| Migrate (dry run)  | `uv run law-db --migrate-dry-run`                                                                |
| Migrate            | `uv run law-db --migrate`                                                                        |

### Query (`law-db-query`)

| Operation          | Command                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| List topics        | `uv run law-db-query --list-topics`                                                              |
| List docs/topic    | `uv run law-db-query --topic '<slug>'`                                                           |
| Check document     | `uv run law-db-query --check-document '<ID>'`                                                    |
| Read metadata      | `uv run law-db-query --read-metadata '<path>'`                                                   |
| Read + abstract    | `uv run law-db-query --read-metadata '<path>' --show-abstract`                                   |
| Keyword search     | `uv run law-db-query --search-keyword '<term>'`                                                  |
| Scoped keyword     | `uv run law-db-query --search-keyword '<term>' --search-topic '<slug>'`                          |
| Recent documents   | `uv run law-db-query --recent <N>`                                                               |
| Search searches    | `uv run law-db-query --search-searches '<term>'`                                                 |

### External Lookup (`law-db-lookup`)

| Operation          | Command                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| Lookup document    | `uv run law-db-lookup --document <ID>`                                                           |
| Lookup URL         | `uv run law-db-lookup --url <URL>`                                                               |

### Maintenance

| Operation          | Command                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| Integrity check    | `uv run law-db-integrity-check --law-db law-db`                                                  |
| JSON integrity     | `uv run law-db-integrity-check --law-db law-db --json`                                           |
| All tests          | `uv run test`                                                                                    |

### Lint Rules

- After completing edits to any `*.md` file, run `uv run lint-md` (or `uv run lint-md --fix`).
- **Never run `uv run pymarkdownlnt` directly.** Only `uv run lint-md`.
- Canonical test command after editing any `*.py` file: `uv run test`. Full suite must pass.
