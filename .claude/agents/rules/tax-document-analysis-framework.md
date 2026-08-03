---
description: >
  Systematic framework for analyzing tax documents — document categories,
  receipt fields, broker statement analysis, red-flag patterns, and
  structured analysis methodology. Read during Phase 2 (document analysis)
  of the tax-advisor workflow.
---

# Tax Document Analysis Framework

## Document Categories

| Category | German Term | Typical Content | EStG Reference |
|---|---|---|---|
| Honorarnote | Honorarnote | Medical receipt from a Wahlarzt (fee-for-service doctor) | §§ 34–35 außergewöhnliche Belastung |
| Rechnung | Rechnung | Invoice with Umsatzsteuerausweis | § 12 UStG Vorsteuer; § 16 Werbungskosten |
| Beleg | Beleg | Generic receipt (cash register slip, expense proof) | § 16 Werbungskosten |
| Depotauszug | Depotauszug | Broker custody statement showing holdings, transactions | § 27(3) EStG Kapitalvermögen |
| Jahressteuerreport | Jahressteuerreport | Annual tax report from a broker summarizing all taxable events | § 27 EStG; KESt § 93 |
| Kontoauszug | Kontoauszug | Bank statement showing credits and debits | § 27(2) Zinserträge; § 16 Zahlungsnachweis |
| Lohnzettel | Lohnzettel (L16) | Annual salary statement from employer | § 25 nichtselbstständige Arbeit |
| Fondsmitteilung | Fondsmitteilung | Fund report — ausschüttungsgleiche Erträge, Thesaurierung | § 27(3), § 186 InvFG |
| Steuerbescheid | Steuerbescheid | Tax assessment notice from Finanzamt | BAO §§ 198–300 |

## Receipt Analysis (Honorarnoten, Rechnungen)

Fields to extract from every receipt:

| Field | Description | Relevance |
|---|---|---|
| Payer | Who paid (taxpayer, insurance, third party) | Determines who can claim deduction |
| Payee | Who received payment (doctor, supplier) | Verifies legitimacy of deduction |
| Amount | Gross amount (Bruttobetrag) | Deduction base amount |
| Umsatzsteuer | VAT amount separately stated | Vorsteuerabzug if applicable (§ 12 UStG) |
| Date | Document date | Tax period assignment |
| Purpose | Reason for expense (Leistungsbeschreibung) | Determines EStG category |
| Tax category | werbungskosten / sonderausgaben / aussergewoehnliche_belastung | Determines deduction rules and limits |

### Medical Receipts (Honorarnoten) — EStG § 34

- **Wahlarztrechnungen**: Deductible as außergewöhnliche Belastung (§ 34)
- **Selbstbehalt**: 6–12 % of income (depending on income level and family status, § 34(4))
- **Krankheitskosten**: Not classified as Werbungskosten except when work-related (§ 34(6))
- **Refunds from insurance (KV)**: Reduce the deductible amount — only the net out-of-pocket expense counts
- **Required proof**: Honorarnote must show doctor name, patient name, date, Leistungsbeschreibung, amount, and Umsatzsteuer if applicable

### Business Expense Receipts (Werbungskosten) — EStG § 16

- **Arbeitsmittel § 16(1)Z7**: Computer, software, books, work equipment
- **Fortbildung § 16(1)Z8**: Courses, conferences, professional literature
- **Reisekosten § 16(1)Z9**: Travel, accommodation, per-diem allowances
- **Arbeitszimmer § 20(1)Z2a**: Home office — only if workplace is in home and constitutes the center of professional activity

## Broker Statement Analysis (§ 27 EStG — Kapitalvermögen)

### Dividends (§ 27(2)Z1)

- KESt 27,5 % deducted at source by Austrian brokers (Endbesteuerungswirkung § 97)
- Foreign dividends: check DBA withholding rate (typically 15 %); excess can be credited
- Dividend amount (Bruttodividende) vs KESt-basis may differ (Quellensteuerabzug)

### Realized Gains/Losses (§ 27(3))

- Realisierte Kursgewinne: Taxed at 27,5 % KESt
- Realisierte Kursverluste: Offset only against capital gains (§ 27(3) and § 27(8))
- Altbestand (acquired before 2011-01-01 for shares, before 2012-04-01 for bonds): tax-exempt
- Loss carry-forward: only within the same brokerage account; no cross-broker loss offset without Verlustausgleichsantrag

### Interest Income (§ 27(2)Z2)

- Zinserträge: 27,5 % KESt
- Sparbuchzinsen, Anleihenzinsen, Festgeld — all taxed at 27,5 %

