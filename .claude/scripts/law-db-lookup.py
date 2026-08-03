"""Lightweight external lookup — document and URL lookup.

Fetches document data by identifier or URL. Does NOT archive to law-db — use
`law-db` for archival. Returns JSON to stdout by default; use `--format text` for
human-readable output.
"""

import argparse
import json
import sys
import utils


def lookup_document(identifier):
    """Look up a document by its identifier.

    Placeholder for future integration with legal databases (EUR-Lex, RIS, etc.).
    Currently reports that external lookup is not yet implemented for the given source.
    """
    return {
        "source": "unknown",
        "identifier": identifier,
        "error": "External document lookup not yet implemented. Archive documents via 'uv run law-db --archive-url <URL>' instead.",
    }


def lookup_url(url):
    """Fetch and return information about a URL."""
    try:
        raw = utils.fetch_url(url, timeout=30)
        return {
            "source": "web",
            "url": url,
            "status": "fetched",
            "content_length": len(raw),
            "content_preview": raw[:500].strip(),
        }
    except RuntimeError as exc:
        return {
            "source": "web",
            "url": url,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _format_json(results):
    return json.dumps({"results": results}, indent=2, default=str, ensure_ascii=False)


def _format_text(results):
    lines = []
    for index, result in enumerate(results, 1):
        if "error" in result:
            lines.append(f"--- Result {index} ({result.get('source', 'unknown')}) ---")
            lines.append(f"ID/URL: {result.get('identifier') or result.get('url', 'N/A')}")
            lines.append(f"ERROR:  {result['error']}")
            lines.append("")
            continue

        lines.append(f"--- Result {index} ({result['source']}) ---")
        lines.append(f"URL:            {result.get('url', 'N/A')}")
        if "content_length" in result:
            lines.append(f"Content length: {result['content_length']} bytes")
        if "content_preview" in result:
            lines.append(f"Preview:        {result['content_preview'][:200]}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Lightweight external lookup — document or URL lookup. No archival.",
    )
    parser.add_argument(
        "--document",
        action="append",
        default=[],
        help="Document identifier to look up. May be passed multiple times.",
    )
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        help="URL to look up. May be passed multiple times.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. Defaults to json.",
    )

    args = parser.parse_args()
    if not args.document and not args.url:
        parser.error("provide at least one of --document or --url")
    return args


def main():
    args = parse_args()
    results = []

    for identifier in args.document:
        results.append(lookup_document(identifier))

    for url in args.url:
        results.append(lookup_url(url))

    if args.format == "text":
        print(_format_text(results))
    else:
        print(_format_json(results))

    return 1 if any("error" in r for r in results) else 0


if __name__ == "__main__":
    utils.run_cli(main)
