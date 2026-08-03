"""Tests for utils.py — shared helpers used across law-db scripts."""

import json
import sys
import urllib.error
from pathlib import Path

import pytest

import utils


class _FakeHeaders:
    def __init__(self, charset="utf-8"):
        self.charset = charset

    def get_content_charset(self, default="utf-8"):
        return self.charset or default


class _FakeResponse:
    def __init__(self, body, charset="utf-8"):
        self.body = body
        self.headers = _FakeHeaders(charset)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.body


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_basic_english(self):
        assert utils.slugify("Hello World") == "hello-world"

    def test_with_special_chars(self):
        assert utils.slugify("Legal & Regulatory (compliance)") == "legal-regulatory-compliance"

    def test_unicode_to_ascii(self):
        """NFKD normalization converts accented chars to ASCII."""
        result = utils.slugify("café naïve étude")
        assert result == "cafe-naive-etude"

    def test_german_umlauts(self):
        result = utils.slugify("Österreichisches Recht")
        assert result == "osterreichisches-recht"

    def test_empty_string_fallback(self):
        assert utils.slugify("") == "record"

    def test_only_special_chars_fallback(self):
        assert utils.slugify("!@#$%") == "record"

    def test_custom_fallback(self):
        assert utils.slugify("!!!", fallback="custom-fb") == "custom-fb"

    def test_max_words_truncation(self):
        result = utils.slugify(
            "one two three four five six seven eight nine ten eleven twelve",
            max_words=5,
        )
        assert result == "one-two-three-four-five"

    def test_max_length_truncation(self):
        result = utils.slugify("a very long title that exceeds the character limit easily", max_length=25)
        assert len(result) <= 25
        assert result == "a-very-long-title-that-ex"

    def test_max_length_doesnt_end_with_hyphen(self):
        result = utils.slugify("abcdef-ghijklm-nopqrstuv", max_length=13)
        assert not result.endswith("-")

    def test_consecutive_special_chars(self):
        assert utils.slugify("hello---world___test") == "hello-world-test"

    def test_str_coerces_non_string(self):
        """Should handle numeric input via str()."""
        assert utils.slugify(35350465) == "35350465"

    def test_default_max_words(self):
        """max_words defaults to 10."""
        result = utils.slugify("a " * 15)
        assert result.count("-") == 9  # 10 words, 9 hyphens

    def test_default_max_length(self):
        """max_length defaults to 80, rstrip hyphen."""
        long_text = "a" * 100
        assert len(utils.slugify(long_text)) <= 80

    def test_nfkd_vs_no_nfkd_non_ascii_slug_difference(self):
        """Prove NFKD normalisation matters for non-ASCII input."""
        assert utils.slugify("Käse-Törtchen") == "kase-tortchen"


# ---------------------------------------------------------------------------
# fetch_url
# ---------------------------------------------------------------------------


class TestFetchUrl:
    def test_raises_runtime_error_on_failure(self):
        """Network errors raise RuntimeError."""
        with pytest.raises(RuntimeError):
            utils.fetch_url("https://nonexistent.invalid.example", timeout=0.1)

    def test_includes_user_agent(self):
        """The request should carry a User-Agent header."""
        assert len(utils.USER_AGENT) > 20

    def test_retries_transient_failure(self, monkeypatch):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append((request, timeout))
            if len(calls) == 1:
                raise urllib.error.URLError("temporary reset")
            return _FakeResponse(b'{"ok": true}')

        monkeypatch.setattr(utils.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(utils.time, "sleep", lambda delay: None)

        assert utils.fetch_url("https://example.com", timeout=5) == '{"ok": true}'
        assert len(calls) == 2

    def test_decodes_declared_charset(self, monkeypatch):
        def fake_urlopen(request, timeout):
            return _FakeResponse("café".encode("iso-8859-1"), charset="iso-8859-1")

        monkeypatch.setattr(utils.urllib.request, "urlopen", fake_urlopen)

        assert utils.fetch_url("https://example.com", timeout=5) == "café"

    def test_does_not_retry_client_http_error(self, monkeypatch):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request)
            raise urllib.error.HTTPError(request.full_url, 404, "not found", {}, None)

        monkeypatch.setattr(utils.urllib.request, "urlopen", fake_urlopen)

        with pytest.raises(RuntimeError):
            utils.fetch_url("https://example.com/missing", timeout=5)
        assert len(calls) == 1


