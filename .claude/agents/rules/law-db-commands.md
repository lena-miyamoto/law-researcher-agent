---
description: >
  Complete `uv run` parameter reference covering all law-db entry points. Command tables for
  archival, lookup, query, and integrity check operations.
---

# law-db Command Reference

`uv run <entry-point> …` from repo root. Default JSON; `--format text` for readable output.

Direct Python invocation **forbidden**. Access only through `uv run` entry points — validation, indexing, integrity checks always applied.

Web discovery sources: `google-scholar`, `doaj`, `open-science-directory`.
Prefer official legal databases (EUR-Lex, RIS) for primary legal sources.

`law-db-integrity-check` runs after every archival operation. Errors block completion (exit code 1) — fix immediately.

---

## `uv run law-db` — Archival

Archive searches, documents, and web discovery results into local `law-db/` tree. Always include
`--topic` (human-readable name, e.g. `datenschutz`, `mietrecht`). Integrity check runs on completion.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--source` | choice | `google-scholar` | Primary source: `google-scholar`, `doaj`, `open-science-directory` |
| `--query` | str | — | Search query for selected source |
| `--search-slug` | str | — | Optional slug for saved search file |
| `--topic` | str | `uncategorized` | Legal topic for grouping output (e.g. `datenschutz`, `mietrecht`). Kebab-case slug auto-derived |
| `--topic-slug` | str | — | Explicit kebab-case slug; overrides `--topic` |
| `--document` | str[] | `[]` | Document identifier to archive; repeatable |
| `--archive-url` | str[] | `[]` | URL to archive; repeatable |
| `--archive-first` | int | `0` | Also archive first N results returned by `--query` |
| `--retmax` | int | `20` | Machine-readable hits to request for archived search JSON |
| `--law-db` | str | `law-db` | Target `law-db/` directory path |
| `--delay` | float | `0.34` | Delay between fetches (seconds) |
| `--migrate` | flag | off | Migrate flat `law-db/` to topic-based per-document folders |
| `--migrate-dry-run` | flag | off | Preview `--migrate` without copying files |

---

## `uv run law-db-integrity-check` — Validation

Runs after every archival operation. Errors block (exit code 1) — fix immediately.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--law-db` | str | `law-db` | Target `law-db/` directory path |
| `--json` | flag | off | Emit findings as machine-parseable JSON |

---

## `uv run law-db-lookup` — External Lookup (read-only, no archival)

Query external sources. At least one of `--document` or `--url` required.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--document` | str[] | `[]` | Document identifier to look up; repeatable |
| `--url` | str[] | `[]` | URL to look up; repeatable |
| `--format` | choice | `json` | Output format: `json` or `text` |

---

## `uv run law-db-query` — Local Archive Query (read-only)

Query local `law-db/` archive. Exactly one operation flag required (mutually exclusive group).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--law-db` | str | `law-db` | Path to `law-db/` root directory |
| `--format` | choice | `json` | Output format: `json` or `text` |

**Operation (mutually exclusive — pick exactly one):**

| Flag | Type | Description |
|---|---|---|
| `--list-topics` | flag | List all topics with document and search counts |
| `--topic` | str | List all documents under a topic |
| `--check-document` | str | Check if a document identifier is already archived |
| `--read-metadata` | str | Read metadata from a document directory path |
| `--search-keyword` | str | Search documents by keyword (case-insensitive) |
| `--recent` | int | List N most recently added documents |
| `--search-searches` | str | Search archived search queries by keyword (case-insensitive) |

**Modifiers (usable with certain operations):**

| Parameter | Type | Default | Applies to | Description |
|---|---|---|---|---|
| `--search-topic` | str | — | `--search-keyword`, `--search-searches` | Restrict search to a specific topic |
| `--show-abstract` | flag | off | `--read-metadata` | Include abstract text in output |
| `--summary` | flag | off | `--search-keyword` | Compact output (identifiers + titles only) |
