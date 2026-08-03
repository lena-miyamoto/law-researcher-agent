---
title: RIS — Rechtsinformationssystem des Bundes
authors: Bundeskanzleramt Österreich (BKA)
source: RIS (Rechtsinformationssystem des Bundes)
source_url: https://www.ris.bka.gv.at/
access_date: 2026-08-03
language: de
extraction_notes: >
  Die RIS-Website (www.ris.bka.gv.at) war beim Zugriffsversuch nicht erreichbar
  (HTTP 503). Diese Dokumentation basiert auf der öffentlichen OGD-RIS API-Dokumentation
  (Handbuch V2.6, Juli 2025), der risAT R-Paket-Dokumentation, dem RIS-Abfragehandbuch
  (HandbuchGesamtabfrage.pdf) und Web-Suchergebnissen. Die API-Basis-URL und Parameter
  sind dokumentiert und wurden aus mehreren Quellen verifiziert. Sobald die RIS-Website
  wieder erreichbar ist, sollte diese Datei durch direkten Seitenbesuch ergänzt werden.
---

## RIS — Rechtsinformationssystem des Bundes

Das **amtliche** Rechtsinformungsystem der Republik Österreich. Betrieben vom
Bundeskanzleramt (BKA). **Vollständig kostenfrei, Open Data (CC BY 4.0), kein Login
erforderlich.** Ca. 1,4 Mio. Dokumente.

RIS ist die **primäre und für rechtsverbindliche Auskünfte einzig maßgebliche**
Online-Quelle für österreichisches Recht. Alle anderen Plattformen (jusline.at, RDB,
LexisNexis) sind private Zusatzangebote.

## Zugang

| Zugangsweg | URL | Nutzung |
|---|---|---|
| Web-Oberfläche | `https://www.ris.bka.gv.at/` | Manuelle Recherche, Formular-basiert |
| REST-API | `https://data.bka.gv.at/ris/api/v2.6/` | Programmierte Abfragen, kein API-Key |
| API-Schema | `https://data.bka.gv.at/ris/api/v2.6/applications/<app>` | Metadaten und Parameter-Dokumentation pro Applikation |

Hinweis: Die Web-Oberfläche und die API liefern dieselben Ergebnisse. Eine in der
Web-Oberfläche konstruierte Suche kann durch Übernahme der URL-Parameter in eine
API-Abfrage umgewandelt werden.

## Inhalt und Applikationen

### Bundesrecht

| Applikation | Kürzel (API) | Beschreibung | Zeitraum |
|---|---|---|---|
| Bundesrecht konsolidiert | `BrKons` | Gesamtgeltungsfassung aller Bundesgesetze | aktuell + historische Fassungen |
| Bundesgesetzblatt authentisch | `BgblAuth` | Amtssignierte, rechtsverbindliche elektronische Bundesgesetzblätter | ab 2004 |
| Staats- und Bundesgesetzblatt | `BgblPdf` | PDF-Scans der Gesetzblätter | 1945–2003 |
| Reichs-, Staats- und Bundesgesetzblatt | `BgblAlt` | Historische Gesetzblätter | 1848–1940 |
| Begutachtungsentwürfe | `Begut` | Gesetzesentwürfe in Begutachtung | laufend |
| Regierungsvorlagen | `RegV` | Regierungsvorlagen zum Nationalrat | laufend |
| English Translations | `Erv` | Rechtsvorschriften in englischer Sprache | ausgewählte Gesetze |

**Web-URLs:**

- Konsolidiertes Bundesrecht: `https://www.ris.bka.gv.at/Bundesrecht/`
- BGBl authentisch: `https://www.ris.bka.gv.at/Bgbl-Auth/`
- BGBl 1945–2003: `https://www.ris.bka.gv.at/Bgbl-Pdf/`
- BGBl 1848–1940: `https://www.ris.bka.gv.at/Bgbl-Alt/`
- Begutachtungsentwürfe: `https://www.ris.bka.gv.at/Begut/`
- Regierungsvorlagen: `https://www.ris.bka.gv.at/RegV/`
- Englische Übersetzungen: `https://www.ris.bka.gv.at/Englisch-Rv/`

