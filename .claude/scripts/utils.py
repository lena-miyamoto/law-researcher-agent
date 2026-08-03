"""Shared utilities for law-db scripts.

Constants, slugify, fetch helpers, and integrity check library.
"""

import html as _html
import json
import re
import sys as _sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository paths — canonical single source for all scripts
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LAW_DB = REPO_ROOT / "law-db"

# ---------------------------------------------------------------------------
# API / network constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# slugify — canonical version (NFKD → ASCII → kebab-case)
# ---------------------------------------------------------------------------


def slugify(text, fallback="record", max_words=10, max_length=80):
    """Normalise *text* into an ASCII kebab-case slug."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if not text:
        return fallback
    words = [word for word in text.split("-") if word]
    text = "-".join(words[:max_words])
    return text[:max_length].rstrip("-") or fallback


# ---------------------------------------------------------------------------
# atomic_write — safe file writes (tmp + rename)
# ---------------------------------------------------------------------------


def atomic_write(path, content):
    """Write *content* to *path* atomically via a temporary file + rename.

    On POSIX ``Path.replace`` is atomic when the source and destination are
    on the same filesystem.  This prevents corruption if the process crashes
    mid-write.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Fetch helper
# ---------------------------------------------------------------------------


def fetch_url(url, timeout=60, retries=2, retry_delay=0.25):
    """GET *url*, return decoded UTF-8 body.

    Raises ``RuntimeError`` on network / HTTP errors.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset("utf-8")
                try:
                    return raw.decode(charset)
                except UnicodeDecodeError:
                    return raw.decode(charset, errors="replace")
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code < 500 or attempt == retries:
                break
        except (urllib.error.URLError, OSError) as exc:
            last_error = exc
            if attempt == retries:
                break
        if retry_delay > 0:
            time.sleep(retry_delay * (2 ** attempt))
    raise RuntimeError(f"error fetching {url}: {last_error}")


# ---------------------------------------------------------------------------
# _strip_html — lightweight HTML → plain-text
# ---------------------------------------------------------------------------


def _strip_html(text):
    """Strip HTML tags, decode entities, collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# wrap_text — word-wrap a string to a given width
# ---------------------------------------------------------------------------


