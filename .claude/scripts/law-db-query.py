"""Query the local law-db archive.

Provides CLI access to inspect the law-db filesystem structure: list topics,
check whether a document is already archived, read document metadata,
and search by keyword.

All operations are read-only filesystem queries. No network calls.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

import utils

STATUTE_EXPIRY_DAYS = 365


# Re-export canonical slugify for convenience
slugify = utils.slugify


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------



def _read_json_with_error(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid metadata json: {exc}"
    except OSError as exc:
        return None, f"could not read metadata json: {exc}"


def _document_metadata(document_dir):
    meta, error = _read_json_with_error(document_dir / "metadata.json")
    if meta is None:
        return {"error": error}, None

    title = meta.get("title", "Unknown title")
    source = meta.get("source", "unknown")
    url = meta.get("url", "")
    identifier = meta.get("identifier") or url or "unknown"

    return {
        "source": source,
        "identifier": identifier,
        "title": title,
        "url": url,
        "access_date": meta.get("access_date", ""),
    }, meta


# ---------------------------------------------------------------------------
# Core query functions
# ---------------------------------------------------------------------------


def list_topics(law_db):
    """List all topics with document and search counts."""
    topics = {}

    documents_dir = law_db / "documents"
    searches_dir = law_db / "searches"

    for parent_dir, key in (
        (documents_dir, "document_count"),
        (searches_dir, "search_count"),
    ):
        if not parent_dir.is_dir():
            continue
        for child in sorted(parent_dir.iterdir()):
            if not child.is_dir():
                continue
            topic = child.name
            entry = topics.setdefault(
                topic, {"topic": topic, "document_count": 0, "search_count": 0}
            )
            if key == "document_count":
                entry["document_count"] = sum(
                    1 for p in child.rglob("metadata.json") if p.is_file()
                )
            else:
                entry["search_count"] = sum(
                    1 for p in child.rglob("*.json") if p.is_file()
                )

    return sorted(topics.values(), key=lambda t: t["topic"])


def list_topic_documents(law_db, topic):
    """List all documents archived under a topic."""
    topic_dir = law_db / "documents" / topic
    if not topic_dir.is_dir():
        return []

    documents = []
    for document_dir in sorted(topic_dir.iterdir()):
        if not document_dir.is_dir():
            continue
        meta_file = document_dir / "metadata.json"
        if not meta_file.is_file():
            continue
        info, _ = _document_metadata(document_dir)
        if info and "error" not in info:
            title = info.get("title", "Unknown title")
            identifier = info.get("identifier", "unknown")
            url = info.get("url", "")
        else:
            identifier = "unknown"
            url = ""
            title = "Unknown title"
        documents.append({
            "folder": str(document_dir.relative_to(law_db)),
            "identifier": identifier,
            "url": url,
            "title": title,
        })
    return documents


def check_document_archived(law_db, identifier):
    """Check if a document identifier is already archived anywhere under documents/."""
    documents_dir = law_db / "documents"
    if not documents_dir.is_dir():
        return {"identifier": identifier, "archived": False, "locations": []}

    identifier_lower = identifier.lower()
    locations = []
    for meta_path in sorted(documents_dir.rglob("metadata.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        stored = str(meta.get("identifier") or meta.get("url") or "").lower()
        if identifier_lower in stored or stored in identifier_lower:
            document_dir = meta_path.parent
            locations.append(str(document_dir.relative_to(law_db)))

    return {
        "identifier": identifier,
        "archived": len(locations) > 0,
        "locations": locations,
    }


def read_document_metadata(document_dir):
    """Read structured metadata from a document directory."""
    info, _ = _document_metadata(Path(document_dir))
    if info is None or "error" in info:
        detail = info.get("error") if info else "unknown error"
        return {"error": f"could not parse metadata from {document_dir}: {detail}"}
    return info


def search_keyword(law_db, keyword, topic=None, exclude_expired=False):
    """Search documents by keyword in title. Case-insensitive.

    When *exclude_expired* is True, documents whose ``access_date`` is more
    than ``STATUTE_EXPIRY_DAYS`` old are omitted.  Documents with a missing
    or unparseable ``access_date`` are retained (err on the side of showing
    results).
    """
    documents_dir = law_db / "documents"
    search_root = documents_dir / topic if topic else documents_dir
    if not search_root.is_dir():
        return []

    keyword_lower = keyword.lower()
    cutoff = None
    if exclude_expired:
        cutoff = datetime.date.today() - datetime.timedelta(days=STATUTE_EXPIRY_DAYS)
    matches = []

    for meta_path in sorted(search_root.rglob("metadata.json")):
        document_dir = meta_path.parent
        info, _ = _document_metadata(document_dir)
        if info is None or "error" in info:
            continue

        if exclude_expired and cutoff is not None:
            access_str = (info.get("access_date") or "").strip()
            if access_str:
                try:
                    access_date = datetime.date.fromisoformat(access_str)
                    if access_date < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass  # unparseable date → retain

        title = str(info.get("title", "")).lower()
        match_field = []
        match_snippet = ""

        if keyword_lower in title:
            match_field.append("title")
            idx = title.index(keyword_lower)
            start = max(0, idx - 30)
            end = min(len(title), idx + len(keyword_lower) + 30)
            match_snippet = ("..." if start > 0 else "") + str(info.get("title", ""))[start:end] + ("..." if end < len(title) else "")

        if match_field:
            matches.append({
                "folder": str(document_dir.relative_to(law_db)),
                "identifier": info.get("identifier", "unknown"),
                "url": info.get("url", ""),
                "title": info.get("title", "Unknown title"),
                "match_field": "+".join(match_field),
                "match_snippet": match_snippet,
            })

    return matches


def read_document_fulltext(document_dir):
    """Read the source.md from a document directory."""
    source_path = Path(document_dir) / "source.md"
    if not source_path.is_file():
        return None
    try:
        return source_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return f"Could not read full text: {exc}"


def recent_documents(law_db, count=10):
    """List the most recently added documents from index.json."""
    index_path = law_db / "index.json"
    if not index_path.is_file():
        return []

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    entries = []
    for document in data.get("documents", []):
        path_str = document.get("path", "")
        topic = path_str.split("/")[1] if "/" in path_str else "unknown"
        entries.append({
            "path": path_str,
            "identifier": document.get("identifier", "unknown"),
            "url": document.get("url", ""),
            "title": _document_title_from_path(law_db, path_str),
            "topic": topic,
            "accessed": document.get("accessed", ""),
        })

    entries.sort(key=lambda e: e["accessed"], reverse=True)
    return entries[:count]


def _document_title_from_path(law_db, rel_path):
    """Read the title from a document's metadata.json given its index path."""
    meta_path = law_db / rel_path / "metadata.json"
    if not meta_path.is_file():
        return "Unknown title"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "Unknown title"

    return meta.get("title", "Unknown title")


