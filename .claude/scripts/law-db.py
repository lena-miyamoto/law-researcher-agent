"""Archive legal research sources into the local law-db schema.

Supports web discovery sources (Google Scholar, DOAJ, Open Science Directory),
URL archiving, and search query archival.
"""

import argparse
import datetime
import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

import utils

# ---------------------------------------------------------------------------
# Web-source URL bases
# ---------------------------------------------------------------------------

GOOGLE_SCHOLAR_BASE = "https://scholar.google.com/scholar"
DOAJ_ARTICLES_BASE = "https://doaj.org/search/articles"
OPEN_SCIENCE_DIRECTORY_BASE = "https://opensciencedirectory.net/"

DEFAULT_SEARCH_PURPOSE = "Archived via law-db.py; review and refine purpose."
DEFAULT_DOCUMENT_PURPOSE = "Archived via law-db.py; review and refine purpose."
DEFAULT_WEB_PURPOSE = "Archived web source; review and refine purpose."
DEFAULT_TOPIC = "uncategorized"


# Re-export canonical utilities for convenience
slugify = utils.slugify
validate_topic_slug = utils.validate_topic_slug


def unique_filename(directory, stem, suffix):
    """Return stem.suffix, or stem-N.suffix if stem.suffix already exists."""
    candidate = f"{stem}{suffix}"
    path = directory / candidate
    if not path.exists():
        return candidate
    n = 2
    while True:
        candidate = f"{stem}-{n}{suffix}"
        if not (directory / candidate).exists():
            return candidate
        n += 1


def save_text(path, content):
    utils.atomic_write(path, content)


def ensure_law_db_structure(law_db):
    for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts", "receipts"):
        (law_db / name).mkdir(parents=True, exist_ok=True)


def source_label(source_name):
    spec = WEB_SOURCE_SPECS.get(source_name)
    if spec:
        return spec["label"]
    return source_name


def build_google_scholar_url(query):
    return f"{GOOGLE_SCHOLAR_BASE}?{urllib.parse.urlencode({'q': query, 'hl': 'en'})}"


def build_doaj_url(query):
    payload = {
        "query": {
            "multi_match": {
                "query": query,
                "operator": "and",
            }
        },
        "size": 10,
        "track_total_hits": True,
    }
    params = {
        "ref": "homepage",
        "source": json.dumps(payload, separators=(",", ":")),
    }
    return f"{DOAJ_ARTICLES_BASE}?{urllib.parse.urlencode(params)}"


WEB_SOURCE_SPECS = {
    "google-scholar": {
        "label": "Google Scholar",
        "filename_prefix": "google-scholar",
        "landing_url": GOOGLE_SCHOLAR_BASE,
        "query_url_builder": build_google_scholar_url,
    },
    "doaj": {
        "label": "Directory of Open Access Journals",
        "filename_prefix": "doaj",
        "landing_url": DOAJ_ARTICLES_BASE,
        "query_url_builder": build_doaj_url,
    },
    "open-science-directory": {
        "label": "Open Science Directory",
        "filename_prefix": "open-science-directory",
        "landing_url": OPEN_SCIENCE_DIRECTORY_BASE,
    },
}


# ---------------------------------------------------------------------------
# index.json generation
# ---------------------------------------------------------------------------


def load_existing_index_entries(index_path):
    """Parse existing index.json to preserve user-edited purposes and metadata."""
    if not index_path.is_file():
        return {}, {}, {}, {}, {}, {}, {}

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}, {}, {}, {}, {}, {}, {}

    search_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("searches", [])}
    document_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("documents", [])}
    fulltext_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("fulltext", [])}
    guideline_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("guidelines", [])}
    web_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("web", [])}
    contract_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("contracts", [])}
    receipt_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("receipts", [])}

    return search_entries, document_entries, fulltext_entries, guideline_entries, web_entries, contract_entries, receipt_entries