### Foreign Withholding Tax (Quellensteuer)

- Creditable up to the applicable DBA rate (typically 15 %)
- Exceeding foreign tax: reclaim from foreign tax authority (often cumbersome for retail investors)
- DBA Austria-Germany, Austria-Switzerland, Austria-USA: Quellensteuer 15 % on dividends
- Depottransfer zwischen Brokern: Anschaffungskosten and Anschaffungszeitpunkt must be carried over (§ 93(3) EStG)

### Accumulating Funds (Thesaurierende Fonds, § 186 InvFG)

- **Ausschüttungsgleiche Erträge**: Taxed annually even though no cash distribution occurs
- Reported by Fondsmitteilung; taxed via KESt deduction from cash account or by separate charge
- **Meldung an die OeKB**: All Austrian tax-reporting funds publish their agE via OeKB (oe kb.at)
- **Nichtmeldefonds**: Punitive taxation (pauschale Besteuerung, 27,5 % on 90 % of annual gain, min. 10 % of NAV)

### Transaction Fees

- Not deductible from capital gains for tax purposes
- Included in Anschaffungskosten basis adjustment (reduces gain / increases loss)

### FX Gains/Losses

- Foreign currency gains on deposit accounts: taxable if realized
- FX gains on securities: embedded in the EUR-equivalent sale price; not separately stated

## Red-Flag Text Patterns

Search tax document text for these patterns (German — Austrian tax documents):

| Pattern | Significance |
|---|---|
| `Honorar` | Medical fee — check if außergewöhnliche Belastung or business expense |
| `Umsatzsteuer` | VAT — check for Vorsteuerabzug eligibility (§ 12 UStG) |
| `Kapitalertragsteuer` | KESt deduction — verify rate (27,5 % or special rate) |
| `Quellensteuer` | Foreign withholding tax — check DBA credit |
| `realisierter Gewinn` | Realized capital gain — § 27(3) EStG |
| `realisierter Verlust` | Realized capital loss — offset within § 27 only |
| `Anschaffungskosten` | Acquisition cost — basis for gain/loss calculation |
| `ausschüttungsgleicher Ertrag` | Accumulating fund taxable income — § 186 InvFG |
| `Thesaurierung` | Reinvestment — accumulating fund (compare with agE) |
| `Zwischendividende` | Interim dividend paid during tax year |
| `AGB-Änderung` | Terms change — informational, not tax-relevant |
| `Steuerreport` | Tax report — comprehensive annual summary (high value for analysis) |
| `Jahressteuerreport` | Annual tax report — same as Steuerreport (Flatex terminology) |
| `Depottransfer` | Brokerage account transfer — check Anschaffungskosten carryover |

## Document Categorization Decision Tree

1. **Is the document from a broker/bank?**
   - Jahressteuerreport / Steuerreport → Broker Statement (Kapitalvermögen § 27)
   - Depotauszug → Broker Statement (Kapitalvermögen § 27)
   - Kontoauszug → Bank Statement (interest income § 27(2)Z2)
   - Fondsmitteilung → Fund Report (agE § 186 InvFG)

2. **Is the document from a doctor/medical provider?**
   - Honorarnote → Medical Receipt (außergewöhnliche Belastung § 34)
   - Rechnung with USt → Medical Invoice (check tax category based on purpose)

3. **Is the document from an employer?**
   - Lohnzettel (L16) → Salary Statement (nichtselbstständige Arbeit § 25)

4. **Is the document from Finanzamt?**
   - Steuerbescheid → Tax Assessment (BAO)

5. **Other documents:**
   - Contains `Rechnung` or `Umsatzsteuer` → Invoice (Werbungskosten § 16 or UStG § 12)
   - Generic expense proof → Receipt/Beleg (Werbungskosten § 16)

## Structured Analysis Methodology

1. **Categorize** the document using the decision tree above. Assign `subtype` and `tax_category`.
2. **Extract metadata fields**: payer, payee, amount, currency, document_date, tax_period.
3. **For broker statements**: extract and categorize each transaction (dividend, realized gain/loss, interest, agE, fee, FX) with EStG section reference.
4. **For medical receipts**: calculate net out-of-pocket (gross minus KV refund); check Selbstbehalt threshold (§ 34(4)).
5. **For business expense receipts**: verify work-relatedness (§ 16); check for mixed private/business use and apportion if needed.
6. **Cross-reference** amounts against bank/broker records for consistency.
7. **Flag** any unusual items: missing Umsatzsteuer on invoices where expected, foreign Quellensteuer without DBA claim, accumulating fund agE without OeKB-Meldung, Altbestand sales incorrectly taxed.
