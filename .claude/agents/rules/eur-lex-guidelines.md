---
title: EUR-Lex — Zugang zum EU-Recht
authors: Amt für Veröffentlichungen der Europäischen Union (Publications Office of the EU)
source: EUR-Lex
source_url: https://eur-lex.europa.eu/homepage.html?locale=de
access_date: 2026-08-03
language: de
extraction_notes: >
  Direkter Seitenzugriff auf eur-lex.europa.eu mit locale=de.
  Zusätzliche Informationen zu API, SPARQL-Endpoint und Datenzugriff
  aus der offiziellen EUR-Lex-Hilfeseite zur Datenwiederverwendung
  (https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html?locale=de).
---

## EUR-Lex — Zugang zum EU-Recht

Amtliches Portal der Europäischen Union für den Zugang zu EU-Recht.
Betrieben vom Amt für Veröffentlichungen der Europäischen Union.
**Kostenlos, 24 Amtssprachen, darunter Deutsch als voll unterstützte Sprache.**

## Zugang auf Deutsch

- Haupt-URL mit deutscher Oberfläche: `https://eur-lex.europa.eu/homepage.html?locale=de`
- URL-Parameter: `?locale=de` oder `?lang=de`
- Alle Navigation, Hilfe und rechtliche Hinweise sind vollständig übersetzt.
- Dokumentinhalte sind in deutscher Sprachfassung abrufbar (Sprachcode: `DE` / `DEU`).

## Inhalt

### Primärrecht

- **Gründungsverträge** (EUV, AEUV, Euratom-Vertrag)
- **Beitrittsverträge** und Protokolle
- **Charta der Grundrechte der Europäischen Union** (GRC)
- Chronologische Übersicht aller Verträge

### Sekundärrecht

- **Verordnungen** (unmittelbar geltend in allen Mitgliedstaaten)
- **Richtlinien** (umsetzungsbedürftig durch nationale Gesetzgebung)
- **Beschlüsse** (verbindlich für bestimmte Adressaten)
- **Konsolidierte Fassungen** (mit allen Änderungen integriert, tägliche
  Aktualisierung)
- **Vorarbeiten** (COM/JOIN-Dokumente, SEC/SWD-Arbeitsdokumente)
- **Delegierte Rechtsakte** und Durchführungsrechtsakte

### Internationale Übereinkommen

- Von der EU geschlossene internationale Abkommen
- EFTA-Dokumente

### Rechtsprechung

- **CJEU-Entscheidungen** (EuGH und EuG)
- Sammlung der Rechtsprechung
- Rechtsprechungsübersicht

### Nationales Recht

- **Nationale Umsetzungsmaßnahmen (NIM)** — wie Mitgliedstaaten Richtlinien
  umgesetzt haben
- **Nationale Rechtsprechung** mit EU-Bezug
- **JURE** — Zuständigkeit, Anerkennung und Vollstreckung von Entscheidungen

### Weitere Inhalte

- **Amtsblatt** — Reihen L (Rechtsakte) und C (Mitteilungen), tägliche Ansicht,
  rechtlich verbindliche Druckausgaben
- **Zusammenfassungen der EU-Gesetzgebung** (LEGISSUM)
- **EU Law Tracker** — Verfolgung von Gesetzgebungsverfahren
  (`law-tracker.europa.eu`)
- **EUROVOC** — Mehrsprachiger und multidisziplinärer Thesaurus der EU
- **N-Lex** — Nationale Rechtsdatenbanken der Mitgliedstaaten
- **Haushaltsplan online** — direkter Zugang zum EU-Haushalt

## CELEX-Nummer

Eindeutige Kennung jedes Dokuments in EUR-Lex. Aufbau:

- **Sektorziffer** (1 Stelle): 1 = Verträge, 2 = Internationale Übereinkommen,
  3 = Rechtsakte, 4 = Durchführungsrechtsakte, 5 = Vorarbeiten, 6 = Rechtsprechung,
  7 = Nationale Umsetzung, 9 = Parlamentarische Anfragen
- **Jahr** (2 oder 4 Stellen)
- **Dokumenttyp** (1–2 Buchstaben): R = Verordnung, L = Richtlinie,
  D = Beschluss, usw.
- **Laufende Nummer** (4 Stellen)

**Beispiele:**

- `32006L0121` — Verordnung (EG) Nr. 121/2006 (Sektor 3, Jahr 2006, Richtlinie L, Nr. 0121)
- `12012E/TXT` — Konsolidierte Fassung des AEUV (Sektor 1, Jahr 2012, E = AEUV)

**Suche nach CELEX-Nummer:** `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:<CELEX>`

## ELI (European Legislation Identifier)

- Standardisiertes Identifikationssystem für Rechtsakte
- URI-basiert: `http://data.europa.eu/eli/<typ>/<jahr>/<nummer>`
- Von immer mehr Mitgliedstaaten implementiert
- Ermöglicht grenzüberschreitende Verlinkung von Rechtsakten

## URL-Struktur (wichtige Muster)