def collect_index_data(law_db):
    """Walk the filesystem and collect entries for index.json."""
    today = datetime.date.today().isoformat()
    searches = []
    documents = []
    fulltexts = []
    guidelines = []
    web_sources = []

    # Searches
    searches_dir = law_db / "searches"
    if searches_dir.is_dir():
        for path in sorted(searches_dir.rglob("*.json")):
            rel = str(path.relative_to(law_db))
            searches.append({
                "path": rel,
                "source": "Archived search",
                "query": "Query unavailable; review and refine.",
                "purpose": DEFAULT_SEARCH_PURPOSE,
                "accessed": today,
            })

    # Documents
    documents_dir = law_db / "documents"
    if documents_dir.is_dir():
        for meta_path in sorted(documents_dir.rglob("metadata.json")):
            document_dir = meta_path.parent
            rel_dir = str(document_dir.relative_to(law_db))
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}
            documents.append({
                "path": rel_dir,
                "identifier": meta.get("url") or meta.get("identifier") or "Review and refine identifier.",
                "url": meta.get("url") or "URL unavailable; review and refine.",
                "purpose": meta.get("purpose") or DEFAULT_DOCUMENT_PURPOSE,
                "accessed": meta.get("access_date") or today,
            })

    # Fulltext
    fulltext_dir = law_db / "fulltext"
    if fulltext_dir.is_dir():
        for meta_path in sorted(fulltext_dir.rglob("metadata.json")):
            ft_dir = meta_path.parent
            rel_dir = str(ft_dir.relative_to(law_db))
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}
            fulltexts.append({
                "path": rel_dir,
                "identifier": meta.get("url") or meta.get("identifier") or "Review and refine identifier.",
                "url": meta.get("url") or "URL unavailable; review and refine.",
                "purpose": meta.get("purpose") or DEFAULT_DOCUMENT_PURPOSE,
                "accessed": meta.get("access_date") or today,
            })

    # Guidelines
    guidelines_dir = law_db / "guidelines"
    if guidelines_dir.is_dir():
        seen_dirs = set()
        for pattern in ("source.md", "source.*.md"):
            for source_path in sorted(guidelines_dir.rglob(pattern)):
                guideline_dir = source_path.parent
                rel_dir = str(guideline_dir.relative_to(law_db))
                if rel_dir in seen_dirs:
                    continue
                seen_dirs.add(rel_dir)
                guidelines.append({
                    "path": rel_dir,
                    "source": "Review and refine source.",
                    "url": "URL unavailable; review and refine.",
                    "purpose": DEFAULT_DOCUMENT_PURPOSE,
                    "accessed": today,
                })

    # Web
    web_dir = law_db / "web"
    if web_dir.is_dir():
        for path in sorted(web_dir.rglob("*.html")):
            rel = str(path.relative_to(law_db))
            web_sources.append({
                "path": rel,
                "url": "URL unavailable; review and refine.",
                "purpose": DEFAULT_WEB_PURPOSE,
                "accessed": today,
            })

    # Contracts
    contracts = []
    contracts_dir = law_db / "contracts"
    if contracts_dir.is_dir():
        for meta_path in sorted(contracts_dir.rglob("metadata.json")):
            contract_dir = meta_path.parent
            rel_dir = str(contract_dir.relative_to(law_db))
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}
            contracts.append({
                "path": rel_dir,
                "identifier": meta.get("url") or meta.get("identifier") or "Review and refine identifier.",
                "type": meta.get("type") or "contract",
                "title": meta.get("title") or "Review and refine title.",
                "purpose": meta.get("purpose") or "Review and refine purpose.",
                "accessed": meta.get("access_date") or today,
            })

    # Receipts
    receipts = []
    receipts_dir = law_db / "receipts"
    if receipts_dir.is_dir():
        for meta_path in sorted(receipts_dir.rglob("metadata.json")):
            receipt_dir = meta_path.parent
            rel_dir = str(receipt_dir.relative_to(law_db))
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}
            receipts.append({
                "path": rel_dir,
                "identifier": meta.get("url") or meta.get("identifier") or "Review and refine identifier.",
                "subtype": meta.get("subtype") or "receipt",
                "title": meta.get("title") or "Review and refine title.",
                "tax_category": meta.get("tax_category") or "other",
                "purpose": meta.get("purpose") or "Review and refine purpose.",
                "accessed": meta.get("access_date") or today,
            })

    return searches, documents, fulltexts, guidelines, web_sources, contracts, receipts


