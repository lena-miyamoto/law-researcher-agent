---
title: JUSLINE Österreich
authors: ADVOKAT Unternehmensberatung Greiter & Greiter GmbH
source: jusline.at
source_url: https://www.jusline.at/
access_date: 2026-08-05
language: de
---

## JUSLINE Österreich

Freier Zugang zu österreichischen Gesetzestexten. Private Plattform der
ADVOKAT Unternehmensberatung Greiter & Greiter GmbH. Online und
uneingeschränkt nutzbar.

## Inhalt

### Gesetzestexte (kostenlos)

Konsolidierte Fassungen österreichischer Bundesgesetze. Jeder Paragraph ist
als eigene HTML-Seite (Standardansicht) und als PDF abrufbar. Die
konsolidierte Fassung enthält den berücksichtigten Gesetzgebungsstand.

- **ABGB** — Allgemeines bürgerliches Gesetzbuch
- **ASVG** — Allgemeines Sozialversicherungsgesetz
- **StGB** — Strafgesetzbuch
- **StPO** — Strafprozeßordnung 1975
- **B-VG** — Bundes-Verfassungsgesetz
- **EStG** — Einkommensteuergesetz
- **UStG** — Umsatzsteuergesetz
- **BAO** — Bundesabgabenordnung
- **NormG 2016** — Normalpreisgesetz
- **ETG 1992** — Elektrotechnikgesetz
- **UrhG** — Urheberrechtsgesetz
- Weitere Bundesgesetze (Umfang entspricht weitgehend dem RIS-Bestand an
  konsolidiertem Bundesrecht)

### Judikatur

Entscheidungen von OGH, VwGH und VfGH im PDF-Format. URL-Muster:
`/entscheidung/<id>.pdf`. Die Entscheidungen enthalten Rechtssätze (RS)
und sind durchsuchbar.

### Weitere Dienste (teilweise kostenpflichtig)

- **Grundbuch** — Grundbuchsabfragen
- **Firmenbuch** — Firmenbuchauskünfte
- **GISA** — Gewerbeinformationssystem Austria
- **Gesetzeskommentare** — Juristische Kommentierungen
- **Forum Recht** — Diskussionsplattform
- **Hilfstools** — Zinsrechner, Existenzminimum-Rechner

## URL-Struktur

| Ressource | Muster |
|---|---|
| Gesetzestext (HTML) | `https://www.jusline.at/gesetz/<kürzel>/paragraf/<nummer>` |
| Gesetzestext (PDF) | `https://www.jusline.at/gesetz/<kürzel>/paragraf/<nummer>.pdf` |
| Entscheidung | `https://www.jusline.at/entscheidung/<id>.pdf` |

Beispiele:

- `https://www.jusline.at/gesetz/asvg/paragraf/133` — § 133 ASVG (HTML)
- `https://www.jusline.at/gesetz/asvg/paragraf/131.pdf` — § 131 ASVG (PDF)
- `https://www.jusline.at/gesetz/estg/paragraf/34` — § 34 EStG (HTML)
- `https://www.jusline.at/entscheidung/446112.pdf`

### Websuche auf jusline.at

Die Plattform hat eine interne Suchfunktion. Ergänzend kann eine
Websuche mit `site:jusline.at` eingesetzt werden, um bestimmte Paragrafen
oder Entscheidungen zu finden:

```text
WebSearch(query="site:jusline.at ASVG 133 Krankenbehandlung")
```

## Einordnung

| Kriterium | Bewertung |
|---|---|
| Betreiber | Privat (ADVOKAT Greiter & Greiter) |
| Amtlichkeit | Nein — keine amtliche Quelle |
| Kosten | Gesetzestexte kostenlos; Grundbuch/Firmenbuch/GISA kostenpflichtig |
| API | **Nicht verfügbar.** Keine REST-API, kein SPARQL-Endpunkt, keine JSON-Exporte. Die Plattform bietet ausschließlich HTML-Seiten und PDFs für Endnutzer. Ein Word-Addin (A-S-O-Tool, `legaltech.jusline.at`) existiert, ist aber ebenfalls kein API. Für programmatischen Zugriff auf österreichisches Recht → RIS OGD API (`data.bka.gv.at/ris/api/v2.6/`). |
| Dokumentformat | HTML (Standard) + PDF (pro Paragraph) |
| Konsolidierung | Ja — enthält berücksichtigten Gesetzgebungsstand |
| Suchfunktion | Vorhanden (genaue Syntax nicht dokumentiert) |
| Qualität | Hoch für Alltagsgebrauch; für rechtsverbindliche Auskünfte ist RIS vorzuziehen |

## Nutzung durch den law-researcher Agent

### Abruf eines Paragrafen per WebFetch

```text
WebFetch(url="https://www.jusline.at/gesetz/<kürzel>/paragraf/<nummer>",
         prompt="Gib den vollständigen Gesetzestext von § X wieder.")
```

Die HTML-Seite enthält den konsolidierten Gesetzestext. `WebFetch`
konvertiert die Seite nach Markdown und extrahiert den Paragrafentext.

### Abruf als PDF per curl (für Archivierung in law-db)

