---
name: explain-law
description: >
  Explain an Austrian or EU law or case: fetch the official text, archive it, summarize
  what it is about and its most important points, then answer follow-up questions
  interactively. Delegates deep research to the law-researcher agent.
argument-hint: "<law name, abbreviation, case ref, or CELEX (e.g. ABGB, DSGVO, C-43/24, 32016R0679)>"
user-invocable: true
---

# explain-law

Fetch, archive, and explain Austrian or EU laws and cases. Interactive Q&A.
Delegates deep research to law-researcher agent.

## When to Use

User asks: "what is X?", "explain law Y", "was ist das ABGB?", "erklär mir die DSGVO",
"what does the MRG say?", provides a CELEX number or RIS reference, or a case reference
like "C-43/24", "5Ob234/20b", "AZ C-43/24".

## Procedure

### 1. Parse Input — Document Type & Jurisdiction Detection

Classify input as **statute** or **case**. Then detect jurisdiction.

**Case references (handle with streamlined case-law procedure below):**

| Pattern | Court | Jurisdiction | Examples |
|---------|-------|-------------|----------|
| `C-<num>/<yy>` or `C-<num>/<yy> P` | CJEU (Court of Justice) | EU | C-43/24, C-4/23 P |
| `T-<num>/<yy>` | CJEU (General Court) | EU | T-123/24 |
| CELEX starting with `6` (case law sector) | CJEU | EU | 62024CJ0043, 62024CN0043 |
| `AZ C-<num>/<yy>` (German "Aktenzeichen" prefix) | CJEU | EU | AZ C-43/24 |
| `<digits>Ob<num>/<digits><letter>` | OGH (Austrian Supreme Court) | AT | 5Ob234/20b |
| `Ra <year>/<num>/<num>` or `Ro <year>/<num>/<num>` | VwGH (Austrian Admin Court) | AT | Ra 2020/01/0123 |
| `G <num>/<yy>` or `B <num>/<yy>` | VfGH (Austrian Constitutional Court) | AT | G 123/24, B 456/23 |
| `GZ <anything>` (Austrian Geschäftszahl) | Austrian courts | AT | GZ A7/99 |

**Statute references (existing procedure):**

| Pattern | Jurisdiction | Examples |
|---------|-------------|----------|
| Short German acronym (2–5 letters, all caps) | Austrian | ABGB, StGB, MRG, KSchG, UGB, EStG, BAO |
| "DSGVO" or "GDPR" | EU (GDPR = DSGVO) | DSGVO, GDPR |
| CELEX number (`3xxxxXxxxx`) | EU | 32016R0679 |
| Regulation/Directive number | EU | VO 2016/679, RL 2006/123 |
| "EU-", "EU " prefix | EU | EU-Datenschutz-Grundverordnung |
| Full German name | Austrian | Allgemeines bürgerliches Gesetzbuch |
| RIS reference (`BGBl. I Nr. …`) | Austrian | BGBl. I Nr. 33/2022 |

If ambiguous → ask: "Is this Austrian law or EU law?"
If no law name clear → ask: "Which law would you like me to explain?"

---

### Streamlined Case-Law Procedure

> **Core principle: one deterministic URL, one primary fetch, then present.**
> Do NOT scattergun WebSearch + parallel WebFetch. Case reference encodes the URL —
> derive directly.

#### Step C1: Derive CELEX / URL from Case Reference

**CJEU cases:**

```text
C-{num}/{yy}    → CELEX 620{yy}CJ{num-4-digits}
T-{num}/{yy}    → CELEX 620{yy}TJ{num-4-digits}
C-{num}/{yy} P  → CELEX 620{yy}CJ{num-4-digits} (appeal; same CELEX, different document)
```

Pad the case number to 4 digits: `43` → `0043`. Append `P` after CELEX for appeal judgments.

```text
C-43/24 → 62024CJ0043
C-4/23  → 62023CJ0004
```

Construction:

```text
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:620<yy>CJ<num-4-digits>
```

For Advocate General Opinions (if specifically requested), substitute `CN` for `CJ`:

```text
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:620<yy>CN<num-4-digits>
```

**Verification note:** CELEX derivation is deterministic but not guaranteed — newly
assigned cases may differ. If derived URL errors, single `WebSearch` case reference +
"EUR-Lex", retry with correct CELEX.

