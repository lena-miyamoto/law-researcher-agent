# Tax Advisor Agent Implementation Plan

## Context

The repo has two agents (law-researcher, insurance-broker) with a structured pattern: `.claude/agents/<name>.md` source of truth, `.github/agents/<name>.agent.md` thin wrapper, phased workflows, and rule/guideline files in `.claude/agents/rules/`. The user wants a tax advisor agent that acts in the user's best interest (analogous to the insurance-broker's fiduciary duty), dispatches `law-researcher` sub-agents for legal research, parses tax documents (receipts, medical honoraria, investment broker PDFs/CSVs), and provides evidence-backed tax recommendations under Austrian personal income tax law.

## Scope decisions (confirmed by user)

- **Tax domain**: Austrian personal income tax (Einkommensteuer/EStG)
- **Tooling**: New `uv run law-db-receipt` entry point for tax document archiving into `law-db/receipts/`
- **CSV parsing**: New `parse_csv_rows` function in `utils.py` (stdlib `csv` only, no new dependencies)

---

## Files to create

### 1. `.claude/agents/tax-advisor.md` (~220 lines)

Pattern: mirror `insurance-broker.md` (209 lines) exactly. YAML frontmatter with `name: tax-advisor`, `tools: Read, Grep, WebFetch, WebSearch, Agent, Bash, Edit, Write`, `model: inherit`. Sections:

- **Best Interest Duty** (first, before Role — analogous to Fiduciary Duty). Non-negotiable imperative: act in user's best interest, never favor tax authority, disclose conflicts, default to user protection when uncertain, evidence standards for "common practice" claims.
- **Role and Core Responsibilities**: Tax document analysis, receipt categorization, broker statement analysis, deduction optimization (Werbungskosten, Sonderausgaben, außergewöhnliche Belastungen), tax law research via `law-researcher` sub-agent. Default: Austrian tax law.
- **Primary Legal Framework**: EStG, UStG (limited), BAO, EU tax directives. Pointer to `rules/austrian-tax-law-guidelines.md`.
- **6-Phase Workflow**:
  1. Intake and Scoping — identify income types, tax-relevant expenses, existing documents, tax period. ASK if anything ambiguous.
  2. Document Analysis — read tax documents (PDFs, CSVs), apply `tax-document-analysis-framework.md`, categorize items, flag tax-relevant entries
  3. Tax Law Research — dispatch `law-researcher` sub-agents for specific legal questions. Batch related questions. Clear dispatch criteria (when to/not to).
  4. Tax Optimization Analysis — identify deduction opportunities, optimal filing strategies, risk assessment
  5. Synthesis — weigh evidence, build recommendation chain, never hide uncertainty
  6. Output — structured report (see below)
- **Output Format**: Tax situation summary, document analysis, legal assessment (with law-researcher findings), optimization recommendations, risk disclosure, sources.
- **Jurisdictional Default**: Austria. Key institutions: BMF, Finanzamt, BFG, VwGH, EuGH. Key databases: ris.bka.gv.at, Findok (findok.bmf.gv.at), BMF rulings.
- **Rules File Pointers**: `austrian-tax-law-guidelines.md`, `tax-document-analysis-framework.md`.
- **Phase/Tools table**: Quick-reference mapping phases to primary tools.
- **Document archival instructions**: How to use `uv run law-db-receipt` to archive tax documents.

### 2. `.github/agents/tax-advisor.agent.md` (~17 lines)

Thin wrapper following `insurance-broker.agent.md` pattern exactly: Copilot frontmatter (model: GPT-5, tools: [read, search, execute, web, todo]), single-line body pointing to `.claude/agents/tax-advisor.md`.

### 3. `.claude/agents/rules/austrian-tax-law-guidelines.md` (~180 lines)

Follow `insurance-at-eu-guidelines.md` format (121 lines, German, YAML frontmatter with source metadata). Content:

- EStG income categories (§§ 21-29): Land- und Forstwirtschaft, selbstständige Arbeit, Gewerbebetrieb, nichtselbstständige Arbeit, Kapitalvermögen, Vermietung und Verpachtung, sonstige Einkünfte
- Deduction categories: Werbungskosten (§ 16), Sonderausgaben (§ 18), außergewöhnliche Belastungen (§§ 34-35), Freibeträge
- Tax rates: progressive brackets, KESt 27.5%, special rates
- UStG: VAT rates (20/10/13%), Kleinunternehmerregelung (§ 6(1)Z27)
- BAO: procedural law, statute of limitations (§§ 207-209), audit procedures
- Key institutions with URLs: BMF, Finanzamt, BFG, VwGH, EuGH
- Key databases with quality/bias ratings: ris.bka.gv.at (tax sections), Findok, BMF rulings, EUR-Lex (EU tax directives)
- EU tax directives: ATAD, DAC, Parent-Subsidiary, Interest-Royalty
- Permitted research domains table with data quality and bias-risk ratings

### 4. `.claude/agents/rules/tax-document-analysis-framework.md` (~180 lines)

Follow `contract-analysis-framework.md` format (75 lines, German). Content:

- Document categories table: Honorarnote (medical receipt), Rechnung (invoice), Beleg (receipt), Depotauszug/Jahressteuerreport (broker statement), Kontoauszug (bank statement), Lohnzettel (salary statement), Fondsmitteilung (fund report), Steuerbescheid (tax assessment)
- Receipt analysis: fields to extract (payer, payee, amount, date, purpose, tax category), EStG references per category
- Broker statement analysis: dividends (KESt treatment), realized gains/losses (tax-relevant vs exempt), interest income, foreign withholding tax (DBA credit), transaction fees (not deductible), FX gains/losses, ausschüttungsgleiche Erträge (accumulating funds)
- Red-flag text patterns (German): `Honorar`, `Umsatzsteuer`, `Kapitalertragsteuer`, `Quellensteuer`, `realisierter Gewinn`, `Anschaffungskosten`, `ausschüttungsgleicher Ertrag`, `Thesaurierung`, `Zwischendividende`, `AGB-Änderung`, `Steuerreport`, `Jahressteuerreport`
- Document categorization decision tree
- Structured analysis methodology: step-by-step per document type, EStG section references

### 5. `.claude/scripts/law-db-receipt.py` (~350 lines)

Template: `law-db-contract.py` (322 lines). Key differences:

- **Subtype enum**: `receipt`, `medical_honorarium`, `broker_statement`, `business_expense`, `income_document`, `salary_statement`, `bank_statement`, `other`
- **Tax category enum**: `werbungskosten`, `sonderausgaben`, `aussergewoehnliche_belastung`, `einkuenfte_aus_kapitalvermoegen`, `einkuenfte_aus_selbststaendiger_arbeit`, `einkuenfte_aus_nichtselbststaendiger_arbeit`, `umsatzsteuer_vorsteuer`, `other`
- **Metadata fields**: `payer`, `payee`, `amount`, `currency`, `document_date`, `tax_period`, `tax_category`, `has_pdf`, `has_markdown`, `has_csv`
- **CSV handling**: If `--file` is `.csv`, parse with `utils.parse_csv_rows()`, save `source.csv`, populate metadata
- **Archive destination**: `law-db/receipts/<tax_category>/<identifier-slug>/`
- **Bootstrap**: create `receipts/` directory alongside existing dirs
- **Integrity check**: call `utils.verify_and_report_integrity` on completion
- **Index sync**: call `law_db.sync_index` with receipt updates

### 6. `tests/test_law_db_receipt.py` (~200 lines)

Test classes following `test_law_db.py` pattern: `TestValidateReceiptSubtype`, `TestValidateTaxCategory`, `TestArchiveReceiptPdf`, `TestArchiveReceiptCsv`, `TestReceiptMetadata`, `TestSyncIndexReceipts`. Uses temp dirs for isolation.

---

## Files to modify

### 7. `.claude/scripts/utils.py` — 3 additions, 1 new function

Additions (follow the `contracts` pattern exactly):

- **Line ~332**: Add `CATEGORY_RECEIPT = "receipt"` constant after `CATEGORY_CONTRACT`
- **Line 361**: Add `"receipts"` to `check_required_dirs` tuple (currently 6 items)
- **Line 428**: Add `"receipts"` to `expected_keys` set in `check_index_valid`
- **Line ~518-524**: Add receipt entries to `check_index_crossref` tuple: `index_receipts = _indexed_paths(data, "receipts")` and add `("receipt", index_receipts, actual_receipts, CATEGORY_RECEIPT)` to the loop
- **New function `check_receipts_integrity(root, findings)`** (~80 lines, after `check_contracts_integrity`): validates `metadata.json` JSON, checks subtype validity, validates `source.pdf`/`source.md`/`source.csv` existence, checks for empty files
- **Line ~969**: Add `check_receipts_integrity(root, findings)` after `check_contracts_integrity` call in `run_integrity_check`
- **New function `parse_csv_rows(file_path, delimiter=",", encoding="utf-8")`** (~25 lines, placed near existing utility functions): uses `csv.DictReader`, returns `list[dict[str, str]]`, skips empty rows, handles encoding. Local import `import csv as _csv` to keep function pure.