### Landesrecht

| Applikation | Kürzel | Beschreibung |
|---|---|---|
| Landesrecht konsolidiert | `LrKons` | Konsolidiertes Recht aller 9 Bundesländer |
| Landesgesetzblatt authentisch | `LgblAuth` | Amtssignierte Landesgesetzblätter |
| Landesgesetzblatt (nicht authentisch) | `Lgbl` | Retro-digitalisierte Landesgesetzblätter |
| Landesgesetzblatt NÖ (alt) | `LgblNO` | Niederösterreichisches LGBL historisch |
| Verordnungsblätter | `Vbl` | Verordnungsblätter der Länder |

Bundesländer-Kürzel: `Bgld`, `Ktn`, `NOe`, `OOe`, `Sbg`, `Stmk`, `Tirol`, `Vbg`, `Wien`

### Judikatur (Case Law)

| Applikation | Gericht / Spruchkörper | API-Kürzel |
|---|---|---|
| **Justiz** — Ordentliche Gerichte | **OGH**, OLG, LG, BG, AUSL | `Justiz` |
| **Verfassungsgerichtshof** | **VfGH** | `Vfgh` |
| **Verwaltungsgerichtshof** | **VwGH** | `Vwgh` |
| Bundesverwaltungsgericht | BVwG | `Bvwg` |
| Landesverwaltungsgerichte | LVwG (9 Länder) | `Lvwg` |
| Datenschutzbehörde | DSK / DSB / PDK | `Dsk` |
| Disziplinarbehörden | BDB / DK / DOK / BK | `Dok` |
| Personalvertretung | PVAK / PVAB | `Pvak` |
| Gleichbehandlungskommission | GBK | `Gbk` |
| Asylgerichtshof (2008–2013) | AsylGH | `AsylGH` |
| Unabhängiger Bundesasylsenat (1998–2008) | UBAS | `Ubas` |
| Unabhängige Verwaltungssenate (1991–2013) | UVS | `Uvs` |
| Umweltsenat (1994–2013) | UMSE | `Umse` |
| Bundeskommunikationssenat (2001–2013) | BKS | `Bks` |
| Vergabekontrollbehörden (bis 2013) | VERG | `Verg` |

**Web-URLs:**

- VfGH: `https://www.ris.bka.gv.at/Vfgh/`
- VwGH: `https://www.ris.bka.gv.at/Vwgh/`
- Justiz (OGH etc.): `https://www.ris.bka.gv.at/Just/`
- BVwG: `https://www.ris.bka.gv.at/Bvwg/`
- LVwG: `https://www.ris.bka.gv.at/Lvwg/`

### Weitere Applikationen

- **Gemeinderecht:** `Gr` (konsolidiert), `GrA` (authentisch)
- **Bezirksverwaltungsbehörden:** `Bvb` — Kundmachungen
- **Sonstige:** `Upts`, `Erlaesse`, `Avsv` — Erläuterungen, Erlässen, Ausschreibungen

## Suchsyntax (Web und API)

### Boolesche Operatoren

| Operator | Syntax | Wirkung |
|---|---|---|
| **UND** | `und` oder Leerzeichen | Alle Begriffe müssen vorkommen |
| **ODER** | `oder` | Mindestens einer muss vorkommen |
| **NICHT** | `nicht` | Erster Begriff ja, zweiter nein |
| **Klammerung** | `( … )` | Ausdrücke gruppieren |
| **Wildcard** | `*` | Am Anfang, in der Mitte oder am Ende eines Wortes |
| **Phrasensuche** | `"…"` oder `'…'` | Exakte Wortfolge |

**Beispiele:**