def sync_index(law_db, search_updates=None, document_updates=None, fulltext_updates=None, guideline_updates=None, web_updates=None, contract_updates=None, receipt_updates=None):
    """Generate index.json from filesystem, merging in user-provided metadata."""
    index_path = law_db / "index.json"
    existing_searches, existing_documents, existing_fulltexts, existing_guidelines, existing_web, existing_contracts, existing_receipts = load_existing_index_entries(index_path)

    if search_updates:
        existing_searches.update(search_updates)
    if document_updates:
        existing_documents.update(document_updates)
    if fulltext_updates:
        existing_fulltexts.update(fulltext_updates)
    if guideline_updates:
        existing_guidelines.update(guideline_updates)
    if web_updates:
        existing_web.update(web_updates)
    if contract_updates:
        existing_contracts.update(contract_updates)
    if receipt_updates:
        existing_receipts.update(receipt_updates)

    fs_searches, fs_documents, fs_fulltexts, fs_guidelines, fs_web, fs_contracts, fs_receipts = collect_index_data(law_db)

    def _merge(fs_list, existing_dict):
        result = []
        for item in fs_list:
            entry = existing_dict.get(item["path"], {})
            merged = dict(item)
            merged.update(entry)
            result.append(merged)
        return result

    index_data = {
        "searches": _merge(fs_searches, existing_searches),
        "documents": _merge(fs_documents, existing_documents),
        "fulltext": _merge(fs_fulltexts, existing_fulltexts),
        "guidelines": _merge(fs_guidelines, existing_guidelines),
        "web": _merge(fs_web, existing_web),
        "contracts": _merge(fs_contracts, existing_contracts),
        "receipts": _merge(fs_receipts, existing_receipts),
    }
    index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Archive operations
# ---------------------------------------------------------------------------


def archive_web_query(args, law_db, topic):
    spec = WEB_SOURCE_SPECS[args.source]
    query_url_builder = spec.get("query_url_builder")
    target_url = query_url_builder(args.query) if query_url_builder else spec["landing_url"]
    topic_dir = law_db / "web" / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    web_slug = args.search_slug or slugify(args.query, fallback=f"{spec['filename_prefix']}-search")
    filename = unique_filename(topic_dir, f"{spec['filename_prefix']}-{web_slug}", ".html")
    web_file = topic_dir / filename
    today = datetime.date.today().isoformat()
    if query_url_builder:
        archive_note = (
            f"This file archives a reproducible {spec['label']} search URL for discovery use in the law-db workflow."
        )
        link_label = f"Open this {spec['label']} query"
    else:
        archive_note = (
            "This source does not expose a stable public query URL in this workflow. "
            "This file preserves the query text together with the source landing page used for manual lookup."
        )
        link_label = f"Open the {spec['label']} search entry"
    html_body = "\n".join([
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        f"  <title>{spec['label']} query archive: {html.escape(args.query)}</title>",
        "</head>",
        "<body>",
        f"  <h1>{spec['label']} Query Archive</h1>",
        f"  <p><strong>Source:</strong> {spec['label']}</p>",
        f"  <p><strong>Query:</strong> {html.escape(args.query)}</p>",
        f"  <p><strong>Access date:</strong> {today}</p>",
        f"  <p>{archive_note}</p>",
        f"  <p><a href=\"{target_url}\">{link_label}</a></p>",
        "</body>",
        "</html>",
    ])
    save_text(web_file, html_body + "\n")
    return web_file, target_url


def _extract_title_from_html(raw_html, url):
    """Extract a title from HTML content — ``<title>``, first ``<h1>``, or URL fallback."""
    import re as _re

    match = _re.search(r"<title[^>]*>(.*?)</title>", raw_html, _re.IGNORECASE | _re.DOTALL)
    if match:
        title = utils._strip_html(match.group(1)).strip()
        if title:
            return title
    match = _re.search(r"<h1[^>]*>(.*?)</h1>", raw_html, _re.IGNORECASE | _re.DOTALL)
    if match:
        title = utils._strip_html(match.group(1)).strip()
        if title:
            return title
    return f"Document from {url}"