### 8. `.claude/scripts/law-db.py` — 3 small additions

- **Line 56**: Add `"receipts"` to `ensure_law_db_structure` tuple
- **Lines ~225-240**: Add receipts collection in `collect_index_data` (follow contracts pattern)
- **Lines ~278**: Add `"receipts"` to the `sync_index` data dict

### 9. `.claude/scripts/entrypoints.py` — 1 new function (~4 lines)

Add `law_db_receipt()` function after `law_db_contract()`:
```python
def law_db_receipt():
    return _load_script("law_db_receipt", "law-db-receipt.py").main()
```

### 10. `pyproject.toml` — 1 new entry point

Add `law-db-receipt = "entrypoints:law_db_receipt"` to `[project.scripts]`.

### 11. `tests/conftest.py` — 1 line

Add `_load_module("law_db_receipt", "law-db-receipt.py")` to `pytest_configure`.

### 12. `tests/test_utils.py` — new test class (~30 lines)

Add `TestParseCsvRows` class: basic parsing, empty file, header-only, custom delimiter, missing values, UTF-8 with BOM, rows with empty values skipped.

### 13. `CLAUDE.md` — 2 edits

- **Line 102**: Add `tax-advisor` to available agents list: `Available agents: law-researcher (legal research), insurance-broker (insurance contract analysis, regulatory compliance, and market comparison), tax-advisor (tax document analysis, Austrian and EU tax law research, and tax optimization).`
- **Line 109**: Add `austrian-tax-law-guidelines.md`, `tax-document-analysis-framework.md` to the guidelines example list (alongside existing `ris-guidelines.md`, `eur-lex-guidelines.md`).

### 14. `.claude/agents/rules/law-db-commands.md` — add receipt section (~20 lines)

Add `law-db-receipt` command reference table following the `law-db-contract` pattern: parameters, types, defaults, descriptions.

### 15. `.claude/skills/law-db/SKILL.md` — add receipt entries

Add `law-db-receipt` to: the Command Reference table (Archive section), the Source Policies table, and the Forbidden Patterns table (add receipt equivalents).

---

## Implementation sequence

1. **Add `parse_csv_rows` to utils.py** + tests → `uv run test`
2. **Add receipts integrity checks to utils.py** (CATEGORY_RECEIPT, check_required_dirs, expected_keys, check_index_crossref, check_receipts_integrity, run_integrity_check call) → `uv run test`
3. **Update law-db.py** (ensure_law_db_structure, collect_index_data, sync_index) → `uv run test`
4. **Create law-db-receipt.py** → `uv run test`
5. **Wire entrypoints.py + pyproject.toml + conftest.py** → verify `uv run law-db-receipt --help`
6. **Create test_law_db_receipt.py** → `uv run test`
7. **Create austrian-tax-law-guidelines.md** → `uv run lint-md`
8. **Create tax-document-analysis-framework.md** → `uv run lint-md`
9. **Create tax-advisor.md agent** → `uv run lint-md`
10. **Create .github/agents/tax-advisor.agent.md** wrapper
11. **Update CLAUDE.md** (agents list + guidelines) → `uv run lint-md`
12. **Update law-db-commands.md + law-db SKILL.md** → `uv run lint-md`

## Verification

- `uv run test` — full suite passes (no regressions, new tests pass)
- `uv run lint-md` — no violations
- `uv run law-db-receipt --help` — prints help text
- `uv run law-db-receipt --type receipt --title "Test Receipt" --file /path/to/test.pdf --tax-category werbungskosten` — archives successfully, integrity check passes
- Agent invoked via `Agent(subagent_type: "tax-advisor")` — loads and follows phased workflow
- Sub-agent dispatch: tax-advisor dispatches `law-researcher` for legal questions (e.g., "Are medical honoraria from a Wahlarzt deductible as außergewöhnliche Belastung under EStG § 34?")