- `Mietrecht` — einfache Volltextsuche
- `(dienstbarkeit oder servitut) und verjährung` — komplexe Boolesche Suche
- `"condictio indebiti"` — exakte Phrase
- `arbeit*gesetz` — Wildcard (findet Arbeitsgesetz, Arbeitnehmergesetz, etc.)
- `*minister` — Präfix-Wildcard (findet Bundesminister, Justizminister, etc.)
- `erfüllungsgehilfe nicht haftung` — Ausschluss

### Hinweise zur Suchsyntax

- Begriffe in **verschiedenen Abfragefeldern** werden stets mit **UND** verknüpft.
- Suchoperatoren sind in folgenden Feldern erlaubt: `Suchworte`, `Titel`, `Index`, `Typ`.
- In Feldern wie `Paragraph`, `Artikel`, `Anlage`, `Geschäftszahl` sind **keine**
  Suchoperatoren möglich (exakte Eingabe).
- Mindestens 2 Zeichen vor/nach `*`-Wildcard sind erforderlich.

## API-Abfrageparameter

### Bundesrecht konsolidiert (`BrKons`)

**Endpoint:** `GET https://data.bka.gv.at/ris/api/v2.6/Bundesrecht`

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` | `BrKons` | (Pflicht) Applikation wählen. Default: `BrKons` |
| `Suchworte` | FulltextSearchExpression | Volltext über alle Metadaten (max. ~1000 Zeichen) |
| `Titel` | FulltextSearchExpression | Suche in Kurztitel, Langtitel, Abkürzung (z. B. `ABGB`) |
| `Index` | PhraseSearchExpression | Sachgruppen-Nummern/-Bezeichnungen des Bundesrechts-Index |
| `Typ` | FulltextSearchExpression | Dokumenttyp |
| `FassungVom` | `YYYY-MM-DD` | Punktuelle historische Fassung |
| `DokumenteProSeite` | `Ten`, `Twenty`, `Fifty`, `OneHundred` | Paginierung |
| `Seitennummer` | Integer (1–n) | Seitennummer |
| `ImRisSeit` | `EinerWoche`, `ZweiWochen`, `EinemMonat`, `DreiMonaten`, `SechsMonaten`, `EinemJahr` | Neuigkeitsfilter |

**Beispiel (API):**

```text
https://data.bka.gv.at/ris/api/v2.6/Bundesrecht?Applikation=BrKons&Titel=ABGB&Suchworte=Mietrecht&DokumenteProSeite=Twenty
```

**Beispiel (Web — URL-Konstruktion):**

```text
https://www.ris.bka.gv.at/Bundesrecht/?Titel=ABGB&Suchworte=Mietrecht
```

### Bundesgesetzblatt authentisch ab 2004 (`BgblAuth`)

**Web-URL:** `https://www.ris.bka.gv.at/Bgbl-Auth/`

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` | `BgblAuth` | (Pflicht) |
| `Suchworte` | FulltextSearchExpression | Volltext |
| `Titel` | FulltextSearchExpression | Titel des Gesetzblatts |
| `Kundgemacht.Von` / `.Bis` | `YYYY-MM-DD` | Kundmachungsdatum |
| `Typ` | Booleans | `SucheInGesetzen`, `SucheInKundmachungen`, `SucheInVerordnungen`, `SucheInSonstiges` |
| `Teil` | Booleans | `SucheInAlt`, `SucheInTeil1`, `SucheInTeil2`, `SucheInTeil3` |
| `Sortierung` | `Fundstelle` / `Kundmachungsdatum` + `Ascending`/`Descending` | Sortierung |
| `DokumenteProSeite` | `Ten`, `Twenty`, `Fifty`, `OneHundred` | Paginierung |
| `Seitennummer` | Integer (1–n) | Seite |

**Beispiel (API):**

```text
https://data.bka.gv.at/ris/api/v2.6/Bundesrecht?Applikation=BgblAuth&Suchworte=Datenschutz&Kundgemacht.Von=2020-01-01&SucheInGesetzen=true
```

### Bundesgesetzblatt 1945–2003 (`BgblPdf`)

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` | `BgblPdf` | (Pflicht) |
| `Suchworte` | FulltextSearchExpression | Volltext |
| `Titel` | FulltextSearchExpression | Titel |
| `Bundesgesetzblatt` | PhraseSearchExpression | BGBl-Nummer |
| `Kundgemacht.Von` / `.Bis` | `YYYY-MM-DD` | Kundmachungsdatum |
| `Typ` | Booleans | Gleiche wie `BgblAuth` |
| `Sortierung` | `Fundstelle` / `Kundmachungsdatum` | Sortierung |