def search_searches(law_db, keyword, topic=None):
    """Keyword search within archived search JSON files' query text."""
    searches_dir = law_db / "searches"
    search_root = searches_dir / topic if topic else searches_dir
    if not search_root.is_dir():
        return []

    keyword_lower = keyword.lower()
    matches = []

    for search_path in sorted(search_root.rglob("*.json")):
        try:
            data = json.loads(search_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        query_text = data.get("query") or data.get("queryString") or ""

        if keyword_lower in query_text.lower():
            idx = query_text.lower().index(keyword_lower)
            start = max(0, idx - 30)
            end = min(len(query_text), idx + len(keyword_lower) + 30)
            snippet = ("..." if start > 0 else "") + query_text[start:end] + ("..." if end < len(query_text) else "")

            matches.append({
                "path": str(search_path.relative_to(law_db)),
                "source": data.get("source", "unknown"),
                "query": query_text,
                "match_snippet": snippet,
            })

    return matches


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _format_json(result):
    return json.dumps(result, indent=2, default=str, ensure_ascii=False)


def _format_text(result, command):
    if command == "list-topics":
        if not result.get("topics"):
            return "No topics found."
        lines = ["Topics:"]
        for t in result["topics"]:
            lines.append(f"  {t['topic']}: {t['document_count']} documents, {t['search_count']} searches")
        return "\n".join(lines)

    if command == "topic-documents":
        documents = result.get("documents", [])
        if not documents:
            return "No documents found for this topic."
        lines = [f"Documents in '{result['topic']}':"]
        for d in documents:
            lines.append(f"  {d['folder']}")
            lines.append(f"    {d['identifier']}")
            lines.append(f"    {d['title'][:120]}")
        return "\n".join(lines)

    if command == "check-document":
        if result["archived"]:
            lines = [f"Document '{result['identifier']}': ARCHIVED"]
            for loc in result["locations"]:
                lines.append(f"  {loc}")
        else:
            lines = [f"Document '{result['identifier']}': NOT ARCHIVED"]
        return "\n".join(lines)

    if command == "read-metadata":
        if "error" in result:
            return f"Error: {result['error']}"
        lines = [
            f"Title:      {result.get('title', 'N/A')}",
            f"Source:     {result.get('source', 'N/A')}",
            f"Identifier: {result.get('identifier', 'N/A')}",
            f"URL:        {result.get('url', 'N/A')}",
            f"Accessed:   {result.get('access_date', 'N/A')}",
        ]
        fulltext = result.get("fulltext")
        if fulltext:
            lines.append("")
            lines.append("Full Text:")
            lines.extend(utils.wrap_text(fulltext))
        return "\n".join(lines)

    if command == "search-keyword":
        matches = result.get("matches", [])
        if not matches:
            return f"No matches for '{result.get('keyword', '')}'."
        summary = result.get("summary", False)
        if summary:
            lines = [f"Keyword '{result.get('keyword', '')}': {result.get('match_count', len(matches))} match(es)"]
            for m in matches:
                lines.append(f"  {m['identifier']}: {m['title'][:120]}")
            return "\n".join(lines)
        lines = [f"Keyword '{result.get('keyword', '')}': {len(matches)} match(es)"]
        for m in matches:
            lines.append(f"  {m['folder']}")
            lines.append(f"    {m['identifier']}: {m['title'][:100]}")
            lines.append(f"    matched in: {m['match_field']}")
        return "\n".join(lines)

    if command == "recent":
        documents = result.get("documents", [])
        if not documents:
            return "No recently added documents found."
        lines = [f"Recent documents ({len(documents)}):"]
        for d in documents:
            lines.append(f"  {d['accessed']}  {d['identifier']}  [{d['topic']}]")
            lines.append(f"    {d['title'][:120]}")
        return "\n".join(lines)

    if command == "search-searches":
        matches = result.get("matches", [])
        if not matches:
            return f"No matching searches for '{result.get('keyword', '')}'."
        lines = [f"Search keyword '{result.get('keyword', '')}': {len(matches)} match(es)"]
        for m in matches:
            lines.append(f"  {m['path']}")
            lines.append(f"    source: {m['source']}")
            lines.append(f"    query:  {m['query'][:120]}")
        return "\n".join(lines)

    return json.dumps(result, indent=2, default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query the local law-db archive.",
    )
    parser.add_argument(
        "--law-db",
        default="law-db",
        help="Path to law-db root directory. Defaults to ./law-db.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. Defaults to json.",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-topics", action="store_true", help="List all topics with document and search counts.")
    group.add_argument("--topic", type=str, help="List all documents under a topic.")
    group.add_argument("--check-document", type=str, help="Check if a document identifier is already archived.")
    group.add_argument("--read-metadata", type=str, help="Read metadata from a document directory.")
    group.add_argument("--search-keyword", type=str, help="Search documents by keyword (case-insensitive).")
    group.add_argument("--recent", type=int, help="List N most recently added documents.")
    group.add_argument("--search-searches", type=str, help="Search archived search queries by keyword (case-insensitive).")
    parser.add_argument(
        "--search-topic",
        type=str,
        help="Optional topic scope for --search-keyword or --search-searches.",
    )
    parser.add_argument(
        "--show-fulltext",
        action="store_true",
        help="Include full text (source.md) with --read-metadata output.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Compact output for --search-keyword (identifiers and titles only, no snippets).",
    )
    parser.add_argument(
        "--exclude-expired",
        action="store_true",
        help="With --search-keyword: omit documents whose access_date is older than 365 days. Missing/unparseable dates are retained.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    law_db = Path(args.law_db)

    if not law_db.is_dir():
        print(json.dumps({"error": f"law-db directory not found: {law_db}"}), file=sys.stderr)
        return 1

    command = None
    result = None

    if args.list_topics:
        command = "list-topics"
        result = {"topics": list_topics(law_db)}
    elif args.topic:
        command = "topic-documents"
        result = {"topic": args.topic, "documents": list_topic_documents(law_db, args.topic)}
    elif args.check_document:
        command = "check-document"
        result = check_document_archived(law_db, args.check_document)
    elif args.read_metadata:
        command = "read-metadata"
        result = read_document_metadata(args.read_metadata)
        if args.show_fulltext and "error" not in result:
            fulltext = read_document_fulltext(args.read_metadata)
            if fulltext is not None:
                result["fulltext"] = fulltext
    elif args.search_keyword:
        command = "search-keyword"
        matches = search_keyword(law_db, args.search_keyword, topic=args.search_topic, exclude_expired=args.exclude_expired)
        result = {
            "keyword": args.search_keyword,
            "match_count": len(matches),
            "matches": matches,
            "summary": args.summary,
        }
    elif args.recent:
        command = "recent"
        documents = recent_documents(law_db, count=args.recent)
        result = {"documents": documents}
    elif args.search_searches:
        command = "search-searches"
        matches = search_searches(law_db, args.search_searches, topic=args.search_topic)
        result = {
            "keyword": args.search_searches,
            "match_count": len(matches),
            "matches": matches,
        }

    if args.format == "text":
        print(_format_text(result, command))
    else:
        print(_format_json(result))

    return 0


if __name__ == "__main__":
    utils.run_cli(main)