```bash
curl -s "https://www.jusline.at/gesetz/<kürzel>/paragraf/<nummer>.pdf" \
  -o law-db/documents/<topic>/<identifier>/source.pdf
```

PDFs eignen sich besonders zum Archivieren, da sie den exakten Stand
zum Abrufzeitpunkt einfrieren.

### Suche nach einem Gesetz oder Paragrafen

```text
WebSearch(query="site:jusline.at <kürzel> <paragraf>")
```

Beispiel: `WebSearch(query="site:jusline.at ASVG Kostenerstattung")`

### Wann jusline.at, wann RIS?

| Kriterium | jusline.at | RIS |
|---|---|---|
| **Amtlichkeit** | Nein | Ja — für rechtsverbindliche Auskünfte |
| **Benutzerfreundlichkeit** | Hoch — übersichtliche HTML-Seiten | Mittel — komplexere Navigation |
| **Paragrafen-PDFs** | Ja — ein PDF pro Paragraph | Ja — über Druckansicht |
| **Historische Fassungen** | Nein | Ja — `FassungVom`-Parameter |
| **Landesrecht** | Nein | Ja — `LrKons` |
| **EU-Recht** | Nein | Nein — dafür EUR-Lex |
| **API** | **Keine** — weder REST noch sonstige | **Ja** — OGD REST-API, kein API-Key |
| **Strukturierter Datenzugriff** | Nur HTML-Scraping (nicht dokumentiert) | JSON/XML über API-Endpunkte |

**Grundregel:** jusline.at für schnelle Erstrechersche und Übersicht; RIS
für rechtsverbindliche Auskünfte, historische Fassungen, Landesrecht,
Behördenkontakt und jeden programmatischen Zugriff.

### Programmatischer Zugriff: RIS OGD API (kein API-Key)

Da jusline.at **keine API** anbietet, ist für jeden programmatischen Zugriff
auf österreichische Rechtsdaten ausschließlich die **RIS OGD API** zu
verwenden:

- **Basis-URL:** `https://data.bka.gv.at/ris/api/v2.6/`
- **Authentifizierung:** Keine — offene Schnittstelle, kein API-Key
- **Lizenz:** CC BY 4.0 (Open Data)
- **Dokumentation:** `https://data.bka.gv.at/ris/api/v2.6/dokumentation`

**Verfügbare Daten über die API (Auszug):**

| Endpunkt | Inhalt |
|---|---|
| `Bundesrecht/` | Konsolidiertes Bundesrecht (BrKons) |
| `Landesrecht/` | Konsolidiertes Landesrecht (LrKons) |
| `Judikatur/` | VfGH, VwGH, OGH, BVwG, LVwG |
| `BgblAuth/` | Authentische Bundesgesetzblätter |
| `Bgbl/` | Historische Gesetzblätter (1848–2003) |

**Abfragebeispiele:**

```bash
# Konsolidiertes Bundesrecht: § 133 ASVG
curl -s "https://data.bka.gv.at/ris/api/v2.6/Bundesrecht?fachzuordnung=Sozialversicherung&typ=Konsolidierte+Fassung"

# OGH-Entscheidung per Geschäftszahl
curl -s "https://data.bka.gv.at/ris/api/v2.6/Judikatur?ger=OGH&gz=10ObS2303/96s"

# Volltextsuche in der Judikatur
curl -s "https://data.bka.gv.at/ris/api/v2.6/Judikatur?suche=Genderdysphorie+krankenbehandlung"
```

Für die law-researcher-Recherche kann die RIS API verwendet werden, um
Gesetzestexte und Judikatur strukturiert (JSON) abzurufen und in law-db
zu archivieren. jusline.at bleibt das Werkzeug für schnelle,
leserfreundliche Einzelparagrafenabrufe per WebFetch.

### Archivieren in law-db

```bash
uv run law-db-query --archive-url "https://www.jusline.at/gesetz/<kürzel>/paragraf/<nummer>.pdf" \
  --source-name "jusline.at" \
  --topic "<topic>" \
  --jurisdiction AT \
  --document-type gesetz
```

Archivierte jusline.at-Dokumente in law-db behalten ihre Gültigkeit,
sofern der Gesetzgebungsstand nicht überholt ist.

## Alternative: RIS (Rechtsinformationssystem des Bundes)

Das offizielle, amtliche und **vollständig kostenfreie** Rechtsinformationssystem
des Bundes ist die primäre Alternative und für rechtsverbindliche Recherchen
vorzuziehen.

- **URL:** `https://ris.bka.gv.at/`
- **Inhalt:** Bundesrecht (konsolidiert und Originalfassungen), Landesrecht,
  Judikatur der Höchstgerichte (OGH, VwGH, VfGH), authentische Bundesgesetzblätter
- **Umfang:** ca. 1,4 Mio. Dokumente
- **Betreiber:** Bundeskanzleramt, amtlich
- **API:** REST-API unter `data.bka.gv.at/ris/api/v2.6/`, kein API-Key

## Weiterführende Quellen

- RIS: `https://ris.bka.gv.at/`
- ADVOKAT: `https://www.advokat.at/`