def wrap_text(text, width=80):
    """Word-wrap *text* to *width* columns, returning a list of lines."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if not current_line:
            current_line = word
        elif len(current_line) + len(word) + 1 > width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = f"{current_line} {word}"
    if current_line:
        lines.append(current_line)
    return lines


# =============================================================================
# law-db integrity check — shared library
# =============================================================================
#
# These functions are used by both the standalone law-db-integrity-check CLI
# (thin wrapper in law-db-integrity-check.py) and by every script that modifies
# law-db/ (law-db.py, etc.).  After a modification, call
# ``verify_and_report_integrity(root)`` — it returns 0 on success and prints
# actionable error details on failure so an agent can fix issues immediately.

from collections import Counter as _Counter

# --- finding model -----------------------------------------------------------

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

CATEGORY_STRUCTURAL = "structural"
CATEGORY_INDEX = "index"
CATEGORY_METADATA = "metadata"
CATEGORY_SEARCH = "search"
CATEGORY_WEB = "web"
CATEGORY_GUIDELINE = "guideline"


def finding(severity, category, location, description, fix_hint):
    """Create a structured finding dict."""
    return {
        "severity": severity,
        "category": category,
        "location": location,
        "description": description,
        "fix": fix_hint,
    }


# --- tiny helpers ------------------------------------------------------------


def _read_text(path):
    return Path(path).read_text(encoding="utf-8")


def _indexed_paths(data, key):
    """Return sorted list of ``path`` values from an index category."""
    return sorted(entry["path"] for entry in data.get(key, []))


# --- check functions — each appends to ``findings`` --------------------------


def check_required_dirs(root, findings):
    for name in ("searches", "documents", "fulltext", "guidelines", "web"):
        p = root / name
        if not p.is_dir():
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_STRUCTURAL,
                    str(p),
                    f"Required top-level directory is missing: {name}/",
                    f"Run any archival command (e.g. 'uv run law-db --document EXAMPLE') to bootstrap the directory tree.",
                )
            )


def check_empty_files(root, findings):
    for p in root.rglob("*"):
        if p.is_file() and p.stat().st_size == 0:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_STRUCTURAL,
                    str(p.relative_to(root)),
                    "File is empty (zero bytes).",
                    "Remove the empty file or populate it with valid content.",
                )
            )


def check_index_valid(root, findings):
    index_path = root / "index.json"
    if not index_path.is_file():
        findings.append(
            finding(
                SEVERITY_ERROR,
                CATEGORY_INDEX,
                "index.json",
                "index.json is missing — the archive has no master index.",
                "Run any archival command to auto-create index.json, or restore from backup.",
            )
        )
        return None

    try:
        data = json.loads(_read_text(index_path))
    except json.JSONDecodeError as exc:
        findings.append(
            finding(
                SEVERITY_ERROR,
                CATEGORY_INDEX,
                "index.json",
                f"index.json is not valid JSON: {exc}",
                "Fix the JSON syntax error or restore from a known-good backup.",
            )
        )
        return None
    except OSError as exc:
        findings.append(
            finding(
                SEVERITY_ERROR,
                CATEGORY_INDEX,
                "index.json",
                f"Cannot read index.json: {exc}",
                "Check file permissions and disk health.",
            )
        )
        return None

    expected_keys = {"searches", "documents", "fulltext", "guidelines", "web"}
    actual_keys = set(data.keys())
    missing_keys = expected_keys - actual_keys
    extra_keys = actual_keys - expected_keys

    for key in sorted(missing_keys):
        findings.append(
            finding(
                SEVERITY_ERROR,
                CATEGORY_INDEX,
                "index.json",
                f"index.json is missing required top-level key: \"{key}\"",
                f"Add a \"{key}\": [] entry to index.json.",
            )
        )
    for key in sorted(extra_keys):
        findings.append(
            finding(
                SEVERITY_WARNING,
                CATEGORY_INDEX,
                "index.json",
                f"index.json contains unrecognised top-level key: \"{key}\"",
                "Remove the key if it is stale; otherwise update the validator to recognise it.",
            )
        )

    if missing_keys:
        return None  # can't proceed with cross-reference checks

    # Duplicate paths within each category
    for key in sorted(expected_keys):
        paths = [entry.get("path", "") for entry in data.get(key, [])]
        dup_counts = {p: c for p, c in _Counter(paths).items() if c > 1}
        for p, count in sorted(dup_counts.items()):
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_INDEX,
                    f"index.json → {key}",
                    f"Duplicate path appears {count}× in \"{key}\" index: {p}",
                    "Remove the duplicate entries, keeping only one copy.",
                )
            )

    return data


def check_index_crossref(root, data, findings):
    """Cross-reference index.json entries against the filesystem."""
    actual_searches = sorted(
        str(p.relative_to(root))
        for p in (root / "searches").rglob("*.json")
        if (root / "searches").is_dir()
    )
    actual_documents = sorted(
        str(p.parent.relative_to(root))
        for p in (root / "documents").rglob("metadata.json")
        if (root / "documents").is_dir()
    )
    actual_fulltext = sorted(
        str(p.parent.relative_to(root))
        for p in (root / "fulltext").rglob("metadata.json")
        if (root / "fulltext").is_dir()
    )
    actual_guidelines = sorted(
        set(
            str(p.parent.relative_to(root))
            for pattern in ("source.md", "source.*.md")
            for p in (root / "guidelines").rglob(pattern)
            if (root / "guidelines").is_dir()
        )
    )
    actual_web = sorted(
        str(p.relative_to(root))
        for p in (root / "web").rglob("*")
        if p.is_file() and (root / "web").is_dir()
    )

    index_searches = _indexed_paths(data, "searches")
    index_documents = _indexed_paths(data, "documents")
    index_fulltext = _indexed_paths(data, "fulltext")
    index_guidelines = _indexed_paths(data, "guidelines")
    index_web = _indexed_paths(data, "web")

    for label, indexed, on_disk, category in (
        ("search", index_searches, actual_searches, CATEGORY_SEARCH),
        ("document", index_documents, actual_documents, CATEGORY_METADATA),
        ("fulltext", index_fulltext, actual_fulltext, CATEGORY_METADATA),
        ("guideline", index_guidelines, actual_guidelines, CATEGORY_GUIDELINE),
        ("web", index_web, actual_web, CATEGORY_WEB),
    ):
        missing = sorted(set(indexed) - set(on_disk))
        extra = sorted(set(on_disk) - set(indexed))

        for item in missing:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    category,
                    item,
                    f"Indexed in index.json → {label}s but not found on disk.",
                    "Remove the stale index entry, or restore the missing file from backup.",
                )
            )
        for item in extra:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    category,
                    item,
                    f"Exists on disk but is not listed in index.json → {label}s.",
                    f"Add an entry to the \"{label}s\" array in index.json for this file/directory.",
                )
            )


def check_document_integrity(root, findings):
    documents_dir = root / "documents"
    if not documents_dir.is_dir():
        return

    for meta_file in sorted(documents_dir.rglob("metadata.json")):
        document_dir = meta_file.parent
        rel_dir = str(document_dir.relative_to(root))

        # abstract.txt
        abstract_file = document_dir / "abstract.txt"
        if not abstract_file.is_file():
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_METADATA,
                    rel_dir,
                    "Document directory is missing abstract.txt.",
                    "Fetch the abstract or restore from backup.",
                )
            )

        # Validate metadata.json JSON
        try:
            json.loads(_read_text(meta_file))
        except json.JSONDecodeError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_METADATA,
                    f"{rel_dir}/metadata.json",
                    f"metadata.json is not valid JSON: {exc}",
                    "Fix the JSON syntax error or re-fetch the document.",
                )
            )

    # Check abstract content (non-empty after stripping)
    for abs_file in sorted(documents_dir.rglob("abstract.txt")):
        rel = str(abs_file.relative_to(root))
        try:
            content = _read_text(abs_file).strip()
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_METADATA,
                    rel,
                    f"Cannot read abstract.txt: {exc}",
                    "Check file permissions.",
                )
            )
            continue
        if not content:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_METADATA,
                    rel,
                    "abstract.txt exists but contains only whitespace.",
                    "Fetch the abstract for this document.",
                )
            )


def check_search_json(root, findings):
    searches_dir = root / "searches"
    if not searches_dir.is_dir():
        return

    for path in sorted(searches_dir.rglob("*.json")):
        rel = str(path.relative_to(root))
        try:
            data = json.loads(_read_text(path))
        except json.JSONDecodeError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_SEARCH,
                    rel,
                    f"Search JSON is not valid JSON: {exc}",
                    "Re-run the search or restore from backup.",
                )
            )
            continue
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_SEARCH,
                    rel,
                    f"Cannot read search file: {exc}",
                    "Check file permissions.",
                )
            )
            continue

        if not isinstance(data, dict):
            continue

        # Generic search JSON — just verify it's valid (parsed above)
        if data:
            continue

        findings.append(
            finding(
                SEVERITY_WARNING,
                CATEGORY_SEARCH,
                rel,
                "Search JSON is empty.",
                "Verify the file is a valid search artifact; if so, this warning can be ignored.",
            )
        )


def check_web_files(root, findings):
    web_dir = root / "web"
    if not web_dir.is_dir():
        return

    for path in sorted(web_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        try:
            content = _read_text(path)
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_WEB,
                    rel,
                    f"Cannot read web file: {exc}",
                    "Check file permissions.",
                )
            )
            continue

        if not content.strip():
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_WEB,
                    rel,
                    "Web file is empty (no content after stripping whitespace).",
                    "Remove or re-download the file.",
                )
            )

        if path.suffix == ".html" and "<html" not in content.lower():
            findings.append(
                finding(
                    SEVERITY_WARNING,
                    CATEGORY_WEB,
                    rel,
                    "HTML file does not contain <html> tag — may not be valid HTML.",
                    "Re-download the page if the content looks incomplete.",
                )
            )


def check_guideline_integrity(root, findings):
    guidelines_dir = root / "guidelines"
    if not guidelines_dir.is_dir():
        return

    for src_file in sorted(guidelines_dir.rglob("source.md")):
        rel = str(src_file.relative_to(root))
        try:
            content = _read_text(src_file)
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_GUIDELINE,
                    rel,
                    f"Cannot read guideline source file: {exc}",
                    "Check file permissions.",
                )
            )
            continue

        if not content.strip():
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_GUIDELINE,
                    rel,
                    "Guideline source.md is empty.",
                    "Restore from backup or re-run the setup command.",
                )
            )

        # Check for YAML frontmatter
        if not content.startswith("---"):
            findings.append(
                finding(
                    SEVERITY_WARNING,
                    CATEGORY_GUIDELINE,
                    rel,
                    "Guideline source.md is missing YAML frontmatter (does not start with ---).",
                    "Add proper frontmatter with title, authors, source, source_url, access_date, language, and extraction_notes.",
                )
            )

    # Also check source.*.md files (e.g. source.de.md)
    for src_file in sorted(guidelines_dir.rglob("source.*.md")):
        rel = str(src_file.relative_to(root))
        try:
            content = _read_text(src_file)
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_GUIDELINE,
                    rel,
                    f"Cannot read guideline source file: {exc}",
                    "Check file permissions.",
                )
            )
            continue
        if not content.strip():
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_GUIDELINE,
                    rel,
                    "Guideline source file is empty.",
                    "Restore from backup or re-run the setup command.",
                )
            )


def check_legacy_dirs(root, findings):
    """Warn about old flat directories left over from pre-migration layouts."""
    for name in ("metadata", "abstracts", "papers"):
        legacy = root / name
        if legacy.is_dir():
            findings.append(
                finding(
                    SEVERITY_WARNING,
                    CATEGORY_STRUCTURAL,
                    str(legacy),
                    f"Legacy flat directory \"{name}/\" still exists after migration.",
                    f"Verify all content has been migrated to documents/, then remove: rm -rf {legacy}",
                )
            )


# --- orchestration -----------------------------------------------------------


def run_integrity_check(root):
    """Run all integrity checks on *root* and return a list of finding dicts.

    Does NOT format output or exit — purely a library function.  Callers
    (CLI wrapper, modifying scripts) decide how to present results.
    """
    root = Path(root)
    findings = []

    if not root.is_dir():
        findings.append(
            finding(
                SEVERITY_ERROR,
                CATEGORY_STRUCTURAL,
                str(root),
                f"law-db directory not found: {root}",
                "Create the directory or check the path.",
            )
        )
        return findings

    # Phase 1: structural checks (fast, no index needed)
    check_required_dirs(root, findings)

    fatal_structural = [
        f for f in findings
        if f["severity"] == SEVERITY_ERROR and f["category"] == CATEGORY_STRUCTURAL
    ]
    if fatal_structural:
        check_empty_files(root, findings)
        return findings

    check_empty_files(root, findings)

    # Phase 2: index-dependent checks
    data = check_index_valid(root, findings)
    if data is not None:
        check_index_crossref(root, data, findings)

    # Phase 3: content integrity
    check_document_integrity(root, findings)
    check_search_json(root, findings)
    check_web_files(root, findings)
    check_guideline_integrity(root, findings)

    # Phase 4: legacy / cleanup
    check_legacy_dirs(root, findings)

    return findings


def verify_and_report_integrity(root):
    """Run integrity check, print issues, return 0 (clean) or 1 (errors).

    Designed for use at the end of every script that modifies law-db/.
    Silent on success; prints a compact error report to stderr on failure
    so the calling agent can see and fix issues immediately.
    """
    findings = run_integrity_check(root)
    errors = [f for f in findings if f["severity"] == SEVERITY_ERROR]
    warnings = [f for f in findings if f["severity"] == SEVERITY_WARNING]

    if not findings:
        return 0

    # Compact error report to stderr
    print("\n--- law-db integrity check ---", file=_sys.stderr)
    for f in errors + warnings:
        prefix = "ERROR" if f["severity"] == SEVERITY_ERROR else "WARNING"
        print(f"{prefix} [{f['category']}] {f['location']}", file=_sys.stderr)
        print(f"  Problem: {f['description']}", file=_sys.stderr)
        print(f"  Fix: {f['fix']}", file=_sys.stderr)

    if errors:
        print(
            f"\n✗ Integrity check FAILED: {len(errors)} error(s), {len(warnings)} warning(s). "
            f"Fix the errors above to prevent data loss.",
            file=_sys.stderr,
        )
        return 1
    else:
        print(
            f"✓ Integrity check passed with {len(warnings)} warning(s).",
            file=_sys.stderr,
        )
        return 0


# ---------------------------------------------------------------------------
# run_cli — canonical CLI entry-point wrapper
# ---------------------------------------------------------------------------


def run_cli(main_func):
    """Run *main_func* as a CLI entry point with KeyboardInterrupt handling.

    Usage::

        if __name__ == "__main__":
            utils.run_cli(main)
    """
    try:
        raise SystemExit(main_func())
    except KeyboardInterrupt:
        print("cancelled", file=_sys.stderr)
        raise SystemExit(130)
