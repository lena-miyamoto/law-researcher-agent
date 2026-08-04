"""Archive contracts and AGB into the local law-db schema.

Supports PDF archival with automatic Markdown extraction (via pdftotext),
direct Markdown archival, and URL-based archival.  Contracts, AGB, and
templates are stored under law-db/contracts/<topic>/<identifier-slug>/.
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
DEFAULT_PURPOSE = "Archived via law-db-contract; review and refine purpose."
VALID_TYPES = {"contract", "agb", "template"}
VALID_STATUSES = {"template", "pending", "active", "terminated"}
VALID_INSURANCE_TYPES = {
    "haushalt", "rechtsschutz", "kfz", "private-krankenversicherung",
    "lebensversicherung", "berufsunfaehigkeit", "unfall", "reise",
    "haftpflicht", "gebaeude", "recht", "other",
}


def validate_contract_type(value):
    if value not in VALID_TYPES:
        raise ValueError(f"invalid type: {value!r}; must be one of: {', '.join(sorted(VALID_TYPES))}")
    return value


def validate_contract_status(value):
    if value not in VALID_STATUSES:
        raise ValueError(f"invalid status: {value!r}; must be one of: {', '.join(sorted(VALID_STATUSES))}")
    return value


def validate_insurance_type(value):
    if value not in VALID_INSURANCE_TYPES:
        raise ValueError(f"invalid insurance type: {value!r}; must be one of: {', '.join(sorted(VALID_INSURANCE_TYPES))}")
    return value



def archive_contract_pdf(pdf_path, contract_dir, metadata):
    """Copy PDF into *contract_dir*/source.pdf and extract source.md."""
    destination_pdf = contract_dir / "source.pdf"
    utils.copy_file_verified(pdf_path, destination_pdf)

    raw_bytes = pdf_path.read_bytes()
    if not utils.content_is_pdf(raw_bytes):
        raise ValueError(f"file does not appear to be a PDF (no %%PDF- header): {pdf_path}")

    metadata["has_pdf"] = True
    try:
        markdown_text = utils.pdf_bytes_to_markdown(raw_bytes, str(pdf_path))
        utils.atomic_write(contract_dir / "source.md", markdown_text)
        metadata["has_markdown"] = True
    except RuntimeError as exc:
        print(f"warning: PDF extraction failed: {exc}", file=sys.stderr)
        print("PDF saved but no markdown was extracted.", file=sys.stderr)
        metadata["has_markdown"] = False


def archive_contract_markdown(markdown_path, contract_dir, metadata):
    """Copy Markdown into *contract_dir*/source.md."""
    destination_markdown = contract_dir / "source.md"
    utils.copy_file_verified(markdown_path, destination_markdown)
    metadata["has_markdown"] = True


def archive_contract_url(url, contract_dir, metadata):
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

    # Write PDF as binary (atomic_write is text-only; write_bytes + atomic rename)
    pdf_destination = contract_dir / "source.pdf"
    pdf_tmp = pdf_destination.with_suffix(".pdf.tmp")
    pdf_tmp.write_bytes(raw_bytes)
    pdf_tmp.replace(pdf_destination)

    metadata["has_pdf"] = True
    try:
        markdown_text = utils.pdf_bytes_to_markdown(raw_bytes, url)
        utils.atomic_write(contract_dir / "source.md", markdown_text)
        metadata["has_markdown"] = True
    except RuntimeError as exc:
        print(f"warning: PDF extraction failed: {exc}", file=sys.stderr)
        print("PDF saved but no markdown was extracted.", file=sys.stderr)
        metadata["has_markdown"] = False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Archive contracts and AGB into the local law-db schema.",
    )
    parser.add_argument(
        "--type",
        choices=sorted(VALID_TYPES),
        required=True,
        help="Type of document: contract, agb, or template.",
    )
    parser.add_argument(
        "--file",
        help="Path to a PDF or Markdown file to archive.",
    )
    parser.add_argument(
        "--url",
        help="URL to download and archive as a PDF.",
    )
    parser.add_argument(
        "--topic",
        help="Topic for grouping (e.g. versicherung, haushalt). Defaults to 'uncategorized'.",
        default=DEFAULT_TOPIC,
    )
    parser.add_argument(
        "--topic-slug",
        help="Explicit kebab-case slug for the topic folder. Overrides --topic if both are given.",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Human-readable title for the contract or AGB document.",
    )
    parser.add_argument(
        "--parties",
        help="Comma-separated list of parties (e.g. 'Insurer AG,John Doe').",
    )
    parser.add_argument(
        "--contract-date",
        help="Date of the contract in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--status",
        choices=sorted(VALID_STATUSES),
        help="Contract status: template, pending, active, or terminated.",
    )
    parser.add_argument(
        "--insurance-type",
        choices=sorted(VALID_INSURANCE_TYPES),
        help="Insurance type (e.g. haushalt, rechtsschutz, kfz).",
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
        help="Free-text notes about the contract or AGB.",
    )
    parser.add_argument(
        "--law-db",
        default="law-db",
        help="Target law-db directory. Defaults to ./law-db.",
    )
    parser.add_argument(
        "--identifier-slug",
        help="Explicit kebab-case slug for the contract folder. Auto-generated from title if omitted.",
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
    for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts"):
        (law_db_path / name).mkdir(parents=True, exist_ok=True)

    topic = utils.validate_topic_slug(
        args.topic_slug or utils.slugify(args.topic, fallback=DEFAULT_TOPIC)
    )

    identifier_slug = args.identifier_slug or utils.slugify(
        args.title, fallback="contract", max_length=60
    )

    contracts_dir = law_db_path / "contracts" / topic
    contracts_dir.mkdir(parents=True, exist_ok=True)
    folder_name = utils.unique_folder_name(contracts_dir, identifier_slug)
    contract_dir = contracts_dir / folder_name
    contract_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()

    metadata = {
        "type": args.type,
        "title": args.title,
        "parties": [p.strip() for p in args.parties.split(",")] if args.parties else [],
        "contract_date": args.contract_date or "",
        "status": args.status or "",
        "insurance_type": args.insurance_type or "",
        "source_url": args.source_url or (args.url if args.url else ""),
        "access_date": today,
        "language": args.language,
        "has_pdf": False,
        "has_markdown": False,
        "notes": args.notes or "",
    }

    if args.url:
        archive_contract_url(args.url, contract_dir, metadata)
    elif args.file:
        file_path = Path(args.file)
        suffix_lower = file_path.suffix.lower()
        if suffix_lower in (".md", ".markdown", ".txt"):
            archive_contract_markdown(file_path, contract_dir, metadata)
        elif suffix_lower == ".pdf":
            archive_contract_pdf(file_path, contract_dir, metadata)
        else:
            # Try PDF detection by content
            raw_bytes = file_path.read_bytes()
            if utils.content_is_pdf(raw_bytes):
                archive_contract_pdf(file_path, contract_dir, metadata)
            else:
                # Treat as markdown/text
                archive_contract_markdown(file_path, contract_dir, metadata)

    metadata_file = contract_dir / "metadata.json"
    utils.atomic_write(
        metadata_file,
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
    )

    relative_path = str(contract_dir.relative_to(law_db_path))
    contract_updates = {
        relative_path: {
            "identifier": metadata["title"],
            "type": metadata["type"],
            "title": metadata["title"],
            "purpose": DEFAULT_PURPOSE,
            "accessed": today,
        },
    }

    utils.ensure_law_db_loaded()
    import law_db
    law_db.sync_index(law_db_path, contract_updates=contract_updates)

    print(f"archived {args.type}: {relative_path}")
    if metadata["has_pdf"]:
        print(f"  PDF: source.pdf")
    if metadata["has_markdown"]:
        print(f"  Markdown: source.md")

    if utils.verify_and_report_integrity(law_db_path) != 0:
        return 1

    return 0


if __name__ == "__main__":
    utils.run_cli(main)
