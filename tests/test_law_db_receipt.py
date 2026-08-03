"""Tests for law-db-receipt.py — tax document archival."""

import json
from pathlib import Path

import pytest

import law_db_receipt
import utils


class TestValidateReceiptSubtype:
    def test_valid_subtypes(self):
        for value in ("receipt", "medical_honorarium", "broker_statement",
                       "business_expense", "income_document", "salary_statement",
                       "bank_statement", "other"):
            assert law_db_receipt.validate_subtype(value) == value

    def test_invalid_subtype_raises(self):
        with pytest.raises(ValueError):
            law_db_receipt.validate_subtype("not_a_subtype")


class TestValidateTaxCategory:
    def test_valid_categories(self):
        for value in ("werbungskosten", "sonderausgaben", "aussergewoehnliche_belastung",
                       "einkuenfte_aus_kapitalvermoegen", "einkuenfte_aus_selbststaendiger_arbeit",
                       "einkuenfte_aus_nichtselbststaendiger_arbeit", "umsatzsteuer_vorsteuer",
                       "other"):
            assert law_db_receipt.validate_tax_category(value) == value

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError):
            law_db_receipt.validate_tax_category("not_a_category")


class TestUniqueFolderName:
    def test_no_conflict(self, tmp_path):
        result = law_db_receipt.unique_folder_name(tmp_path, "test-receipt")
        assert result == "test-receipt"

    def test_with_conflict(self, tmp_path):
        (tmp_path / "test-receipt").mkdir()
        result = law_db_receipt.unique_folder_name(tmp_path, "test-receipt")
        assert result == "test-receipt-2"

    def test_multiple_conflicts(self, tmp_path):
        (tmp_path / "test-receipt").mkdir()
        (tmp_path / "test-receipt-2").mkdir()
        (tmp_path / "test-receipt-3").mkdir()
        result = law_db_receipt.unique_folder_name(tmp_path, "test-receipt")
        assert result == "test-receipt-4"


class TestArchiveReceiptPdf:
    def test_pdf_extraction_and_metadata(self, tmp_path):
        receipt_dir = tmp_path / "receipt"
        receipt_dir.mkdir()
        metadata = {"has_pdf": False, "has_markdown": False, "has_csv": False}

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
            b"0000000058 00000 n \n0000000115 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n"
        )
        pdf_path.write_text(pdf_path.read_text())

        law_db_receipt.archive_receipt_pdf(pdf_path, receipt_dir, metadata)

        assert metadata["has_pdf"] is True
        assert (receipt_dir / "source.pdf").is_file()


class TestArchiveReceiptCsv:
    def test_csv_archival(self, tmp_path):
        receipt_dir = tmp_path / "receipt"
        receipt_dir.mkdir()
        metadata = {"has_pdf": False, "has_markdown": False, "has_csv": False}

        csv_path = tmp_path / "test.csv"
        csv_path.write_text("name,amount,date\nItem A,100,2025-01-15\nItem B,200,2025-02-20\n")

        law_db_receipt.archive_receipt_csv(csv_path, receipt_dir, metadata)

        assert metadata["has_csv"] is True
        assert (receipt_dir / "source.csv").is_file()
        assert metadata["csv_row_count"] == 2
        assert "name" in metadata["csv_columns"]

    def test_empty_csv(self, tmp_path):
        receipt_dir = tmp_path / "receipt"
        receipt_dir.mkdir()
        metadata = {"has_pdf": False, "has_markdown": False, "has_csv": False}

        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("col1,col2\n")

        law_db_receipt.archive_receipt_csv(csv_path, receipt_dir, metadata)

        assert metadata["has_csv"] is True
        assert metadata["csv_row_count"] == 0


class TestReceiptMetadata:
    def test_metadata_written(self, tmp_path):
        law_db_path = tmp_path / "law-db"
        receipts_dir = law_db_path / "receipts" / "werbungskosten" / "test"
        receipts_dir.mkdir(parents=True)
        receipt_dir = law_db_receipt.unique_folder_name(receipts_dir, "test-receipt")
        receipt_dir = receipts_dir / receipt_dir
        receipt_dir.mkdir()

        metadata = {
            "subtype": "receipt",
            "title": "Test Receipt",
            "tax_category": "werbungskosten",
            "payer": "Doctor Clinic",
            "payee": "John Doe",
            "amount": 150.00,
            "currency": "EUR",
            "document_date": "2025-06-15",
            "tax_period": "2025",
            "source_url": "",
            "access_date": "2025-06-20",
            "language": "de",
            "has_pdf": False,
            "has_markdown": False,
            "has_csv": False,
            "notes": "",
        }

        metadata_file = receipt_dir / "metadata.json"
        utils.atomic_write(metadata_file, json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

        saved = json.loads(metadata_file.read_text())
        assert saved["subtype"] == "receipt"
        assert saved["tax_category"] == "werbungskosten"
        assert saved["amount"] == 150.00
        assert saved["payer"] == "Doctor Clinic"

    def test_metadata_csv_columns(self, tmp_path):
        law_db_path = tmp_path / "law-db"
        receipts_dir = law_db_path / "receipts" / "einkuenfte_aus_kapitalvermoegen" / "flatex"
        receipts_dir.mkdir(parents=True)
        receipt_dir = receipts_dir / "dividende-2025"
        receipt_dir.mkdir()

        csv_path = tmp_path / "flatex.csv"
        csv_path.write_text("isin,name,shares,dividend,tax\nAT0000,ACME,100,5.50,1.51\n")

        metadata = {"has_pdf": False, "has_markdown": False, "has_csv": False}
        law_db_receipt.archive_receipt_csv(csv_path, receipt_dir, metadata)
        utils.atomic_write(
            receipt_dir / "metadata.json",
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        )

        saved = json.loads((receipt_dir / "metadata.json").read_text())
        assert saved["csv_columns"] == ["isin", "name", "shares", "dividend", "tax"]
        assert saved["csv_row_count"] == 1


class TestSyncIndexReceipts:
    def test_receipt_appears_in_index(self, tmp_path):
        law_db_path = tmp_path / "law-db"
        law_db_path.mkdir()
        for name in ("searches", "documents", "fulltext", "guidelines", "web", "contracts", "receipts"):
            (law_db_path / name).mkdir()

        receipt_dir = law_db_path / "receipts" / "werbungskosten" / "test" / "test-receipt"
        receipt_dir.mkdir(parents=True)

        metadata = {
            "subtype": "receipt",
            "title": "Test Receipt",
            "tax_category": "werbungskosten",
            "payer": "", "payee": "", "amount": 0, "currency": "EUR",
            "document_date": "", "tax_period": "", "source_url": "",
            "access_date": "2025-06-20", "language": "de",
            "has_pdf": False, "has_markdown": False, "has_csv": False, "notes": "",
        }
        (receipt_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        import law_db
        law_db.sync_index(law_db_path)

        index_data = json.loads((law_db_path / "index.json").read_text())
        receipt_paths = [entry["path"] for entry in index_data["receipts"]]
        assert any("test-receipt" in p for p in receipt_paths)