**Austrian cases:**

RIS Judikatur API with `Geschaeftszahl`:

```text
https://data.bka.gv.at/ris/api/v2.6/Judikatur?Applikation=<Gericht>&Geschaeftszahl=<gz>
```

- OGH: `Applikation=Justiz&Gericht=OGH`
- VfGH: `Applikation=Vfgh`
- VwGH: `Applikation=Vwgh`

Parse the JSON response → `OgdSearchResult.Hits[].DokumentUrl`. `WebFetch` the
`DokumentUrl` for the full decision text.

#### Step C2: Single Primary Fetch

**One** `WebFetch` to the derived CELEX URL (CJEU) or RIS API + DokumentUrl (Austrian).

EUR-Lex CELEX page contains **everything needed in one call:**

- Full judgment text and operative part
- ECLI identifier
- Parties, date, chamber
- Legal basis and prior case law cited
- Procedural history
- Link to related documents (AG Opinion, press release)

Do **not** fetch CURIA, press releases, or other secondary sources in initial
lookup. Follow-up research only — delegate to law-researcher agent.

#### Step C3: Archive

```bash
uv run law-db --archive-url "<eur-lex-celex-url>" --topic "cjeu-<case-slug>"
```

Topic slug: `cjeu-shipova-c-43-24`, `ogh-5ob234-20b`, `vfgh-g-123-24`, etc.

#### Step C4: Analyze & Output (Cases)

**Output template for cases:**

```text
## {Court} {Case Reference} — {Case Name}

**Jurisdiction**: {EU | AT}
**Parties**: {parties}
**Court**: {full court name, chamber if applicable}
**Date**: {judgment date}
**ECLI**: {ECLI} (CJEU only)
**CELEX**: {CELEX} (CJEU only)
**Source**: {EUR-Lex CELEX URL | RIS DokumentUrl}
**Archived**: `law-db/documents/<topic-slug>/`

### What This Case Is About
{2–4 sentence plain-language summary of facts and core legal question}

### Key Holdings
- **{legal principle}**: {one-line holding with legal basis}
- …

### Procedural History (if relevant)
| Date | Event |
|------|-------|
| … | … |

### Significance
{1–2 sentences on why this case matters, what it changes, which jurisdictions it affects}
```

#### Step C5: Interactive Q&A

After summary, prompt: "Do you have any questions about this case?"

---

### Statute Procedure

#### Step S1: Check Local Archive

```bash
uv run law-db-query --search-keyword "<law name or abbreviation>"
```

- Found with full text → read metadata (`--read-metadata --show-abstract`), skip to Step S4
- Found as metadata stub only → treat as not found, proceed to Step S2
- Not found → proceed to Step S2

#### Step S2: Search & Fetch

**Austrian law (RIS):**

Primary: RIS API v2.6

```text
https://data.bka.gv.at/ris/api/v2.6/Bundesrecht?Applikation=BrKons&Titel=<abbreviation>&DokumenteProSeite=Twenty
```

Parse JSON → `OgdSearchResult.Hits[].DokumentUrl`. `WebFetch` the `DokumentUrl` for
consolidated law text.

- Fallback: broader `Suchworte=` search if `Titel=` returns no hits
- Fallback: `WebSearch` with `site:ris.bka.gv.at`
- Reference: `.claude/agents/rules/ris-guidelines.md`

**EU law (EUR-Lex):**

Primary: CELEX URL

```text
https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:<CELEX>
```

- If no CELEX: `WebSearch` for law name + "EUR-Lex" to find CELEX, then fetch
- Reference: `.claude/agents/rules/eur-lex-guidelines.md`

#### Step S3: Archive to law-db

```bash
uv run law-db --archive-url "<document_url>" --topic "<topic-slug>"
```

- Topic slug from law abbreviation (ABGB → `abgb`, DSGVO → `dsgvo`)
- Follow law-db skill black-box rules — never touch `law-db/` files directly
- Integrity check runs automatically

#### Step S4: Analyze & Output

**Explanation (2–4 sentences):**

- Area of law, who it applies to, regulatory purpose
- EU directive (requires national implementation) vs regulation (directly applicable)
- Flag Austrian laws implementing EU directives with the underlying directive

**Summary (5–10 bullet points):**