# ---------------------------------------------------------------------------
# _strip_html
# ---------------------------------------------------------------------------


class TestStripHtml:
    def test_removes_tags(self):
        assert utils._strip_html("<p>Hello</p>") == "Hello"

    def test_decodes_entities(self):
        assert utils._strip_html("&amp;") == "&"
        assert utils._strip_html("&lt;") == "<"
        assert utils._strip_html("&gt;") == ">"

    def test_collapses_whitespace(self):
        assert utils._strip_html("<p>a  b</p>") == "a b"

    def test_empty_string(self):
        assert utils._strip_html("") == ""
        assert utils._strip_html(None) == ""

    def test_nested_tags(self):
        assert utils._strip_html("<div><p>text</p></div>") == "text"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_user_agent_not_empty(self):
        assert len(utils.USER_AGENT) > 0
        assert "Mozilla" in utils.USER_AGENT

    def test_repo_paths(self):
        assert utils.REPO_ROOT.is_dir()
        assert utils.LAW_DB.name == "law-db"


# ---------------------------------------------------------------------------
# wrap_text
# ---------------------------------------------------------------------------


class TestWrapText:
    def test_wraps_at_default_width(self):
        text = "a " * 50  # 100 words, each "a"
        lines = utils.wrap_text(text, width=20)
        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 20

    def test_empty_string(self):
        assert utils.wrap_text("") == []

    def test_shorter_than_width(self):
        assert utils.wrap_text("hello world", width=80) == ["hello world"]

    def test_exact_width_word(self):
        assert utils.wrap_text("abcdefghij", width=10) == ["abcdefghij"]

    def test_long_single_word(self):
        """A single word longer than width is not split — it stays on its own line."""
        lines = utils.wrap_text("supercalifragilisticexpialidocious", width=10)
        assert lines == ["supercalifragilisticexpialidocious"]


# ---------------------------------------------------------------------------
# run_cli
# ---------------------------------------------------------------------------


class TestRunCli:
    def test_normal_exit(self, capsys):
        def fake_main():
            return 42

        with pytest.raises(SystemExit) as exc:
            utils.run_cli(fake_main)
        assert exc.value.code == 42
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_keyboard_interrupt(self, capsys):
        def fake_main():
            raise KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc:
            utils.run_cli(fake_main)
        assert exc.value.code == 130
        captured = capsys.readouterr()
        assert "cancelled" in captured.err

    def test_exception_propagates(self):
        def fake_main():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            utils.run_cli(fake_main)


# ---------------------------------------------------------------------------
# Integrity check — finding factory and constants
# ---------------------------------------------------------------------------


class TestFinding:
    def test_all_fields_populated(self):
        f = utils.finding(
            severity=utils.SEVERITY_ERROR,
            category=utils.CATEGORY_STRUCTURAL,
            location="documents/datenschutz",
            description="Something is wrong.",
            fix_hint="Do this to fix.",
        )
        assert f["severity"] == "error"
        assert f["category"] == "structural"
        assert f["location"] == "documents/datenschutz"
        assert f["description"] == "Something is wrong."
        assert f["fix"] == "Do this to fix."

    def test_warning_severity(self):
        f = utils.finding(utils.SEVERITY_WARNING, utils.CATEGORY_INDEX, "x", "y", "z")
        assert f["severity"] == "warning"


class TestIntegrityConstants:
    def test_severities(self):
        assert utils.SEVERITY_ERROR == "error"
        assert utils.SEVERITY_WARNING == "warning"

    def test_categories(self):
        assert utils.CATEGORY_STRUCTURAL == "structural"
        assert utils.CATEGORY_INDEX == "index"
        assert utils.CATEGORY_METADATA == "metadata"
        assert utils.CATEGORY_SEARCH == "search"
        assert utils.CATEGORY_WEB == "web"
        assert utils.CATEGORY_GUIDELINE == "guideline"


# ---------------------------------------------------------------------------
# Integrity check — structural checks
# ---------------------------------------------------------------------------