def archive_url(url, law_db, topic, fetch_func=None):
    """Archive a document from *url* — fetch, store full text, extract metadata."""
    topic_dir = law_db / "documents" / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    document_slug = slugify(url, fallback="document", max_length=60)
    folder_name = f"url-{document_slug}"
    document_dir = topic_dir / folder_name
    if document_dir.exists():
        print(f"skipping already archived: {folder_name}", file=sys.stderr)
        return None
    document_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()
    fetch = fetch_func if fetch_func is not None else utils.fetch_url

    try:
        raw_content = fetch(url)
    except RuntimeError as exc:
        raw_content = None
        fetch_error = str(exc)

    if raw_content is not None:
        looks_html = raw_content.strip()[:500].lower()
        if looks_html.startswith("<!doctype html") or looks_html.startswith("<html") or "<html" in looks_html:
            text_content = utils.extract_main_content(raw_content, url)
            content_type = "text/html"
        else:
            text_content = raw_content
            content_type = "text/plain"

        source_file = document_dir / "source.md"
        save_text(source_file, text_content)

        title = _extract_title_from_html(raw_content, url) if content_type == "text/html" else f"Document from {url}"

        has_fulltext = True
        content_length = len(raw_content)
    else:
        content_type = "unknown"
        title = "Review and refine title."
        has_fulltext = False
        content_length = 0

    metadata = {
        "source": "web",
        "url": url,
        "access_date": today,
        "title": title,
        "content_type": content_type,
        "content_length": content_length,
        "has_fulltext": has_fulltext,
    }
    if raw_content is None:
        metadata["fetch_error"] = fetch_error

    metadata_file = document_dir / "metadata.json"
    save_text(metadata_file, json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    return metadata_file, url




# ---------------------------------------------------------------------------
# Migration from old flat structure
# ---------------------------------------------------------------------------


def migrate_flat_to_topic(law_db, dry_run=False):
    """Migrate old flat metadata/ into documents/_migrated/."""
    migrated = 0
    errors = 0

    old_metadata = law_db / "metadata"
    old_searches = law_db / "searches"
    old_papers = law_db / "papers"

    # Migrate from old papers/ to documents/
    if old_papers.is_dir():
        for meta_path in sorted(old_papers.rglob("metadata.json")):
            paper_dir = meta_path.parent
            rel_parts = paper_dir.relative_to(old_papers).parts
            dest_dir = law_db / "documents" / "_migrated" / "/".join(rel_parts)
            if dest_dir.exists():
                continue
            if dry_run:
                migrated += 1
                print(f"[dry-run] would migrate: {paper_dir}")
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                utils.copy_file_verified(meta_path, dest_dir / "metadata.json")
                migrated += 1
            except OSError as exc:
                errors += 1
                print(f"error migrating {paper_dir}: {exc}", file=sys.stderr)

    # Migrate old metadata/ flat structure
    if old_metadata.is_dir():
        for meta_path in sorted(old_metadata.glob("*.json")):
            stem = meta_path.stem
            topic_dir = law_db / "documents" / "_migrated" / stem
            if topic_dir.exists():
                continue
            if dry_run:
                migrated += 1
                print(f"[dry-run] would migrate: {stem}")
                continue
            topic_dir.mkdir(parents=True, exist_ok=True)
            try:
                utils.copy_file_verified(meta_path, topic_dir / "metadata.json")
                migrated += 1
            except OSError as exc:
                errors += 1
                print(f"error migrating {stem}: {exc}", file=sys.stderr)

    # Migrate searches
    if old_searches.is_dir():
        for search_path in sorted(old_searches.glob("*.json")):
            dest_dir = law_db / "searches" / "_migrated"
            dest_file = dest_dir / search_path.name
            if dest_file.exists():
                continue
            if dry_run:
                migrated += 1
                print(f"[dry-run] would migrate search: {search_path.name}")
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                utils.copy_file_verified(search_path, dest_file)
                migrated += 1
            except OSError as exc:
                errors += 1
                print(f"error migrating search {search_path.name}: {exc}", file=sys.stderr)

    # Migrate web
    old_web = law_db / "web"
    if old_web.is_dir():
        for web_path in sorted(old_web.glob("*.html")):
            dest_dir = law_db / "web" / "_migrated"
            dest_file = dest_dir / web_path.name
            if dest_file.exists():
                continue
            if dry_run:
                migrated += 1
                print(f"[dry-run] would migrate web: {web_path.name}")
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                utils.copy_file_verified(web_path, dest_file)
                migrated += 1
            except OSError as exc:
                errors += 1
                print(f"error migrating web {web_path.name}: {exc}", file=sys.stderr)

    if dry_run:
        print(f"Would migrate {migrated} items ({errors} errors).")
    else:
        print(f"Migrated {migrated} items ({errors} errors).")
        if migrated > 0:
            print("Original files preserved. Verify the new structure, then remove old flat directories.")
    return 0 if errors == 0 else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Archive legal research sources into the local law-db schema.",
    )
    parser.add_argument(
        "--source",
        choices=tuple(WEB_SOURCE_SPECS),
        default="google-scholar",
        help="Primary source for the current run. Defaults to google-scholar.",
    )
    parser.add_argument("--query", help="Search query to archive for the selected source.")
    parser.add_argument("--search-slug", help="Optional slug for the saved search file.")
    parser.add_argument(
        "--topic",
        help="Legal topic for grouping output (e.g. datenschutz, mietrecht). Defaults to 'uncategorized'.",
        default=DEFAULT_TOPIC,
    )
    parser.add_argument(
        "--topic-slug",
        help="Explicit kebab-case slug for the topic folder. Overrides --topic if both are given.",
    )
    parser.add_argument(
        "--archive-url",
        action="append",
        default=[],
        help="URL to archive. May be passed multiple times.",
    )
    parser.add_argument(
        "--law-db",
        default="law-db",
        help="Target law-db directory. Defaults to ./law-db.",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate existing flat law-db/ structure to topic-based per-document folders. Preserves originals.",
    )
    parser.add_argument(
        "--migrate-dry-run",
        action="store_true",
        help="Preview --migrate without copying files.",
    )
    args = parser.parse_args()

    if args.migrate or args.migrate_dry_run:
        return args

    if not args.query and not args.archive_url:
        parser.error("provide --query and/or --archive-url")
    return args


