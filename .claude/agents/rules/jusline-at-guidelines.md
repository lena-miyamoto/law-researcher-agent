---
title: JUSLINE Österreich
authors: ADVOKAT Unternehmensberatung Greiter & Greiter GmbH
source: jusline.at
source_url: https://www.jusline.at/
access_date: 2026-08-03
language: de
extraction_notes: >
  jusline.at ist derzeit (August 2026) wegen eines Serverproblems offline.
  Diese Dokumentation basiert auf Web-Suchergebnissen und zuvor öffentlich
  zugänglichen Seiten. Die Informationen wurden aus Suchergebnissen und
  zitierten PDF-Dokumenten rekonstruiert, nicht durch direkten Seitenzugriff.
  Sobald jusline.at wieder online ist, sollte diese Datei durch direkten
  Seitenbesuch verifiziert werden.
---

## JUSLINE Österreich

Freier Zugang zu österreichischen Gesetzestexten. Private Plattform der
ADVOKAT Unternehmensberatung Greiter & Greiter GmbH.

## Status

**Derzeit offline (Serverproblem, Stand August 2026).** Kein Zugriff auf
Inhalte möglich. Keine öffentliche Ankündigung zur Wiederherstellung bekannt.

## Inhalt

### Gesetzestexte (kostenlos)

Konsolidierte Fassungen österreichischer Bundesgesetze. Die Plattform stellt
mindestens folgende Gesetze bereit (Liste aus Suchergebnissen rekonstruiert,
nicht abschließend):

- **ABGB** — Allgemeines bürgerliches Gesetzbuch
- **StGB** — Strafgesetzbuch
- **StPO** — Strafprozeßordnung 1975
- **B-VG** — Bundes-Verfassungsgesetz
- **NormG 2016** — Normalpreisgesetz
- **ETG 1992** — Elektrotechnikgesetz
- **UrhG** — Urheberrechtsgesetz
- Weitere Bundesgesetze (Umfang entspricht weitgehend dem RIS-Bestand an
  konsolidiertem Bundesrecht)

Jeder Paragraph ist als einzelne PDF-Datei abrufbar. Die konsolidierte
Fassung enthält den berücksichtigten Gesetzgebungsstand.

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
| Gesetzestext (Paragraph) | `https://www.jusline.at/gesetz/<kürzel>/paragraf/<nummer>.pdf` |
| Entscheidung | `https://www.jusline.at/entscheidung/<id>.pdf` |

Beispiele aus Suchergebnissen:

- `https://www.jusline.at/gesetz/normg/paragraf/8.pdf`
- `https://www.jusline.at/gesetz/etg/paragraf/16f.pdf`
- `https://www.jusline.at/gesetz/urhg/paragraf/76d.pdf`
- `https://www.jusline.at/entscheidung/446112.pdf`

## Einordnung

| Kriterium | Bewertung |
|---|---|
| Betreiber | Privat (ADVOKAT Greiter & Greiter) |
| Amtlichkeit | Nein — keine amtliche Quelle |
| Kosten | Gesetzestexte kostenlos; Grundbuch/Firmenbuch/GISA kostenpflichtig |
| API | Nicht verfügbar |
| Dokumentformat | PDF (pro Paragraph) |
| Konsolidierung | Ja — enthält berücksichtigten Gesetzgebungsstand |
| Suchfunktion | Vorhanden (genaue Syntax nicht dokumentiert) |
| Qualität | Hoch für Alltagsgebrauch; für rechtsverbindliche Auskünfte ist RIS vorzuziehen |

## Alternative: RIS (Rechtsinformationssystem des Bundes)

Das offizielle, amtliche und **vollständig kostenfreie** Rechtsinformationssystem
des Bundes ist die primäre Alternative und für rechtsverbindliche Recherchen
vorzuziehen.

- **URL:** `https://ris.bka.gv.at/`
- **Inhalt:** Bundesrecht (konsolidiert und Originalfassungen), Landesrecht,
  Judikatur der Höchstgerichte (OGH, VwGH, VfGH), authentische Bundesgesetzblätter
- **Umfang:** ca. 1,4 Mio. Dokumente
- **Betreiber:** Bundeskanzleramt, amtlich
- **API:** Nicht vorhanden, aber strukturierte Abfrage-URLs

## Nutzung für law-researcher

- Für **Alltagsrecherche** in österreichischen Gesetzestexten gut geeignet
  (wenn online).
- Für **rechtsverbindliche Auskünfte** und Behördenkontakt **immer RIS**
  verwenden.
- Paragrafen-PDFs eignen sich gut zum Archivieren in law-db (`--archive-url`).
- Die Plattform ist keine amtliche Quelle — in der Authority Hierarchy
  des law-researcher Agents als Zugangswerkzeug zu Primärrecht einzuordnen,
  nicht selbst als Autorität.
- Bei Offline-Status: auf RIS ausweichen. Archivierte jusline.at-Dokumente
  in law-db behalten ihre Gültigkeit, sofern der Gesetzgebungsstand nicht
  überholt ist.

## Weiterführende Quellen

- RIS: `https://ris.bka.gv.at/`
- ADVOKAT: `https://www.advokat.at/`
- jusline.at auf Brandfetch: `https://brandfetch.com/jusline.at`