class TestCheckRequiredDirs:
    def test_all_present(self, tmp_path):
        for name in ("searches", "documents", "fulltext", "guidelines", "web"):
            (tmp_path / name).mkdir()
        findings = []
        utils.check_required_dirs(tmp_path, findings)
        assert findings == []

    def test_one_missing(self, tmp_path):
        for name in ("searches", "documents", "fulltext", "guidelines"):
            (tmp_path / name).mkdir()
        findings = []
        utils.check_required_dirs(tmp_path, findings)
        assert len(findings) == 1
        assert findings[0]["severity"] == "error"
        assert "web" in findings[0]["description"]

    def test_all_missing(self, tmp_path):
        findings = []
        utils.check_required_dirs(tmp_path, findings)
        assert len(findings) == 5


class TestCheckEmptyFiles:
    def test_no_empty_files(self, tmp_path):
        f = tmp_path / "ok.txt"
        f.write_text("content")
        findings = []
        utils.check_empty_files(tmp_path, findings)
        assert findings == []

    def test_one_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        findings = []
        utils.check_empty_files(tmp_path, findings)
        assert len(findings) == 1
        assert findings[0]["severity"] == "error"
        assert "zero bytes" in findings[0]["description"]

    def test_mixed(self, tmp_path):
        (tmp_path / "ok.txt").write_text("content")
        (tmp_path / "empty.txt").write_text("")
        findings = []
        utils.check_empty_files(tmp_path, findings)
        assert len(findings) == 1


# ---------------------------------------------------------------------------
# Integrity check — index validation
# ---------------------------------------------------------------------------


class TestCheckIndexValid:
    def test_missing_index(self, tmp_path):
        findings = []
        result = utils.check_index_valid(tmp_path, findings)
        assert result is None
        assert len(findings) == 1
        assert "missing" in findings[0]["description"]

    def test_valid_index(self, tmp_path):
        index = {
            "searches": [],
            "documents": [],
            "fulltext": [],
            "guidelines": [],
            "web": [],
        }
        (tmp_path / "index.json").write_text(json.dumps(index))
        findings = []
        result = utils.check_index_valid(tmp_path, findings)
        assert result == index
        assert findings == []

    def test_invalid_json(self, tmp_path):
        (tmp_path / "index.json").write_text("not {{{ json")
        findings = []
        result = utils.check_index_valid(tmp_path, findings)
        assert result is None
        assert len(findings) == 1
        assert "not valid JSON" in findings[0]["description"]

    def test_missing_required_keys(self, tmp_path):
        (tmp_path / "index.json").write_text(json.dumps({"searches": [], "documents": []}))
        findings = []
        result = utils.check_index_valid(tmp_path, findings)
        assert result is None
        assert any("fulltext" in f["description"] for f in findings)

    def test_extra_keys_warning(self, tmp_path):
        index = {
            "searches": [], "documents": [], "fulltext": [],
            "guidelines": [], "web": [], "extra_category": [],
        }
        (tmp_path / "index.json").write_text(json.dumps(index))
        findings = []
        result = utils.check_index_valid(tmp_path, findings)
        assert result is not None
        assert any("extra_category" in f["description"] for f in findings)

    def test_duplicate_paths_in_category(self, tmp_path):
        index = {
            "searches": [
                {"path": "searches/datenschutz/search-a.json"},
                {"path": "searches/datenschutz/search-a.json"},
            ],
            "documents": [],
            "fulltext": [],
            "guidelines": [],
            "web": [],
        }
        (tmp_path / "index.json").write_text(json.dumps(index))
        findings = []
        utils.check_index_valid(tmp_path, findings)
        duplicates = [f for f in findings if "Duplicate" in f["description"]]
        assert len(duplicates) == 1


# ---------------------------------------------------------------------------
# Integrity check — cross-reference
# ---------------------------------------------------------------------------


