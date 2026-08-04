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
| `--exclude-expired` | flag | With `--search-keyword`: omit documents whose `access_date` is older than 365 days. Missing/unparseable dates are retained. |
| `--recent` | int | List N most recently added documents |
| `--search-searches` | str | Search archived search queries by keyword (case-insensitive) |

**Modifiers (usable with certain operations):**

| Parameter | Type | Default | Applies to | Description |
|---|---|---|---|---|
| `--search-topic` | str | — | `--search-keyword`, `--search-searches` | Restrict search to a specific topic |
| `--show-abstract` | flag | off | `--read-metadata` | Include abstract text in output |
| `--summary` | flag | off | `--search-keyword` | Compact output (identifiers + titles only) |

---

## `uv run law-db-contract` — Contract and AGB Archival

Archive insurance contracts, AGB, and templates into `law-db/contracts/`.
Stores PDF originals alongside automatically extracted Markdown for full-text search.
Requires `pdftotext` (poppler-utils) on PATH for PDF→Markdown extraction.

**Required parameters:**

| Parameter | Type | Description |
|---|---|---|
| `--type` | choice | `contract`, `agb`, or `template` |
| `--title` | str | Human-readable title for the document |
| `--file` xor `--url` | — | One of `--file <path>` or `--url <url>` (not both) |

**Optional parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--topic` | str | `uncategorized` | Topic for grouping (e.g. `versicherung`, `haushalt`) |
| `--topic-slug` | str | — | Explicit kebab-case slug; overrides `--topic` |
| `--parties` | str | — | Comma-separated list of parties |
| `--contract-date` | str | — | Contract date in YYYY-MM-DD format |
| `--status` | choice | — | `template`, `pending`, `active`, or `terminated` |
| `--insurance-type` | choice | — | e.g. `haushalt`, `rechtsschutz`, `kfz`, `private-krankenversicherung` |
| `--language` | str | `de` | Language code for the document |
| `--source-url` | str | — | Original source URL for reference |
| `--notes` | str | — | Free-text notes |
| `--identifier-slug` | str | auto | Explicit kebab-case folder slug; auto-generated from title |
| `--law-db` | str | `law-db` | Target law-db directory |

**Directory layout:** `contracts/<topic>/<identifier-slug>/` containing:

- `metadata.json` — structured metadata (type, title, parties, dates, has_pdf, has_markdown)
- `source.pdf` — original PDF (if provided)
- `source.md` — extracted Markdown (if extraction succeeded)

---

## `uv run law-db-receipt` — Tax Document Archival

Archive tax documents (receipts, broker statements, medical honoraria) into
`law-db/receipts/`. Stores PDF originals alongside automatically extracted
Markdown, and CSV originals for broker/bank exports. Requires `pdftotext`
(poppler-utils) on PATH for PDF→Markdown extraction.

**Required parameters:**

| Parameter | Type | Description |
|---|---|---|
| `--type` | choice | `receipt`, `medical_honorarium`, `broker_statement`, `business_expense`, `income_document`, `salary_statement`, `bank_statement`, or `other` |
| `--title` | str | Human-readable title for the tax document |
| `--tax-category` | choice | `werbungskosten`, `sonderausgaben`, `aussergewoehnliche_belastung`, `einkuenfte_aus_kapitalvermoegen`, `einkuenfte_aus_selbststaendiger_arbeit`, `einkuenfte_aus_nichtselbststaendiger_arbeit`, `umsatzsteuer_vorsteuer`, or `other` |
| `--file` xor `--url` | — | One of `--file <path>` or `--url <url>` (not both) |

**Optional parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--topic` | str | `uncategorized` | Topic for grouping (e.g. `arztrechnung`, `flatex`, `finanzamt`) |
| `--topic-slug` | str | — | Explicit kebab-case slug; overrides `--topic` |
| `--payer` | str | — | Entity that issued the document (e.g. doctor, broker, employer) |
| `--payee` | str | — | Entity that received the document (typically the taxpayer) |
| `--amount` | float | — | Monetary amount in the document currency |
| `--currency` | str | `EUR` | ISO 4217 currency code |
| `--document-date` | str | — | Date on the document in YYYY-MM-DD format |
| `--tax-period` | str | — | Tax period in YYYY format (e.g. `2025`) |
| `--language` | str | `de` | Language code for the document |
| `--source-url` | str | — | Original source URL for reference |
| `--notes` | str | — | Free-text notes |
| `--identifier-slug` | str | auto | Explicit kebab-case folder slug; auto-generated from title |
| `--law-db` | str | `law-db` | Target law-db directory |

**Directory layout:** `receipts/<tax_category>/<topic>/<identifier-slug>/` containing:

- `metadata.json` — structured metadata (subtype, title, tax_category, payer, payee, amount, dates, has_pdf, has_markdown, has_csv, csv_row_count, csv_columns)
- `source.pdf` — original PDF (if provided)
- `source.md` — extracted Markdown (if extraction succeeded)
- `source.csv` — original CSV data (if provided)