- Thematically grouped — key provisions, rights, obligations
- Scope, key definitions, enforcement mechanisms
- Long laws (>500 sections): summarize structure + key chapters, don't enumerate

**Output template:**

```text
## {Law Name} ({Abbreviation})

**Jurisdiction**: {Austrian | EU | Austrian (implementing EU law)}
**Source**: {RIS URL | EUR-Lex CELEX URL}
**Current version as of**: {FassungVom / access date}

### What This Law Is About
{2–4 sentence plain-language explanation}

### Key Points
- **{Thematic group}**: {one-line summary}
- …
```

#### Step S5: Interactive Q&A

After summary, prompt: "Do you have any questions about this law?"

## Delegation Rules

### Answer Inline (from law text in context + general knowledge)

- "What does section X say?"
- "What is the scope of this law?"
- "How is term Y defined?"
- "What are the penalties under this law?"
- "Does this law apply to {clearly in-scope situation}?"
- Plain-text factual questions answerable from the statute itself

### Delegate to law-researcher (requires sources beyond the law text)

- "How have courts interpreted section X?"
- "Is this provision constitutional?"
- "How does this law interact with law Y?"
- "What are the practical implications for {specific scenario}?"
- "Has this been challenged in court?"
- "What changed in the 2024 amendment?"
- "Is this compliant with EU law?"
- Any question requiring case law, commentary, cross-referencing, or regulatory guidance

**Dispatch pattern:**

```text
Agent(subagent_type="law-researcher", prompt="Research question: {specific question}
Context: User asking about {law name}, {jurisdiction}. Full law text in context.
Question requires {case law/commentary/cross-referencing} because {reason}.
Relevant framework: {specific sections}.
Jurisdiction: {AT/EU/AT+EU}.
Required: Supporting authority, counter-authority, legal risk assessment.")
```

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Law not found | Try alternate names; `WebSearch` for correct identifier; report if still not found |
| Ambiguous name | List possibilities, explain differences, ask user to clarify |
| Already archived (full text) | Skip fetch+archive, read from archive, produce summary |
| Already archived (stub only) | Treat as not found, fetch full text and re-archive |
| Very long law (>500 sections) | Summarize structure + key chapters, note that deeper questions welcome |
| EU directive vs regulation | Clarify: regulations directly applicable; directives require national implementation |
| RIS/EUR-Lex unreachable | Fall back to WebSearch, note source limitation |
| User asks about different law | Restart from Step 1 for new law name |
| CJEU CELEX not at derived URL | Single `WebSearch` case reference + "EUR-Lex" to find correct CELEX; retry with that |
| Austrian case not in RIS | `WebSearch` with Geschäftszahl; some decisions are only in RDB/LexisNexis |
| AG Opinion vs Judgment | If user wants the Opinion, use `CN` (notice) CELEX sub-code; clearly label as non-binding |
| Case reference is a settled order, not a judgment | EUR-Lex page will indicate document type; label accordingly (order vs judgment) |
| User provides ECLI instead of case ref | `WebFetch` `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=ECLI:<ECLI>` directly |

## Integration Pointers

| What | How |
|------|-----|
| Check archive | `uv run law-db-query --search-keyword "..."` |
| Read archived | `uv run law-db-query --read-metadata "<path>" --show-abstract` |
| Archive fetched text | `uv run law-db --archive-url "<url>" --topic "<slug>"` |
| Austrian law search | `WebFetch` RIS API v2.6 endpoint |
| EU law search | `WebFetch` EUR-Lex CELEX URL |
| CJEU case (judgment) | Derive CELEX from case ref → `WebFetch` CELEX URL (see Step C1) |
| CJEU case (AG Opinion) | Same, substitute `CN` for `CJ` |
| CJEU case (ECLI fallback) | `WebFetch` ECLI URL (see Edge Cases) |
| Austrian case (RIS) | `WebFetch` RIS Judikatur API with `Geschaeftszahl` → fetch `DokumentUrl` |
| CELEX verification (fallback) | `WebSearch` case reference + "EUR-Lex" only if derived URL fails |
| Deep legal research | `Agent(subagent_type="law-researcher", ...)` |
| Archive procedure rules | Follow `.claude/skills/law-db/SKILL.md` |
| Search strategies | `.claude/agents/rules/ris-guidelines.md`, `eur-lex-guidelines.md` |