class TestCheckIndexCrossref:
    def test_all_in_sync(self, tmp_path):
        (tmp_path / "searches").mkdir()
        (tmp_path / "documents").mkdir()
        (tmp_path / "fulltext").mkdir()
        (tmp_path / "guidelines").mkdir()
        (tmp_path / "web").mkdir()
        data = {
            "searches": [], "documents": [], "fulltext": [],
            "guidelines": [], "web": [],
        }
        findings = []
        utils.check_index_crossref(tmp_path, data, findings)
        assert findings == []

    def test_indexed_but_missing_on_disk(self, tmp_path):
        for name in ("searches", "documents", "fulltext", "guidelines", "web"):
            (tmp_path / name).mkdir()
        data = {
            "searches": [{"path": "searches/ghost/search.json"}],
            "documents": [],
            "fulltext": [],
            "guidelines": [],
            "web": [],
        }
        findings = []
        utils.check_index_crossref(tmp_path, data, findings)
        missing = [f for f in findings if "not found on disk" in f["description"]]
        assert len(missing) == 1

    def test_on_disk_but_not_indexed(self, tmp_path):
        (tmp_path / "searches" / "topic").mkdir(parents=True)
        (tmp_path / "documents").mkdir()
        (tmp_path / "fulltext").mkdir()
        (tmp_path / "guidelines").mkdir()
        (tmp_path / "web").mkdir()
        (tmp_path / "searches" / "topic" / "search.json").write_text("{}")
        data = {
            "searches": [], "documents": [], "fulltext": [],
            "guidelines": [], "web": [],
        }
        findings = []
        utils.check_index_crossref(tmp_path, data, findings)
        extra = [f for f in findings if "not listed in index" in f["description"]]
        assert len(extra) == 1


# ---------------------------------------------------------------------------
# Integrity check — document integrity
# ---------------------------------------------------------------------------


class TestCheckDocumentIntegrity:
    def test_valid_document(self, tmp_path):
        (tmp_path / "documents" / "datenschutz").mkdir(parents=True)
        doc_dir = tmp_path / "documents" / "datenschutz" / "doc-test-title"
        doc_dir.mkdir()
        (doc_dir / "metadata.json").write_text('{"title": "Test", "source": "web"}')
        (doc_dir / "abstract.txt").write_text("Abstract content.")
        findings = []
        utils.check_document_integrity(tmp_path, findings)
        assert findings == []

    def test_missing_abstract_txt(self, tmp_path):
        (tmp_path / "documents" / "datenschutz").mkdir(parents=True)
        doc_dir = tmp_path / "documents" / "datenschutz" / "doc-test"
        doc_dir.mkdir()
        (doc_dir / "metadata.json").write_text('{"title": "Test"}')
        findings = []
        utils.check_document_integrity(tmp_path, findings)
        assert any("missing abstract.txt" in f["description"] for f in findings)

    def test_invalid_metadata_json(self, tmp_path):
        (tmp_path / "documents" / "datenschutz").mkdir(parents=True)
        doc_dir = tmp_path / "documents" / "datenschutz" / "doc-test"
        doc_dir.mkdir()
        (doc_dir / "metadata.json").write_text("garbage {{{")
        (doc_dir / "abstract.txt").write_text("ok")
        findings = []
        utils.check_document_integrity(tmp_path, findings)
        assert any("not valid JSON" in f["description"] for f in findings)

    def test_empty_abstract_content(self, tmp_path):
        (tmp_path / "documents" / "datenschutz").mkdir(parents=True)
        doc_dir = tmp_path / "documents" / "datenschutz" / "doc-test"
        doc_dir.mkdir()
        (doc_dir / "metadata.json").write_text('{"title": "Test"}')
        (doc_dir / "abstract.txt").write_text("   ")
        findings = []
        utils.check_document_integrity(tmp_path, findings)
        assert any("only whitespace" in f["description"] for f in findings)


# ---------------------------------------------------------------------------
# Integrity check — web files
# ---------------------------------------------------------------------------


class TestCheckWebFiles:
    def test_valid_html(self, tmp_path):
        (tmp_path / "web").mkdir()
        file_path = tmp_path / "web" / "page.html"
        file_path.write_text("<!doctype html>\n<html></html>")
        findings = []
        utils.check_web_files(tmp_path, findings)
        assert findings == []

    def test_empty_file(self, tmp_path):
        (tmp_path / "web").mkdir()
        file_path = tmp_path / "web" / "empty.html"
        file_path.write_text("")
        findings = []
        utils.check_web_files(tmp_path, findings)
        assert any("empty" in f["description"] for f in findings)

    def test_html_file_without_html_tag(self, tmp_path):
        (tmp_path / "web").mkdir()
        file_path = tmp_path / "web" / "page.html"
        file_path.write_text("Just some text, no html tag.")
        findings = []
        utils.check_web_files(tmp_path, findings)
        assert any("<html> tag" in f["description"] for f in findings)