### Bundesgesetzblatt 1848–1940 (`BgblAlt`)

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` | `BgblAlt` | (Pflicht) |
| `Titel` | FulltextSearchExpression | Titel |
| `Gesetzblattnummer` | TermSearchExpression | Nummer (keine Operatoren) |
| `Jahrgang` | TermSearchExpression | Jahrgang (keine Operatoren) |
| `Stuecknummer` | TermSearchExpression | Stücknummer (keine Operatoren) |
| `Kundgemacht.Von` / `.Bis` | `YYYY-MM-DD` | Datum |

### Judikatur — API-Parameter

**Endpoint:** `GET https://data.bka.gv.at/ris/api/v2.6/Judikatur`

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` / `Gericht` | Gerichtskürzel | `Justiz`, `Vfgh`, `Vwgh`, `Bvwg`, `Lvwg`, `Dsk`, etc. |
| `Suchworte` | FulltextSearchExpression | Volltext (max. ~1000 Zeichen) |
| `EntscheidungsdatumVon` / `.Bis` | `YYYY-MM-DD` | Entscheidungsdatum |
| `Dokumenttyp` | Booleans | `SucheInRechtssaetzen`, `SucheInEntscheidungstexten` |
| `Geschaeftszahl` | ExactMatch | Geschäftszahl (z. B. `5Ob234/20b`) |
| `Rechtssatznummer` | ExactMatch | Rechtssatznummer (z. B. `RS0126731`) |
| `Norm` | ExactMatch | Norm (z. B. `1319a ABGB`) |
| `Entscheidungsart` | Enum (variiert je Gericht) | Art der Entscheidung |
| `Gericht` (Justiz) | `OGH`, `OLG`, `LG`, `BG` | Spezifisches Gericht |
| `Spruch` | Text | Spruchtext (nur Entscheidungstexte) |
| `RechtlicheBeurteilung` | Text | Rechtliche Beurteilung (nur Entscheidungstexte) |
| `Fundstelle` | Text | Fundstelle/Zitat |
| `Index` | PhraseSearchExpression | Index-Begriffe |
| `DokumenteProSeite` | `Ten`, `Twenty`, `Fifty`, `OneHundred` | Paginierung |
| `Seitennummer` | Integer (1–n) | Seite |

**Beispiel (VwGH):**

```text
https://data.bka.gv.at/ris/api/v2.6/Judikatur?Applikation=Vwgh&Suchworte=Baurecht&EntscheidungsdatumVon=2024-01-01&Entscheidungsart=Erkenntnis
```

**Beispiel (OGH Justiz):**

```text
https://data.bka.gv.at/ris/api/v2.6/Judikatur?Applikation=Justiz&Suchworte=Schadenersatz&Gericht=OGH&SucheInRechtssaetzen=true
```

**Beispiel (VfGH Grundrechte, nur Rechtssätze):**

```text
https://data.bka.gv.at/ris/api/v2.6/Judikatur?Applikation=Vfgh&Suchworte=Grundrecht&SucheInRechtssaetzen=true&SucheInEntscheidungstexten=false
```

### Entscheidungsarten (wichtige Gerichte)

**Justiz (OGH etc.):**

- `Ordentliche Erledigung (Sachentscheidung)`
- `Zurückweisung mangels erheblicher Rechtsfrage`
- `Zurückweisung aus anderen Gründen`
- `Verstärkter Senat`

**VfGH:**

- `Erkenntnis`
- `Beschluss`
- `Vergleich`

**VwGH:**

- `Erkenntnis`
- `Beschluss`
- `ErkenntnisVS` (verstärkter Senat)
- `BeschlussVS`

### Begutachtungsentwürfe (`Begut`)

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` | `Begut` | (Pflicht) |
| `Suchworte`, `Titel` | FulltextSearchExpression | Volltext, Titel |
| `InBegutachtungAm` | Datum | Stichtag für laufende Begutachtung |
| `EinbringendeStelle` | ExactMatch | Ministerium (aus Liste) |
| `ImRisSeit` | Zeitraum | Neuigkeitsfilter |

