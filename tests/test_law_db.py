"""Tests for law-db.py — archival and index management."""

import datetime
import json
from pathlib import Path

import pytest

import law_db
import utils


# ---------------------------------------------------------------------------
# ensure_law_db_structure
# ---------------------------------------------------------------------------


class TestEnsureLawDbStructure:
    def test_creates_all_dirs(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts", "receipts"):
            assert (tmp_path / name).is_dir()


# ---------------------------------------------------------------------------
# validate_topic_slug
# ---------------------------------------------------------------------------


class TestValidateTopicSlug:
    def test_valid(self):
        assert law_db.validate_topic_slug("datenschutz") == "datenschutz"
        assert law_db.validate_topic_slug("eu-recht") == "eu-recht"
        assert law_db.validate_topic_slug("a") == "a"

    def test_invalid(self):
        with pytest.raises(ValueError):
            law_db.validate_topic_slug("../escape")
        with pytest.raises(ValueError):
            law_db.validate_topic_slug("path/traversal")
        with pytest.raises(ValueError):
            law_db.validate_topic_slug("")
        with pytest.raises(ValueError):
            law_db.validate_topic_slug("Invalid Uppercase")


# ---------------------------------------------------------------------------
# unique_filename
# ---------------------------------------------------------------------------


class TestUniqueFilename:
    def test_no_conflict(self, tmp_path):
        result = law_db.unique_filename(tmp_path, "test", ".json")
        assert result == "test.json"

    def test_with_conflict(self, tmp_path):
        (tmp_path / "test.json").write_text("")
        result = law_db.unique_filename(tmp_path, "test", ".json")
        assert result == "test-2.json"

    def test_multiple_conflicts(self, tmp_path):
        (tmp_path / "test.json").write_text("")
        (tmp_path / "test-2.json").write_text("")
        (tmp_path / "test-3.json").write_text("")
        result = law_db.unique_filename(tmp_path, "test", ".json")
        assert result == "test-4.json"


# ---------------------------------------------------------------------------
# index.json — load_existing_index_entries
# ---------------------------------------------------------------------------


class TestLoadExistingIndexEntries:
    def test_no_index(self, tmp_path):
        result = law_db.load_existing_index_entries(tmp_path / "index.json")
        assert result == ({}, {}, {}, {}, {}, {}, {})

    def test_preserves_entries(self, tmp_path):
        index = {
            "searches": [
                {"path": "searches/datenschutz/search.json", "query": "test", "purpose": "testing"},
            ],
            "documents": [],
            "fulltext": [],
            "guidelines": [],
            "web": [],
        }
        (tmp_path / "index.json").write_text(json.dumps(index))
        searches, documents, fulltexts, guidelines, web, contracts, receipts = law_db.load_existing_index_entries(
            tmp_path / "index.json"
        )
        assert "searches/datenschutz/search.json" in searches
        assert searches["searches/datenschutz/search.json"]["purpose"] == "testing"

    def test_invalid_json_fallback(self, tmp_path):
        (tmp_path / "index.json").write_text("not json {{{")
        result = law_db.load_existing_index_entries(tmp_path / "index.json")
        assert result == ({}, {}, {}, {}, {}, {}, {})


# ---------------------------------------------------------------------------
# index.json — collect_index_data
# ---------------------------------------------------------------------------


class TestCollectIndexData:
    def test_empty_archive(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        searches, documents, fulltexts, guidelines, web, contracts, receipts = law_db.collect_index_data(tmp_path)
        assert searches == []
        assert documents == []
        assert fulltexts == []
        assert guidelines == []
        assert web == []

    def test_documents_collected(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        doc_dir = tmp_path / "documents" / "datenschutz" / "doc-test"
        doc_dir.mkdir(parents=True)
        (doc_dir / "metadata.json").write_text('{"title": "Test Doc"}')
        searches, documents, fulltexts, guidelines, web, contracts, receipts = law_db.collect_index_data(tmp_path)
        assert len(documents) == 1
        assert documents[0]["path"].startswith("documents/")

    def test_web_collected(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        web_dir = tmp_path / "web" / "datenschutz"
        web_dir.mkdir(parents=True)
        (web_dir / "page.html").write_text("<html></html>")
        searches, documents, fulltexts, guidelines, web, contracts, receipts = law_db.collect_index_data(tmp_path)
        assert len(web) == 1

    def test_guidelines_collected(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        gdir = tmp_path / "guidelines" / "eu-law"
        gdir.mkdir(parents=True)
        (gdir / "source.md").write_text("---\ntitle: Test\n---\n# Content")
        searches, documents, fulltexts, guidelines, web, contracts, receipts = law_db.collect_index_data(tmp_path)
        assert len(guidelines) == 1


# ---------------------------------------------------------------------------
# sync_index
# ---------------------------------------------------------------------------


class TestSyncIndex:
    def test_creates_index(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        law_db.sync_index(tmp_path)
        assert (tmp_path / "index.json").is_file()
        data = json.loads((tmp_path / "index.json").read_text())
        assert "searches" in data
        assert "documents" in data

    def test_preserves_user_metadata(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        doc_dir = tmp_path / "documents" / "datenschutz" / "doc-test"
        doc_dir.mkdir(parents=True)
        (doc_dir / "metadata.json").write_text('{"title": "Test"}')

        # First sync
        law_db.sync_index(tmp_path)

        # Manually edit purpose
        index = json.loads((tmp_path / "index.json").read_text())
        index["documents"][0]["purpose"] = "Custom purpose"
        (tmp_path / "index.json").write_text(json.dumps(index))

        # Second sync should preserve purpose
        law_db.sync_index(tmp_path)
        data = json.loads((tmp_path / "index.json").read_text())
        assert data["documents"][0]["purpose"] == "Custom purpose"


# ---------------------------------------------------------------------------
# archive_url
# ---------------------------------------------------------------------------


def _fake_fetch_html(url):
    return """<!doctype html>
<html lang="en">
<head>
  <title>Test Law Document</title>
</head>
<body>
  <h1>Test Law Document</h1>
  <p>This is the full text of a test legal document for archival verification.</p>
  <p>It contains multiple paragraphs for content verification.</p>
</body>
</html>"""


def _fake_fetch_plain(url):
    return "Plain text legal document.\nSection 1: Test content.\nSection 2: More content."


def _fake_fetch_fails(url):
    raise RuntimeError("simulated network failure")


TEST_URL = "https://example.com/law/doc"


class TestArchiveUrl:
    def test_creates_document_structure(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        result = law_db.archive_url(TEST_URL, tmp_path, "test-topic", fetch_func=_fake_fetch_html)
        assert result is not None
        metadata_file, source_url = result
        assert metadata_file.is_file()
        meta = json.loads(metadata_file.read_text())
        assert meta["url"] == TEST_URL
        assert meta["has_fulltext"] is True
        assert meta["content_type"] == "text/html"
        assert meta["title"] == "Test Law Document"

    def test_stores_full_text(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        result = law_db.archive_url(TEST_URL, tmp_path, "test-topic", fetch_func=_fake_fetch_html)
        metadata_file, source_url = result
        source_file = metadata_file.parent / "source.md"
        assert source_file.is_file()
        content = source_file.read_text()
        assert "full text of a test legal document" in content
        assert "<html" not in content  # HTML stripped

    def test_handles_plain_text(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        result = law_db.archive_url(TEST_URL, tmp_path, "test-topic", fetch_func=_fake_fetch_plain)
        metadata_file, source_url = result
        meta = json.loads(metadata_file.read_text())
        assert meta["content_type"] == "text/plain"
        source_file = metadata_file.parent / "source.md"
        assert source_file.is_file()

    def test_handles_fetch_failure(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        result = law_db.archive_url("https://example.com/broken", tmp_path, "test-topic", fetch_func=_fake_fetch_fails)
        assert result is not None  # Still returns — stores stub
        metadata_file, source_url = result
        meta = json.loads(metadata_file.read_text())
        assert meta["has_fulltext"] is False
        assert "fetch_error" in meta
        assert "simulated network failure" in meta["fetch_error"]
        source_file = metadata_file.parent / "source.md"
        assert not source_file.is_file()  # No source.md on failure

    def test_title_extraction_falls_back(self, tmp_path):
        """HTML without <title> uses <h1> or URL fallback."""
        no_title_html = "<html><body><h1>Second Title</h1><p>Content.</p></body></html>"
        law_db.ensure_law_db_structure(tmp_path)
        result = law_db.archive_url(TEST_URL, tmp_path, "test-topic", fetch_func=lambda u: no_title_html)
        metadata_file, source_url = result
        meta = json.loads(metadata_file.read_text())
        assert meta["title"] == "Second Title"

    def test_skips_duplicate(self, tmp_path):
        law_db.ensure_law_db_structure(tmp_path)
        first = law_db.archive_url(TEST_URL, tmp_path, "test-topic", fetch_func=_fake_fetch_html)
        assert first is not None
        second = law_db.archive_url(TEST_URL, tmp_path, "test-topic", fetch_func=_fake_fetch_html)
        assert second is None


# ---------------------------------------------------------------------------
# slugify re-export
# ---------------------------------------------------------------------------


class TestSlugifyReexport:
    def test_slugify_reachable(self):
        """law-db re-exports slugify from utils; verify it produces the same output."""
        assert law_db.slugify("Hello World") == utils.slugify("Hello World")
        assert law_db.slugify("Österreichisches Recht") == "osterreichisches-recht"


# ---------------------------------------------------------------------------
# save_text (atomic write)
# ---------------------------------------------------------------------------


class TestSaveText:
    def test_saves_content(self, tmp_path):
        path = tmp_path / "test.txt"
        law_db.save_text(path, "hello")
        assert path.read_text() == "hello"

    def test_overwrites(self, tmp_path):
        path = tmp_path / "test.txt"
        path.write_text("old")
        law_db.save_text(path, "new")
        assert path.read_text() == "new"