def main():
    args = parse_args()
    law_db = Path(args.law_db)

    if args.migrate or args.migrate_dry_run:
        law_db.mkdir(parents=True, exist_ok=True)
        ensure_law_db_structure(law_db)
        result = migrate_flat_to_topic(law_db, dry_run=args.migrate_dry_run)
        if result != 0:
            return result
        if not args.migrate_dry_run:
            sync_index(law_db)
            if utils.verify_and_report_integrity(law_db) != 0:
                return 1
        return 0

    law_db.mkdir(parents=True, exist_ok=True)
    ensure_law_db_structure(law_db)

    topic = utils.validate_topic_slug(args.topic_slug or slugify(args.topic, fallback=DEFAULT_TOPIC))

    web_updates = {}
    document_updates = {}
    search_updates = {}

    if args.query:
        web_file, query_url = archive_web_query(args, law_db, topic)
        web_updates[str(web_file.relative_to(law_db))] = {
            "url": query_url,
            "purpose": DEFAULT_WEB_PURPOSE,
            "accessed": datetime.date.today().isoformat(),
        }

    for url in args.archive_url:
        result = archive_url(url, law_db, topic)
        if result is None:
            continue
        metadata_file, source_url = result
        document_updates[str(metadata_file.parent.relative_to(law_db))] = {
            "identifier": source_url,
            "url": source_url,
            "purpose": DEFAULT_DOCUMENT_PURPOSE,
            "accessed": datetime.date.today().isoformat(),
        }

    sync_index(law_db, search_updates=search_updates, document_updates=document_updates, web_updates=web_updates)

    if web_updates:
        print("archived web sources:")
        for filename, details in sorted(web_updates.items()):
            print(f"- {filename}: {details['url']}")
    else:
        print("saved search: none")

    if document_updates:
        print("archived documents:")
        for path, details in sorted(document_updates.items()):
            print(f"- {path}: {details['url']}")
    else:
        print("archived documents: none")

    if utils.verify_and_report_integrity(law_db) != 0:
        return 1

    return 0


if __name__ == "__main__":
    utils.run_cli(main)