### Regierungsvorlagen (`RegV`)

| Parameter | Typ | Beschreibung |
|---|---|---|
| `Applikation` | `RegV` | (Pflicht) |
| `Suchworte`, `Titel` | FulltextSearchExpression | Volltext, Titel |
| `BeschlussdatumVon` / `.Bis` | Datum | Beschlussdatum im Ministerrat |
| `EinbringendeStelle` | ExactMatch | Einbringendes Ministerium |

## Bundesrechts-Index

Der Index des Bundesrechts ist das zentrale Navigationsinstrument für das
konsolidierte Bundesrecht. Jede Rechtsvorschrift ist einer oder mehreren
Sachgruppen zugeordnet.

- **Web:** `https://www.ris.bka.gv.at/UI/Bund/Bundesnormen/IndexBundesrecht.aspx`
- **API-Parameter:** `Index` (PhraseSearchExpression)
- Jeder Eintrag hat eine Identifikationsnummer (z. B. `20/01`) und eine
  Bezeichnung (z. B. `ABGB — Allgemeines bürgerliches Gesetzbuch`).

## API-Antwortformat

Die API gibt JSON zurück. Erfolgreiche Antworten enthalten:

- `OgdSearchResult` → `Hits` → Array von Dokumenten
- Jedes Dokument hat: `DokumentUrl`, `Titel`, `Kurztitel`, `Typ`, `Fundstelle`,
  `Kundmachungsdatum`, `FassungVom`, `ContentUrl` (Link zum Volldokument)

Fehlerantworten:

```json
{
  "OgdSearchResult": {
    "Error": {
      "Application": "...",
      "Message": "..."
    }
  }
}
```

## Einordnung

| Kriterium | Bewertung |
|---|---|
| Betreiber | Österreichisches Bundeskanzleramt — amtlich |
| Amtlichkeit | Ja — die einzige authentische amtliche Online-Quelle für österreichisches Bundesrecht |
| Kosten | Vollständig kostenfrei |
| Lizenz | CC BY 4.0 (Open Data) |
| API | Ja — öffentliche REST-API v2.6, kein API-Key erforderlich |
| Dokumentformate | HTML (Web), JSON (API), PDF (BgblPdf), XML (BgblAuth) |
| Konsolidierung | Ja — Bundesrecht konsolidiert (`BrKons`) mit täglicher Aktualisierung |
| Suchfunktion | Umfassend — Boolesche Operatoren, Wildcards, Phrasensuche, Feldsuche, historische Fassungen |
| Umfang | Ca. 1,4 Mio. Dokumente |
| Gerichtsentscheidungen | Ja — VfGH, VwGH, OGH und alle weiteren österreichischen Gerichte |

## Nutzung für law-researcher

RIS ist die **primäre Quelle für österreichisches Recht** und steht in der
Authority Hierarchy an höchster Stelle für alle innerstaatlichen Rechtsfragen:

- **Stufe 1 (Primärrecht):** Bundesverfassung, Bundesgesetze → RIS `BrKons`
- **Stufe 2 (Höchstgerichtliche Judikatur):** VfGH, VwGH, OGH → RIS `Judikatur`
- **Stufe 2 (Konsolidiertes Landesrecht):** → RIS `LrKons`
- **Stufe 3 (Verordnungen, Bescheide):** → RIS `BgblAuth` / `BgblPdf`

