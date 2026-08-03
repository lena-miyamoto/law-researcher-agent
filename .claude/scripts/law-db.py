"""Archive legal research sources into the local law-db schema.

Supports web discovery sources (Google Scholar, DOAJ, Open Science Directory),
URL archiving, and search query archival.
"""

import argparse
import datetime
import html
import json
import re
import shutil
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


# Re-export canonical slugify for convenience
slugify = utils.slugify


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
    for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts"):
        (law_db / name).mkdir(parents=True, exist_ok=True)


def validate_topic_slug(topic):
    if not topic or topic in {".", ".."} or "/" in topic or "\\" in topic:
        raise ValueError(f"invalid topic slug: {topic!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic):
        raise ValueError(f"invalid topic slug: {topic!r}; expected kebab-case ASCII")
    return topic


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
        return {}, {}, {}, {}, {}, {}

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}, {}, {}, {}, {}, {}

    search_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("searches", [])}
    document_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("documents", [])}
    fulltext_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("fulltext", [])}
    guideline_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("guidelines", [])}
    web_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("web", [])}
    contract_entries = {entry["path"]: {k: v for k, v in entry.items() if k != "path"} for entry in data.get("contracts", [])}

    return search_entries, document_entries, fulltext_entries, guideline_entries, web_entries, contract_entries


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
            documents.append({
                "path": rel_dir,
                "identifier": "Review and refine identifier.",
                "url": "URL unavailable; review and refine.",
                "purpose": DEFAULT_DOCUMENT_PURPOSE,
                "accessed": today,
            })

    # Fulltext
    fulltext_dir = law_db / "fulltext"
    if fulltext_dir.is_dir():
        for meta_path in sorted(fulltext_dir.rglob("metadata.json")):
            ft_dir = meta_path.parent
            rel_dir = str(ft_dir.relative_to(law_db))
            fulltexts.append({
                "path": rel_dir,
                "identifier": "Review and refine identifier.",
                "url": "URL unavailable; review and refine.",
                "purpose": DEFAULT_DOCUMENT_PURPOSE,
                "accessed": today,
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
            contracts.append({
                "path": rel_dir,
                "identifier": "Review and refine identifier.",
                "type": "contract",
                "title": "Review and refine title.",
                "purpose": "Review and refine purpose.",
                "accessed": today,
            })

    return searches, documents, fulltexts, guidelines, web_sources, contracts


def sync_index(law_db, search_updates=None, document_updates=None, fulltext_updates=None, guideline_updates=None, web_updates=None, contract_updates=None):
    """Generate index.json from filesystem, merging in user-provided metadata."""
    index_path = law_db / "index.json"
    existing_searches, existing_documents, existing_fulltexts, existing_guidelines, existing_web, existing_contracts = load_existing_index_entries(index_path)

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

    fs_searches, fs_documents, fs_fulltexts, fs_guidelines, fs_web, fs_contracts = collect_index_data(law_db)

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


def archive_url(args, law_db, topic):
    """Archive a document from a URL."""
    topic_dir = law_db / "documents" / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    document_slug = slugify(args.archive_url, fallback="document", max_length=60)
    folder_name = f"url-{document_slug}"
    document_dir = topic_dir / folder_name
    if document_dir.exists():
        print(f"skipping already archived: {folder_name}", file=sys.stderr)
        return None
    document_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()
    metadata = {
        "source": "web",
        "url": args.archive_url,
        "access_date": today,
        "title": "Review and refine title.",
    }
    metadata_file = document_dir / "metadata.json"
    abstract_file = document_dir / "abstract.txt"
    save_text(metadata_file, json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    save_text(abstract_file, f"Content archived from: {args.archive_url}\nAccess date: {today}\nReview and refine.\n")

    return metadata_file, abstract_file, args.archive_url


def copy2_verified(source, destination):
    shutil.copy2(source, destination)
    if source.stat().st_size != destination.stat().st_size:
        raise OSError(f"copy size mismatch: {source} -> {destination}")


# ---------------------------------------------------------------------------
# Migration from old flat structure
# ---------------------------------------------------------------------------


def migrate_flat_to_topic(law_db, dry_run=False):
    """Migrate old flat metadata/ and abstracts/ into documents/_migrated/."""
    migrated = 0
    errors = 0

    old_metadata = law_db / "metadata"
    old_abstracts = law_db / "abstracts"
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
                copy2_verified(meta_path, dest_dir / "metadata.json")
                abstract_path = paper_dir / "abstract.txt"
                if abstract_path.is_file():
                    copy2_verified(abstract_path, dest_dir / "abstract.txt")
                else:
                    (dest_dir / "abstract.txt").write_text("Abstract not found in old location.\n", encoding="utf-8")
                migrated += 1
            except OSError as exc:
                errors += 1
                print(f"error migrating {paper_dir}: {exc}", file=sys.stderr)

    # Migrate old metadata/abstracts flat structure
    if old_metadata.is_dir():
        for meta_path in sorted(old_metadata.glob("*.json")):
            stem = meta_path.stem
            abstract_path = old_abstracts / f"{stem}.txt"
            topic_dir = law_db / "documents" / "_migrated" / stem
            if topic_dir.exists():
                continue
            if dry_run:
                migrated += 1
                print(f"[dry-run] would migrate: {stem}")
                continue
            topic_dir.mkdir(parents=True, exist_ok=True)
            try:
                copy2_verified(meta_path, topic_dir / "metadata.json")
                if abstract_path.is_file():
                    copy2_verified(abstract_path, topic_dir / "abstract.txt")
                else:
                    (topic_dir / "abstract.txt").write_text("Abstract not found in old flat abstracts/ directory.\n", encoding="utf-8")
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
                copy2_verified(search_path, dest_file)
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
                copy2_verified(web_path, dest_file)
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
        "--document",
        action="append",
        default=[],
        help="Document identifier to archive. May be passed multiple times.",
    )
    parser.add_argument(
        "--archive-url",
        action="append",
        default=[],
        help="URL to archive. May be passed multiple times.",
    )
    parser.add_argument(
        "--archive-first",
        type=int,
        default=0,
        help="Also archive the first N results returned by --query.",
    )
    parser.add_argument(
        "--retmax",
        type=int,
        default=20,
        help="How many hits to request for the archived search.",
    )
    parser.add_argument(
        "--law-db",
        default="law-db",
        help="Target law-db directory. Defaults to ./law-db.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.34,
        help="Delay between fetches in seconds. Defaults to 0.34.",
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

    if not args.query and not args.document and not args.archive_url:
        parser.error("provide --query and/or at least one document/URL identifier")
    if args.archive_first < 0:
        parser.error("--archive-first must be >= 0")
    if args.archive_first and not args.query:
        parser.error("--archive-first requires --query")
    if args.retmax < 1:
        parser.error("--retmax must be >= 1")
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

    topic = validate_topic_slug(args.topic_slug or slugify(args.topic, fallback=DEFAULT_TOPIC))

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
        result = archive_url(args, law_db, topic)
        if result is None:
            continue
        metadata_file, abstract_file, source_url = result
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
