"""Archive tax-related documents into the local law-db schema.

Supports PDF archival with automatic Markdown extraction (via pdftotext),
CSV archival (broker statements, bank exports), and direct Markdown archival.
Documents are stored under law-db/receipts/<tax_category>/<identifier-slug>/.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

import utils

# Re-export canonical utilities for convenience
unique_folder_name = utils.unique_folder_name
validate_topic_slug = utils.validate_topic_slug

DEFAULT_TOPIC = "uncategorized"
DEFAULT_PURPOSE = "Archived via law-db-receipt; review and refine purpose."
VALID_SUBTYPES = {
    "receipt", "medical_honorarium", "broker_statement",
    "business_expense", "income_document", "salary_statement",
    "bank_statement", "other",
}
VALID_TAX_CATEGORIES = {
    "werbungskosten", "sonderausgaben", "aussergewoehnliche_belastung",
    "einkuenfte_aus_kapitalvermoegen", "einkuenfte_aus_selbststaendiger_arbeit",
    "einkuenfte_aus_nichtselbststaendiger_arbeit", "umsatzsteuer_vorsteuer",
    "other",
}


def validate_subtype(value):
    if value not in VALID_SUBTYPES:
        raise ValueError(f"invalid subtype: {value!r}; must be one of: {', '.join(sorted(VALID_SUBTYPES))}")
    return value


def validate_tax_category(value):
    if value not in VALID_TAX_CATEGORIES:
        raise ValueError(f"invalid tax category: {value!r}; must be one of: {', '.join(sorted(VALID_TAX_CATEGORIES))}")
    return value


def archive_receipt_pdf(pdf_path, receipt_dir, metadata):
    """Copy PDF into *receipt_dir*/source.pdf and extract source.md."""
    destination_pdf = receipt_dir / "source.pdf"
    utils.copy_file_verified(pdf_path, destination_pdf)

    raw_bytes = pdf_path.read_bytes()
    if not utils.content_is_pdf(raw_bytes):
        raise ValueError(f"file does not appear to be a PDF (no %PDF- header): {pdf_path}")

    metadata["has_pdf"] = True
    try:
        markdown_text = utils.pdf_bytes_to_markdown(raw_bytes, str(pdf_path))
        utils.atomic_write(receipt_dir / "source.md", markdown_text)
        metadata["has_markdown"] = True
    except RuntimeError as exc:
        print(f"warning: PDF extraction failed: {exc}", file=sys.stderr)
        print("PDF saved but no markdown was extracted.", file=sys.stderr)
        metadata["has_markdown"] = False


def archive_receipt_markdown(markdown_path, receipt_dir, metadata):
    """Copy Markdown into *receipt_dir*/source.md."""
    destination_markdown = receipt_dir / "source.md"
    utils.copy_file_verified(markdown_path, destination_markdown)
    metadata["has_markdown"] = True


def archive_receipt_csv(csv_path, receipt_dir, metadata):
    """Copy CSV into *receipt_dir*/source.csv and extract metadata fields."""
    destination_csv = receipt_dir / "source.csv"
    utils.copy_file_verified(csv_path, destination_csv)
    metadata["has_csv"] = True

    rows = utils.parse_csv_rows(str(csv_path))
    if rows:
        metadata["csv_row_count"] = len(rows)
        metadata["csv_columns"] = list(rows[0].keys())
    else:
        metadata["csv_row_count"] = 0
        metadata["csv_columns"] = []


def archive_receipt_url(url, receipt_dir, metadata):
    """Download PDF from *url*, save to source.pdf, and extract source.md."""
    import urllib.request

    request = urllib.request.Request(url, headers={"User-Agent": utils.USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_bytes = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"error fetching {url}: {exc}") from exc

    if not utils.content_is_pdf(raw_bytes):
        raise ValueError(f"downloaded content from {url} does not appear to be a PDF")

    pdf_destination = receipt_dir / "source.pdf"
    pdf_tmp = pdf_destination.with_suffix(".pdf.tmp")
    pdf_tmp.write_bytes(raw_bytes)
    pdf_tmp.replace(pdf_destination)

    metadata["has_pdf"] = True
    try:
        markdown_text = utils.pdf_bytes_to_markdown(raw_bytes, url)
        utils.atomic_write(receipt_dir / "source.md", markdown_text)
        metadata["has_markdown"] = True
    except RuntimeError as exc:
        print(f"warning: PDF extraction failed: {exc}", file=sys.stderr)
        print("PDF saved but no markdown was extracted.", file=sys.stderr)
        metadata["has_markdown"] = False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Archive tax-related documents into the local law-db schema.",
    )
    parser.add_argument(
        "--type",
        choices=sorted(VALID_SUBTYPES),
        required=True,
        help="Subtype of tax document: receipt, medical_honorarium, broker_statement, etc.",
    )
    parser.add_argument(
        "--file",
        help="Path to a PDF, Markdown, or CSV file to archive.",
    )
    parser.add_argument(
        "--url",
        help="URL to download and archive as a PDF.",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Human-readable title for the tax document.",
    )
    parser.add_argument(
        "--tax-category",
        choices=sorted(VALID_TAX_CATEGORIES),
        required=True,
        help="Tax category: werbungskosten, sonderausgaben, aussergewoehnliche_belastung, etc.",
    )
    parser.add_argument(
        "--payer",
        help="Entity that issued the document (e.g. doctor, broker, employer).",
    )
    parser.add_argument(
        "--payee",
        help="Entity that received the document (typically the taxpayer).",
    )
    parser.add_argument(
        "--amount",
        type=float,
        help="Monetary amount in the document currency.",
    )
    parser.add_argument(
        "--currency",
        default="EUR",
        help="ISO 4217 currency code. Defaults to EUR.",
    )
    parser.add_argument(
        "--document-date",
        help="Date on the document in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--tax-period",
        help="Tax period in YYYY format (e.g. 2025).",
    )
    parser.add_argument(
        "--topic",
        help="Topic for grouping (e.g. arztrechnung, flatex, finanzamt). Defaults to 'uncategorized'.",
        default=DEFAULT_TOPIC,
    )
    parser.add_argument(
        "--topic-slug",
        help="Explicit kebab-case slug for the topic folder. Overrides --topic if both are given.",
    )
    parser.add_argument(
        "--language",
        default="de",
        help="Language code for the document. Defaults to 'de'.",
    )
    parser.add_argument(
        "--source-url",
        help="Original source URL for reference.",
    )
    parser.add_argument(
        "--notes",
        help="Free-text notes about the document.",
    )
    parser.add_argument(
        "--law-db",
        default="law-db",
        help="Target law-db directory. Defaults to ./law-db.",
    )
    parser.add_argument(
        "--identifier-slug",
        help="Explicit kebab-case slug for the receipt folder. Auto-generated from title if omitted.",
    )

    args = parser.parse_args()

    if not args.file and not args.url:
        parser.error("provide at least one of --file or --url")

    if args.file and args.url:
        parser.error("provide only one of --file or --url, not both")

    return args


def main():
    args = parse_args()
    law_db_path = Path(args.law_db)

    # Bootstrap if needed
    law_db_path.mkdir(parents=True, exist_ok=True)
    for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts", "receipts"):
        (law_db_path / name).mkdir(parents=True, exist_ok=True)

    tax_category = validate_tax_category(args.tax_category)

    topic = utils.validate_topic_slug(
        args.topic_slug or utils.slugify(args.topic, fallback=DEFAULT_TOPIC)
    )

    identifier_slug = args.identifier_slug or utils.slugify(
        args.title, fallback="receipt", max_length=60
    )

    receipts_dir = law_db_path / "receipts" / tax_category / topic
    receipts_dir.mkdir(parents=True, exist_ok=True)
    folder_name = utils.unique_folder_name(receipts_dir, identifier_slug)
    receipt_dir = receipts_dir / folder_name
    receipt_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()

    metadata = {
        "subtype": args.type,
        "title": args.title,
        "tax_category": tax_category,
        "payer": args.payer or "",
        "payee": args.payee or "",
        "amount": args.amount or 0,
        "currency": args.currency,
        "document_date": args.document_date or "",
        "tax_period": args.tax_period or "",
        "source_url": args.source_url or (args.url if args.url else ""),
        "access_date": today,
        "language": args.language,
        "has_pdf": False,
        "has_markdown": False,
        "has_csv": False,
        "notes": args.notes or "",
    }

    if args.url:
        archive_receipt_url(args.url, receipt_dir, metadata)
    elif args.file:
        file_path = Path(args.file)
        suffix_lower = file_path.suffix.lower()
        if suffix_lower == ".csv":
            archive_receipt_csv(file_path, receipt_dir, metadata)
        elif suffix_lower in (".md", ".markdown", ".txt"):
            archive_receipt_markdown(file_path, receipt_dir, metadata)
        elif suffix_lower == ".pdf":
            archive_receipt_pdf(file_path, receipt_dir, metadata)
        else:
            raw_bytes = file_path.read_bytes()
            if utils.content_is_pdf(raw_bytes):
                archive_receipt_pdf(file_path, receipt_dir, metadata)
            else:
                archive_receipt_markdown(file_path, receipt_dir, metadata)

    metadata_file = receipt_dir / "metadata.json"
    utils.atomic_write(
        metadata_file,
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
    )

    relative_path = str(receipt_dir.relative_to(law_db_path))
    receipt_updates = {
        relative_path: {
            "identifier": metadata["title"],
            "subtype": metadata["subtype"],
            "title": metadata["title"],
            "tax_category": metadata["tax_category"],
            "purpose": DEFAULT_PURPOSE,
            "accessed": today,
        },
    }

    utils.ensure_law_db_loaded()
    import law_db
    law_db.sync_index(law_db_path, receipt_updates=receipt_updates)

    print(f"archived {args.type}: {relative_path}")
    if metadata["has_pdf"]:
        print(f"  PDF: source.pdf")
    if metadata["has_markdown"]:
        print(f"  Markdown: source.md")
    if metadata["has_csv"]:
        print(f"  CSV: source.csv ({metadata.get('csv_row_count', 0)} rows)")

    if utils.verify_and_report_integrity(law_db_path) != 0:
        return 1

    return 0


if __name__ == "__main__":
    utils.run_cli(main)