### Praktische Empfehlungen

1. **Bundesrecht konsolidiert (`BrKons`)** als ersten Einstiegspunkt für jede
   Recherche nach geltendem österreichischen Recht verwenden.
2. **Titel-Suche** mit Gesetzesabkürzung (z. B. `ABGB`, `StGB`, `MRG`) liefert
   die schnellste Navigation zum gewünschten Gesetz.
3. **Index des Bundesrechts** konsultieren, wenn die genaue Gesetzesabkürzung
   nicht bekannt ist — die Sachgruppen-Hierarchie erschließt das gesamte
   Bundesrecht.
4. **`FassungVom`-Parameter** für historische Rechtslage zu einem bestimmten
   Stichtag (entscheidend für die Beurteilung von Altfällen).
5. **Judikatur-Recherche:** Zuerst Rechtssätze (`SucheInRechtssaetzen=true`)
   durchsuchen — sie enthalten die abstrakten Leitsätze. Bei Treffern gezielt
   die Volltexte (`SucheInEntscheidungstexten=true`) der relevanten Entscheidungen
   abrufen.
6. **Geschäftszahl** und **Rechtssatznummer** für punktuelle Zitate verwenden —
   diese Identifier sind stabil und zitierfähig.
7. **Bundesgesetzblatt authentisch (`BgblAuth`)** für die rechtsverbindliche
   Kundmachungsfassung — relevant, wenn es auf den genauen Wortlaut zum Zeitpunkt
   der Kundmachung ankommt (nicht die konsolidierte Fassung).
8. **Landesrecht** nicht vergessen — viele Materien (Bauordnung, Naturschutz,
   Veranstaltungsrecht) sind Landessache und stehen nicht im Bundesrecht.

### law-db-Archivierung

- **Konsolidierte Paragrafen:** `--archive-url` der HTML-Ansicht (stabile URL mit
  `FassungVom`-Parameter für Versionierung)
- **Entscheidungen:** Über die API abrufen, JSON als Volltext archivieren
- **BGBl:** PDF-URL (`BgblPdf`) oder HTML (`BgblAuth`) archivieren
- **Zitierformat:** `RIS-Justiz RS0126731`, `RIS-VfGH GZ A7/99`, `BGBl. I Nr. 33/2022`

### Client-Bibliotheken

- **risAT** (R-Paket): `https://werkstattcodes.github.io/risAT/` — tidyverse-kompatibel
- **ris-mcp** / **ris-mcp-ts** (MCP-Server): `ris_bundesrecht`, `ris_judikatur`, `ris_history` Tools
- **at-eli-mcp** (MCP-Server): Volltextabruf über `content_urls`

## Weiterführende Quellen

- RIS-Homepage: `https://www.ris.bka.gv.at/`
- OGD-RIS API Handbuch V2.6: auf data.gv.at als PDF verfügbar
- RIS-Abfragehandbuch (Gesamtabfrage): `https://www.ris.bka.gv.at/RisInfo/HandbuchGesamtabfrage.pdf`
- RIS-Abfragehandbuch (Bundesnormen): `https://www.ris.bka.gv.at/RisInfo/HandbuchBundesnormen.pdf`
- RIS-Abfragehandbuch (Justiz): `https://www.ris.bka.gv.at/RisInfo/HandbuchJustiz.pdf`
- Index des Bundesrechts: `https://www.ris.bka.gv.at/UI/Bund/Bundesnormen/IndexBundesrecht.aspx`
- API-Schema pro Applikation: `https://data.bka.gv.at/ris/api/v2.6/applications/<app>`
- risAT R-Paket: `https://werkstattcodes.github.io/risAT/`
- RIS auf data.gv.at: `https://www.data.gv.at/katalog/dataset/0fb9ae1a-92cb-4ab8-a589-470c16d4fe21`
