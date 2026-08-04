"""Shared utilities for law-db scripts.

Constants, slugify, fetch helpers, and integrity check library.
"""

import html as _html
import json
import os
import re
import subprocess
import sys as _sys
import tempfile
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
# Filesystem helpers
# ---------------------------------------------------------------------------


def validate_topic_slug(topic):
    """Return *topic* if it is a valid kebab-case ASCII slug, otherwise raise."""
    if not topic or topic in {".", ".."} or "/" in topic or "\\" in topic:
        raise ValueError(f"invalid topic slug: {topic!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic):
        raise ValueError(f"invalid topic slug: {topic!r}; expected kebab-case ASCII")
    return topic


def unique_folder_name(directory, stem):
    """Return *stem*, or *stem*-2, *stem*-3, ... if already taken."""
    candidate = stem
    if not (directory / candidate).exists():
        return candidate
    counter = 2
    while True:
        candidate = f"{stem}-{counter}"
        if not (directory / candidate).exists():
            return candidate
        counter += 1


def copy_file_verified(source, destination):
    """Copy *source* to *destination* and verify sizes match.

    Uses :func:`shutil.copy2` to preserve metadata.
    """
    import shutil

    shutil.copy2(source, destination)
    if source.stat().st_size != destination.stat().st_size:
        raise OSError(f"copy size mismatch: {source} -> {destination}")


def ensure_law_db_loaded():
    """Load the ``law_db`` module via importlib if not already in ``sys.modules``.

    After calling this, ``import law_db`` will find the module in the cache.
    Used by scripts that call ``law_db.sync_index()`` without going through
    the ``law-db`` entry point.
    """
    import importlib.util
    import sys as _sys

    if "law_db" in _sys.modules:
        return

    spec = importlib.util.spec_from_file_location(
        "law_db", Path(__file__).parent / "law-db.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load law-db.py spec")
    module = importlib.util.module_from_spec(spec)
    _sys.modules["law_db"] = module
    spec.loader.exec_module(module)


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
# HTML → plain-text extraction
# ---------------------------------------------------------------------------


def _strip_html(text):
    """Strip HTML tags, decode entities, collapse whitespace.

    ``<script>`` and ``<style>`` blocks are removed entirely (including their
    content) — they never contain human-readable text meant for the reader.
    """
    if not text:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_main_content(raw_html, url=""):
    """Extract the main content from *raw_html*, excluding navigation, headers,
    footers, scripts, and styles.

    Uses BeautifulSoup to parse the HTML and tries a sequence of known
    content selectors.  When no selector matches, falls back to
    :func:`_strip_html` on the full page.

    Returns plain text with collapsed whitespace.
    """
    if not raw_html:
        return ""

    import bs4

    soup = bs4.BeautifulSoup(raw_html, "html.parser")

    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    content_selectors = [
        # EUR-Lex — document tab content
        "#document1 .tabContent",
        "#document1",
        # Generic semantic elements
        "article",
        "main",
        '[role="main"]',
    ]

    for selector in content_selectors:
        element = soup.select_one(selector)
        if element is None:
            continue
        text = element.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 20:
            return text

    return _strip_html(raw_html)



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


# ---------------------------------------------------------------------------
# CSV parsing — stdlib only, no new dependencies
# ---------------------------------------------------------------------------


def parse_csv_rows(file_path, delimiter=",", encoding="utf-8"):
    """Parse *file_path* as CSV, returning ``list[dict[str, str]]``.

    Uses :mod:`csv.DictReader`.  Skips completely empty rows and rows
    where every field is an empty string.  Handles encoding via *encoding*.
    """
    import csv as _csv

    with open(file_path, encoding=encoding, newline="") as handle:
        reader = _csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            return []
        rows = []
        for row in reader:
            if any(value.strip() for value in row.values() if isinstance(value, str)):
                rows.append(row)
        return rows


# ---------------------------------------------------------------------------
# PDF extraction — delegates to system binaries (poppler-utils pdftotext)
# ---------------------------------------------------------------------------


def clean_pdf_text(text):
    """Clean common PDF-extraction artifacts from *text*.

    Handles soft hyphens, de-hyphenation at line breaks, form feeds,
    page numbers, running headers, backspace characters, and whitespace
    normalisation.  Idempotent — safe to call on already-clean text.
    """
    # Character-level fixes (order matters)
    text = text.replace("\xad\n", "")
    text = text.replace("\xad", "")
    text = text.replace("\b", " ")
    text = text.replace("\f", "\n")

    # De-hyphenation: word-\\nword → wordword when continuation starts lowercase
    text = re.sub(
        r"(\w{2,})-\n(\w+)",
        lambda match: match.group(1) + match.group(2)
        if match.group(2)[0].islower()
        else match.group(1) + "-\n" + match.group(2),
        text,
    )

    # Line-level artifact removal
    lines = text.split("\n")
    cleaned = []

    for index, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            cleaned.append("")
            continue

        # Standalone arabic page numbers
        if re.match(r"^\d{1,4}$", stripped):
            if _looks_like_page_artifact(index, lines):
                continue

        # Standalone roman-numeral page numbers
        if re.match(r"^[ivxlcdm]{1,5}$", stripped.lower()):
            if _looks_like_page_artifact(index, lines):
                continue

        # Running headers: short, all-lowercase, no sentence-ending punctuation
        if (
            index > 0
            and len(stripped) < 40
            and stripped.islower()
            and not stripped.endswith((".", ",", "?", "!", ":", ";"))
            and not stripped.endswith("-")
        ):
            previous_empty = not lines[index - 1].strip()
            if previous_empty and _has_text_ahead(index, lines, lookahead=3):
                continue

        cleaned.append(stripped)

    # Whitespace normalisation: collapse 3+ blank lines to 2
    result = []
    blank_count = 0
    for line in cleaned:
        if line == "":
            blank_count += 1
        else:
            if blank_count > 0:
                result.extend([""] * min(blank_count, 2))
            blank_count = 0
            result.append(line)

    # Strip leading blank lines
    while result and result[0] == "":
        result.pop(0)

    return "\n".join(result) + "\n"


def _looks_like_page_artifact(index, lines):
    """Return True if line *index* is likely a page number, not body text."""
    if index == 0:
        return False
    previous_empty = not lines[index - 1].strip()
    if previous_empty and _has_text_ahead(index, lines, lookahead=2):
        return True
    if not previous_empty and _has_text_ahead(index, lines, lookahead=3):
        previous_stripped = lines[index - 1].strip()
        if not previous_stripped.endswith((".", ",", ":", ";")):
            return True
    return False


def _has_text_ahead(index, lines, lookahead=3):
    """Return True if any non-empty line exists within *lookahead* lines after *index*."""
    end = min(index + 1 + lookahead, len(lines))
    for position in range(index + 1, end):
        if lines[position].strip():
            return True
    return False


def content_is_pdf(raw_bytes):
    """Return True if *raw_bytes* looks like PDF content (magic bytes)."""
    return raw_bytes[:5] == b"%PDF-"


def pdf_bytes_to_markdown(raw_bytes, source_url="unknown"):
    """Extract text from *raw_bytes* (PDF content) via ``pdftotext -layout``.

    Returns cleaned Markdown-formatted text.  PDF-specific artifacts
    (soft hyphens, page numbers, running headers, form feeds) are
    removed via :func:`clean_pdf_text`.

    Raises RuntimeError if pdftotext fails or produces empty output
    (likely a scanned/image-only PDF requiring OCR).
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(raw_bytes)
        pdf_path = tmp_file.name

    try:
        process = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if process.returncode != 0:
            raise RuntimeError(
                f"pdftotext failed for {source_url}: {process.stderr}"
            )
        text = process.stdout.strip()
        if not text:
            raise RuntimeError(
                f"pdftotext produced empty output for {source_url} "
                f"(PDF may be scanned/image-only — OCR required)"
            )
        return clean_pdf_text(text)
    finally:
        _trash_or_unlink(pdf_path)


def _trash_or_unlink(file_path):
    """Move *file_path* to the desktop trash, falling back to permanent delete.

    Uses ``gio trash`` when available (GNOME/GLib).  Falls back to
    :func:`os.unlink` when ``gio`` is not on PATH.
    """
    path_string = str(file_path)
    if not os.path.lexists(path_string):
        return
    try:
        subprocess.run(
            ["gio", "trash", "-f", path_string],
            capture_output=True,
            timeout=10,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        os.unlink(path_string)


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
CATEGORY_CONTRACT = "contract"
CATEGORY_RECEIPT = "receipt"


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
    for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts", "receipts"):
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

    expected_keys = {"searches", "documents", "fulltext", "guidelines", "web", "contracts", "receipts"}
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
    actual_contracts = sorted(
        str(p.parent.relative_to(root))
        for p in (root / "contracts").rglob("metadata.json")
        if (root / "contracts").is_dir()
    )
    actual_receipts = sorted(
        str(p.parent.relative_to(root))
        for p in (root / "receipts").rglob("metadata.json")
        if (root / "receipts").is_dir()
    )

    index_searches = _indexed_paths(data, "searches")
    index_documents = _indexed_paths(data, "documents")
    index_fulltext = _indexed_paths(data, "fulltext")
    index_guidelines = _indexed_paths(data, "guidelines")
    index_web = _indexed_paths(data, "web")
    index_contracts = _indexed_paths(data, "contracts")
    index_receipts = _indexed_paths(data, "receipts")

    for label, indexed, on_disk, category in (
        ("search", index_searches, actual_searches, CATEGORY_SEARCH),
        ("document", index_documents, actual_documents, CATEGORY_METADATA),
        ("fulltext", index_fulltext, actual_fulltext, CATEGORY_METADATA),
        ("guideline", index_guidelines, actual_guidelines, CATEGORY_GUIDELINE),
        ("web", index_web, actual_web, CATEGORY_WEB),
        ("contract", index_contracts, actual_contracts, CATEGORY_CONTRACT),
        ("receipt", index_receipts, actual_receipts, CATEGORY_RECEIPT),
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


def check_contracts_integrity(root, findings):
    """Validate contract/AGB directories under contracts/."""
    contracts_dir = root / "contracts"
    if not contracts_dir.is_dir():
        return

    for meta_file in sorted(contracts_dir.rglob("metadata.json")):
        contract_dir = meta_file.parent
        relative_dir = str(contract_dir.relative_to(root))

        # Validate metadata.json JSON
        try:
            metadata = json.loads(_read_text(meta_file))
        except json.JSONDecodeError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_CONTRACT,
                    f"{relative_dir}/metadata.json",
                    f"metadata.json is not valid JSON: {exc}",
                    "Fix the JSON syntax error or re-archive the contract.",
                )
            )
            continue
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_CONTRACT,
                    relative_dir,
                    f"Cannot read metadata.json: {exc}",
                    "Check file permissions.",
                )
            )
            continue

        contract_type = metadata.get("type", "")
        if contract_type not in ("contract", "agb", "template"):
            findings.append(
                finding(
                    SEVERITY_WARNING,
                    CATEGORY_CONTRACT,
                    relative_dir,
                    f"Unrecognised contract type: {contract_type!r}",
                    "Set type to one of: contract, agb, template.",
                )
            )

        # At least one of source.pdf or source.md should exist
        has_pdf = metadata.get("has_pdf", False)
        has_markdown = metadata.get("has_markdown", False)

        if has_pdf:
            pdf_file = contract_dir / "source.pdf"
            if not pdf_file.is_file():
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_CONTRACT,
                        relative_dir,
                        "metadata.json claims has_pdf but source.pdf is missing.",
                        "Restore the PDF or update metadata.json has_pdf to false.",
                    )
                )
            elif pdf_file.stat().st_size == 0:
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_CONTRACT,
                        f"{relative_dir}/source.pdf",
                        "source.pdf is empty (zero bytes).",
                        "Re-download or remove the empty file.",
                    )
                )

        if has_markdown:
            markdown_file = contract_dir / "source.md"
            if not markdown_file.is_file():
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_CONTRACT,
                        relative_dir,
                        "metadata.json claims has_markdown but source.md is missing.",
                        "Re-extract the markdown or update metadata.json has_markdown to false.",
                    )
                )
            else:
                try:
                    content = _read_text(markdown_file).strip()
                    if not content:
                        findings.append(
                            finding(
                                SEVERITY_ERROR,
                                CATEGORY_CONTRACT,
                                f"{relative_dir}/source.md",
                                "source.md exists but is empty.",
                                "Re-extract the markdown content.",
                            )
                        )
                except OSError as exc:
                    findings.append(
                        finding(
                            SEVERITY_ERROR,
                            CATEGORY_CONTRACT,
                            f"{relative_dir}/source.md",
                            f"Cannot read source.md: {exc}",
                            "Check file permissions.",
                        )
                    )

        if not has_pdf and not has_markdown:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_CONTRACT,
                    relative_dir,
                    "Contract directory has neither source.pdf nor source.md.",
                    "Archive at least one of the PDF or extracted markdown.",
                )
            )


def check_receipts_integrity(root, findings):
    """Validate receipt/tax-document directories under receipts/."""
    receipts_dir = root / "receipts"
    if not receipts_dir.is_dir():
        return

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

    for meta_file in sorted(receipts_dir.rglob("metadata.json")):
        receipt_dir = meta_file.parent
        relative_dir = str(receipt_dir.relative_to(root))

        # Validate metadata.json JSON
        try:
            metadata = json.loads(_read_text(meta_file))
        except json.JSONDecodeError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_RECEIPT,
                    f"{relative_dir}/metadata.json",
                    f"metadata.json is not valid JSON: {exc}",
                    "Fix the JSON syntax error or re-archive the receipt.",
                )
            )
            continue
        except OSError as exc:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_RECEIPT,
                    relative_dir,
                    f"Cannot read metadata.json: {exc}",
                    "Check file permissions.",
                )
            )
            continue

        subtype = metadata.get("subtype", "")
        if subtype not in VALID_SUBTYPES:
            findings.append(
                finding(
                    SEVERITY_WARNING,
                    CATEGORY_RECEIPT,
                    relative_dir,
                    f"Unrecognised receipt subtype: {subtype!r}",
                    f"Set subtype to one of: {', '.join(sorted(VALID_SUBTYPES))}.",
                )
            )

        tax_category = metadata.get("tax_category", "")
        if tax_category not in VALID_TAX_CATEGORIES:
            findings.append(
                finding(
                    SEVERITY_WARNING,
                    CATEGORY_RECEIPT,
                    relative_dir,
                    f"Unrecognised tax category: {tax_category!r}",
                    f"Set tax_category to one of: {', '.join(sorted(VALID_TAX_CATEGORIES))}.",
                )
            )

        has_pdf = metadata.get("has_pdf", False)
        has_markdown = metadata.get("has_markdown", False)
        has_csv = metadata.get("has_csv", False)

        if has_pdf:
            pdf_file = receipt_dir / "source.pdf"
            if not pdf_file.is_file():
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_RECEIPT,
                        relative_dir,
                        "metadata.json claims has_pdf but source.pdf is missing.",
                        "Restore the PDF or update metadata.json has_pdf to false.",
                    )
                )
            elif pdf_file.stat().st_size == 0:
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_RECEIPT,
                        f"{relative_dir}/source.pdf",
                        "source.pdf is empty (zero bytes).",
                        "Re-download or remove the empty file.",
                    )
                )

        if has_markdown:
            markdown_file = receipt_dir / "source.md"
            if not markdown_file.is_file():
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_RECEIPT,
                        relative_dir,
                        "metadata.json claims has_markdown but source.md is missing.",
                        "Re-extract the markdown or update metadata.json has_markdown to false.",
                    )
                )
            else:
                try:
                    content = _read_text(markdown_file).strip()
                    if not content:
                        findings.append(
                            finding(
                                SEVERITY_ERROR,
                                CATEGORY_RECEIPT,
                                f"{relative_dir}/source.md",
                                "source.md exists but is empty.",
                                "Re-extract the markdown content.",
                            )
                        )
                except OSError as exc:
                    findings.append(
                        finding(
                            SEVERITY_ERROR,
                            CATEGORY_RECEIPT,
                            f"{relative_dir}/source.md",
                            f"Cannot read source.md: {exc}",
                            "Check file permissions.",
                        )
                    )

        if has_csv:
            csv_file = receipt_dir / "source.csv"
            if not csv_file.is_file():
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_RECEIPT,
                        relative_dir,
                        "metadata.json claims has_csv but source.csv is missing.",
                        "Restore the CSV or update metadata.json has_csv to false.",
                    )
                )
            elif csv_file.stat().st_size == 0:
                findings.append(
                    finding(
                        SEVERITY_ERROR,
                        CATEGORY_RECEIPT,
                        f"{relative_dir}/source.csv",
                        "source.csv is empty (zero bytes).",
                        "Re-export or remove the empty file.",
                    )
                )

        if not has_pdf and not has_markdown and not has_csv:
            findings.append(
                finding(
                    SEVERITY_ERROR,
                    CATEGORY_RECEIPT,
                    relative_dir,
                    "Receipt directory has neither source.pdf, source.md, nor source.csv.",
                    "Archive at least one source file.",
                )
            )


def check_legacy_dirs(root, findings):
    """Warn about old flat directories left over from pre-migration layouts."""
    for name in ("metadata", "papers"):
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
    check_contracts_integrity(root, findings)
    check_receipts_integrity(root, findings)

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
