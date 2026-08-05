---
title: Footnotes and Source Citations
applies_to: all skills, all agents
version: 2026-08-05
---

Every agent or skill that produces a document with sources (legal memos, tax
analyses, insurance reports, research summaries) must follow these rules.

## Format

Footnotes use HTML anchors — **not** the `[^1]` Markdown extension. The
extension is not universally supported and silently breaks in many renderers.

### In the body

```html
<sup><a href="#fn1" id="fnref1">[1]</a></sup>
```

Always wrap in `<sup>` so the number renders as superscript.

### In the source list

Use an ordered list with `id` on each `<li>` so the anchors resolve. Each entry
has a `↩` back-link to its primary reference in the body.

```html
<ol>
<li id="fn1">
  <strong>Full source name and description.</strong><br>
  <a href="https://...">https://...</a>
  <a href="#fnref1">↩</a>
</li>
</ol>
```

### Multiple references to the same source

When the same source is cited more than once in the body, each reference needs
a **unique** `fnref` ID. Append a letter suffix: `fnref1`, `fnref1b`,
`fnref1c`. Every back-link in the source list points to the primary occurrence
(`#fnref1`).

```html
Erste Erwähnung.<sup><a href="#fn1" id="fnref1">[1]</a></sup>
Zweite Erwähnung.<sup><a href="#fn1" id="fnref1b">[1]</a></sup>
```

### Links in source entries

- Every URL is a clickable `<a>` tag — never a bare URL.
- For long URLs with query parameters and tokens, truncate the visible text
  with `…` but keep the full `href`: `<a href="...full...">...truncated…</a>`

## Content of Each Source Entry

Every footnote entry must be **self-contained and understandable in isolation**
— the reader must not need to look up anything in the body text to understand
what the source is.

### Required elements (in order)

1. **Full proper name** — no abbreviations without expansion. Spell out the
   complete name of the law, court, institution, or author.
2. **Abbreviation** in parentheses if commonly used later in the text.
3. **Description** after an em-dash (`—`) explaining what this source covers
   or what it is relevant for. One sentence, specific.
4. **URL** as a clickable link.

### Examples

**Law:**

> § 133 Abs. 2–3 Allgemeines Sozialversicherungsgesetz (ASVG) — Umfang der
> Krankenbehandlung, BGBl. Nr. 189/1955 idgF.

**Court decision:**

> OGH 12.09.1996, 10 ObS 2303/96s, SZ 69/209 — Transsexualität als Krankheit
> im Sinne des § 133 ASVG. Leitsatz RS0106239.
> ASG Wien 28.06.2022, 24 Cgs 69/21v — Laserepilation zur Unterbindung des
> Bartwachstums als Krankenbehandlung bei Geschlechtsdysphorie
> (ICD-10 F64.0). Leitsatz RWA0000049.
> LSG Baden-Württemberg 2009, L 11 KR 3126/08 — Epilation durch Kosmetikerin:
> keine Leistung der gesetzlichen Krankenversicherung (deutsches Recht, nicht
> bindend, Orientierungshilfe zum Risiko bei nichtärztlicher Behandlung).

**Administrative guidance:**

> Österreichische Gesellschaft für Plastische Chirurgie — Kriterien zur
> OP-Bewilligung (ÖGK-Bewilligungspraxis, Stand August 2024). Dokumentiert
> die Position der ÖGK: Laserepilation bei Transgender (Mann zu Frau) im
> Sinne einer Barthaarentfernung ist keine Kassenleistung.

**Media / non-legal context:**

> Medienberichterstattung zu den ASG-Wien-Entscheidungen 2024/2025 (nicht
> rechtsverbindlich, dokumentiert öffentliches Meinungsbild und politische
> Gegenposition der FPÖ): Krone.at — „Krankenkasse muss Epilation für
> Transfrau zahlen".

**Institutional document:**

> Ärztekammer für Oberösterreich — Merkblatt Wahlarzt-Kostenerstattung
> (chefärztliche Bewilligungspflicht bei Inanspruchnahme von
> Nicht-Vertragspartnern).

### Forbidden patterns

| Don't | Do |
|---|---|
| `§ 133 Abs. 2–3 ASVG` | `§ 133 Abs. 2–3 Allgemeines Sozialversicherungsgesetz (ASVG) — Umfang der Krankenbehandlung` |
| `OGH 10 ObS 2303/96s` | `OGH 12.09.1996, 10 ObS 2303/96s, SZ 69/209 — Transsexualität als Krankheit iSd § 133 ASVG` |
| `Krone.at, „Artikel"` | `Medienberichterstattung [Thema]: Krone.at — „Artikeltitel"` |
| Bare URL (not a link) | `<a href="...">https://...</a>` |
| `[^1]: text` (Markdown extension) | `<li id="fn1">…<a href="#fnref1">↩</a></li>` (HTML anchor) |

## Section heading

The source list section is always titled `## Quellenverzeichnis` (German) or
`## Sources` (English), depending on the document language.

## Ordering

Sources are numbered in order of first appearance in the body. If a source is
cited across multiple sections, it keeps its original number; later occurrences
reuse that number via the letter-suffixed `fnref` pattern.