| Ressource | Muster |
|---|---|
| Startseite (DE) | `https://eur-lex.europa.eu/homepage.html?locale=de` |
| Dokument via CELEX | `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:<CELEX>` |
| Erweiterte Suche | `https://eur-lex.europa.eu/advanced-search-form.html?locale=de` |
| Amtsblatt (Tagesansicht) | `https://eur-lex.europa.eu/oj/daily-view/L-series/default.html?ojDate=<DDMMYYYY>` |
| Zusammenfassungen | `https://eur-lex.europa.eu/browse/summaries.html?locale=de` |
| Konsolidierte Texte | `https://eur-lex.europa.eu/collection/eu-law/consleg.html?locale=de` |

## Technischer Zugang (APIs und Datenabruf)

### SPARQL-Endpoint (öffentlich, kein API-Key)

- **URL:** `https://publications.europa.eu/webapi/rdf/sparql`
- Abfrage aller Metadaten inkl. Beziehungen zwischen Dokumenten
- Semantisches Datenmodell (RDF/OWL) — Common Data Model (CDM)
- Sprachfilterung: `FILTER(lang(?title) = "de")` für deutsche Titel
- Advanced Query Editor: `https://op.europa.eu/en/advanced-sparql-query-editor`

### Cellar RESTful API

- Abruf von Metadaten-Notices und Dokumentinhalten
- Mehrere Formate: PDF, HTML, XHTML, Formex XML
- Zugang auf Anfrage

### EUR-Lex Webservice

- XML-basierte Suche (ähnlich Expertensuche)
- Erfordert **EU Login**-Account (registrierter Benutzer)

### Data Dump (Massen-Download)

- Alle Rechtsakte einer Sprache (CELEX-Sektor 3)
- Erfordert **EU Login**-Account
- URL: `https://datadump.publications.europa.eu/`

### data.europa.eu

- CSV-Listen der veröffentlichten Amtsblätter (L- und C-Reihe)
- Ab 2004, nach Jahr und Sprache
- Links zu Formex-XML-Dateien jeder Ausgabe

## Formate

| Format | Verwendung |
|---|---|
| HTML | Online-Lesefassung |
| PDF | Druckversion, Amtsblatt |
| XHTML | Strukturierte Online-Fassung |
| Formex XML | Maschinenlesbare amtliche Fassung (Amtsblatt) |
| RDF/XML | Metadaten (SPARQL-Endpoint) |

## Einordnung

| Kriterium | Bewertung |
|---|---|
| Betreiber | Amtlich — Amt für Veröffentlichungen der EU |
| Amtlichkeit | Ja — die einzige authentische amtliche Quelle für EU-Recht |
| Kosten | Vollständig kostenfrei |
| Sprachen | 24 Amtssprachen, Deutsch voll unterstützt |
| API | Ja — SPARQL (öffentlich), REST, Webservice, Data Dump |
| Dokumentformate | HTML, PDF, XHTML, Formex XML, RDF |
| Konsolidierung | Ja — täglich aktualisiert |
| Suchfunktion | Einfache Suche, Expertensuche, CELEX-Suche, SPARQL |
| Datenwiederverwendung | Kostenlos, vorbehaltlich urheberrechtlicher Beschränkungen |

## Nutzung für law-researcher

EUR-Lex ist die **primäre Quelle für EU-Recht** und steht in der
Authority Hierarchy an höchster Stelle für unionsrechtliche Fragen:

- **Stufe 1 (Primärrecht):** EU-Verträge, Charta → EUR-Lex
- **Stufe 1 (Verordnungen):** Direkt anwendbar → EUR-Lex
- **Stufe 3 (Richtlinien):** Umsetzungsbedürftig → EUR-Lex für EU-Text,
  RIS für österreichische Umsetzung
- **Stufe 2 (CJEU):** Rechtsprechung → EUR-Lex (Curia)

### Praktische Hinweise

- Für deutsche Sprachfassung **immer** `?locale=de` an die URL anhängen.
- `legal-content/DE/TXT/` im Pfad erzeugt die deutsche Dokumentansicht.
- CELEX-Nummer ist der zuverlässigste Identifier für law-db-Archivierung.
- SPARQL-Endpoint für systematische Recherchen (z. B. alle geltenden
  Verordnungen zu einem Thema).
- Für Massenextraktion: Data Dump oder Cellar REST API bevorzugen,
  nicht wiederholtes Web-Scraping.
- **Rechtliche Hinweise zur Datenwiederverwendung beachten** (§2 des
  Impressums/Legal Notice).
- Bei Amtsblatt-Zitaten: die elektronische Ausgabe ist **nicht**
  rechtsverbindlich — nur die gedruckte Ausgabe. Für wissenschaftliche
  Zwecke ist die elektronische Fassung ausreichend.

## Weiterführende Quellen

- EUR-Lex-Hilfe: `https://eur-lex.europa.eu/content/welcome/about.html?locale=de`
- Cellar: `https://op.europa.eu/en/web/cellar/home`
- EU Vocabularies: `https://publications.europa.eu/en/web/eu-vocabularies`
- EU Law Tracker: `https://law-tracker.europa.eu/`
- Methodology of Legal Analysis (LAM): `https://op.europa.eu/web/lam`
- SPARQL Query Editor: `https://op.europa.eu/en/advanced-sparql-query-editor`
- N-Lex (nationale Rechtsdatenbanken): `https://n-lex.europa.eu/`