# ---------------------------------------------------------------------------
# Integrity check — guideline integrity
# ---------------------------------------------------------------------------


class TestCheckGuidelineIntegrity:
    def test_valid_source_md(self, tmp_path):
        (tmp_path / "guidelines").mkdir()
        gdir = tmp_path / "guidelines" / "eu-gdpr"
        gdir.mkdir(parents=True)
        (gdir / "source.md").write_text("---\ntitle: Test\n---\n\n# Content")
        findings = []
        utils.check_guideline_integrity(tmp_path, findings)
        assert findings == []

    def test_empty_source_md(self, tmp_path):
        (tmp_path / "guidelines").mkdir()
        gdir = tmp_path / "guidelines" / "empty-guideline"
        gdir.mkdir(parents=True)
        (gdir / "source.md").write_text("")
        findings = []
        utils.check_guideline_integrity(tmp_path, findings)
        assert any("empty" in f["description"] for f in findings)

    def test_missing_frontmatter(self, tmp_path):
        (tmp_path / "guidelines").mkdir()
        gdir = tmp_path / "guidelines" / "bad-guideline"
        gdir.mkdir(parents=True)
        (gdir / "source.md").write_text("# No frontmatter here")
        findings = []
        utils.check_guideline_integrity(tmp_path, findings)
        assert any("missing YAML frontmatter" in f["description"] for f in findings)

    def test_multilingual_source_files(self, tmp_path):
        (tmp_path / "guidelines").mkdir()
        gdir = tmp_path / "guidelines" / "eu-law"
        gdir.mkdir(parents=True)
        (gdir / "source.de.md").write_text("---\ntitle: DE\n---\nContent")
        findings = []
        utils.check_guideline_integrity(tmp_path, findings)
        assert findings == []


# ---------------------------------------------------------------------------
# Integrity check — legacy dirs
# ---------------------------------------------------------------------------


class TestCheckLegacyDirs:
    def test_legacy_dirs_present(self, tmp_path):
        (tmp_path / "metadata").mkdir()
        (tmp_path / "abstracts").mkdir()
        (tmp_path / "papers").mkdir()
        findings = []
        utils.check_legacy_dirs(tmp_path, findings)
        assert len(findings) == 3
        assert all(f["severity"] == "warning" for f in findings)

    def test_no_legacy_dirs(self, tmp_path):
        findings = []
        utils.check_legacy_dirs(tmp_path, findings)
        assert findings == []


# ---------------------------------------------------------------------------
# Integrity check — orchestration
# ---------------------------------------------------------------------------


class TestRunIntegrityCheck:
    def test_missing_root(self, tmp_path):
        missing = tmp_path / "nonexistent"
        findings = utils.run_integrity_check(missing)
        assert len(findings) == 1
        assert findings[0]["severity"] == "error"
        assert "not found" in findings[0]["description"]

    def test_clean_archive(self, tmp_path):
        for name in ("searches", "documents", "fulltext", "guidelines", "web"):
            (tmp_path / name).mkdir()
        index = {
            "searches": [], "documents": [], "fulltext": [],
            "guidelines": [], "web": [],
        }
        (tmp_path / "index.json").write_text(json.dumps(index))
        findings = utils.run_integrity_check(tmp_path)
        assert findings == []


class TestVerifyAndReportIntegrity:
    def test_clean_returns_zero(self, tmp_path, capsys):
        for name in ("searches", "documents", "fulltext", "guidelines", "web"):
            (tmp_path / name).mkdir()
        index = {
            "searches": [], "documents": [], "fulltext": [],
            "guidelines": [], "web": [],
        }
        (tmp_path / "index.json").write_text(json.dumps(index))
        result = utils.verify_and_report_integrity(tmp_path)
        assert result == 0

    def test_errors_return_one(self, tmp_path, capsys):
        result = utils.verify_and_report_integrity(tmp_path)
        assert result == 1
        captured = capsys.readouterr()
        assert "FAILED" in captured.err
