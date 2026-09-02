"""Tests for Magic Bytes Validation and Corrupted File Prevention.

Author: alimohammadzadeh@ut.ac.ir
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.data.codal_fetcher import CodalFetcher, clean_corrupted_codal_reports
from src.agents.crawler import CrawlerAgent


def test_validate_file_magic_bytes_pdf():
    # Valid PDF headers
    assert CodalFetcher.validate_file_magic_bytes(b"%PDF-1.4\nrest of file", "report.pdf") is True
    assert CodalFetcher.validate_file_magic_bytes(b"%PDF-1.7\nrest of file", "statement.PDF") is True

    # Invalid PDF content (HTML error pages or random text)
    assert CodalFetcher.validate_file_magic_bytes(b"<!DOCTYPE html><html>", "report.pdf") is False
    assert CodalFetcher.validate_file_magic_bytes(b"\r\n<html xmlns:v=", "report.pdf") is False
    assert CodalFetcher.validate_file_magic_bytes(b"Error 404 Not Found", "report.pdf") is False
    assert CodalFetcher.validate_file_magic_bytes(b"%PD", "report.pdf") is False
    assert CodalFetcher.validate_file_magic_bytes(b"", "report.pdf") is False


def test_validate_file_magic_bytes_xlsx():
    # Valid XLSX zip header
    assert CodalFetcher.validate_file_magic_bytes(b"PK\x03\x04\x14\x00\x06\x00", "financials.xlsx") is True
    assert CodalFetcher.validate_file_magic_bytes(b"PK\x03\x04\x14\x00\x06\x00", "financials.XLSX") is True

    # Invalid XLSX content
    assert CodalFetcher.validate_file_magic_bytes(b"<!doctype html><html>", "financials.xlsx") is False
    assert CodalFetcher.validate_file_magic_bytes(b"\r\n<html><body>", "financials.xlsx") is False
    assert CodalFetcher.validate_file_magic_bytes(b"PK\x01\x02", "financials.xlsx") is False
    assert CodalFetcher.validate_file_magic_bytes(b"", "financials.xlsx") is False


def test_validate_file_magic_bytes_xls():
    # Valid legacy XLS OLE header
    assert CodalFetcher.validate_file_magic_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "old_sheet.xls") is True

    # Invalid XLS content
    assert CodalFetcher.validate_file_magic_bytes(b"<html><body>Error</body></html>", "old_sheet.xls") is False
    assert CodalFetcher.validate_file_magic_bytes(b"short", "old_sheet.xls") is False


def test_validate_file_magic_bytes_other_extensions():
    # Non-binary or other extensions
    assert CodalFetcher.validate_file_magic_bytes(b"<html><body>ok</body></html>", "report.html") is True
    assert CodalFetcher.validate_file_magic_bytes('{"symbol": "فولاد"}'.encode("utf-8"), "data.json") is True
    assert CodalFetcher.validate_file_magic_bytes(b"some text", "notes.txt") is True

    # Too short or empty content
    assert CodalFetcher.validate_file_magic_bytes(b"abc", "notes.txt") is False
    assert CodalFetcher.validate_file_magic_bytes(b"", "notes.txt") is False


def test_codal_fetcher_download_file_with_fallbacks(tmp_path):
    mock_client = MagicMock()
    fetcher = CodalFetcher(client=mock_client)

    primary_url = "https://codal.ir/Reports/DownloadFile.aspx?LetterSerial=123&type=pdf"
    fallback_url = "https://codal.ir/Reports/DownloadFile.aspx?id=999&type=pdf"
    target_file = tmp_path / "report.pdf"

    # Scenario: Primary returns HTML error page, fallback returns valid PDF
    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        url_str = str(url)
        if url_str == primary_url:
            resp.content = b"<!DOCTYPE html><html><body>Error 500</body></html>"
            resp.text = "<!DOCTYPE html><html><body>Error 500</body></html>"
            resp.headers = {"content-type": "text/html"}
        elif url_str == fallback_url:
            resp.content = b"%PDF-1.4 valid binary stream data"
            resp.text = "%PDF-1.4 valid binary stream data"
            resp.headers = {"content-type": "application/pdf"}
        else:
            resp.content = b""
            resp.text = ""
        return resp

    mock_client.get.side_effect = mock_get

    success, content, c_type = fetcher.download_file(
        url=primary_url,
        target_path=target_file,
        fallback_urls=[fallback_url],
    )

    assert success is True
    assert content.startswith(b"%PDF-1.4")
    assert c_type == "pdf"
    assert target_file.exists()
    assert target_file.read_bytes().startswith(b"%PDF-1.4")


def test_codal_fetcher_download_file_all_invalid_no_corrupt_file(tmp_path):
    mock_client = MagicMock()
    fetcher = CodalFetcher(client=mock_client)

    primary_url = "https://codal.ir/Reports/DownloadFile.aspx?LetterSerial=123&type=pdf"
    fallback_url = "https://codal.ir/Reports/DownloadFile.aspx?id=999&type=pdf"
    target_file = tmp_path / "corrupt_report.pdf"

    # Both return HTML error
    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\r\n<!doctype html><html><body>Access Denied</body></html>"
        resp.text = "\r\n<!doctype html><html><body>Access Denied</body></html>"
        resp.headers = {"content-type": "text/html"}
        return resp

    mock_client.get.side_effect = mock_get

    success, content, c_type = fetcher.download_file(
        url=primary_url,
        target_path=target_file,
        fallback_urls=[fallback_url],
    )

    assert success is False
    # Corrupted PDF must NOT be written to disk
    assert not target_file.exists()


def test_crawler_prevents_saving_html_as_pdf_or_xlsx(tmp_path):
    symbol_dir = tmp_path / "شتران"
    symbol_dir.mkdir(parents=True)

    mock_client = MagicMock()
    letters_data = [
        {
            "Title": "گزارش ۶ ماهه شتران",
            "TracingNo": 8881,
            "LetterSerial": 7771,
            "PublishDateTime": "1403/07/01",
            "Url": "Decision.aspx?LetterSerial=7771",
            "PdfUrl": "https://codal.ir/Reports/DownloadFile.aspx?LetterSerial=7771&type=pdf",
            "ExcelUrl": "https://excel.codal.ir/service/Excel/GetAll/7771",
        }
    ]

    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        url_str = str(url)
        if "search.codal.ir" in url_str:
            resp.json.return_value = {"Letters": letters_data}
            resp.text = json.dumps({"Letters": letters_data})
            resp.content = resp.text.encode("utf-8")
        elif "DownloadFile.aspx" in url_str or ".pdf" in url_str:
            # Codal returns HTML error page instead of PDF
            html_err = "\r\n<!doctype html><html><head><title>خطا در سامانه کدال</title></head></html>"
            resp.content = html_err.encode("utf-8")
            resp.text = html_err
            resp.headers = {"content-type": "text/html"}
        elif "excel.codal.ir" in url_str or ".xlsx" in url_str:
            # Codal returns HTML redirect instead of Excel
            html_err = "\r\n<html xmlns:v=\"urn:schemas-microsoft-com:vml\"><body>Redirect</body></html>"
            resp.content = html_err.encode("utf-8")
            resp.text = html_err
            resp.headers = {"content-type": "text/html"}
        else:
            resp.text = "<html><body>اطلاعیه متن</body></html>"
            resp.content = resp.text.encode("utf-8")
            resp.headers = {"content-type": "text/html"}
        return resp

    mock_client.get.side_effect = mock_get

    crawler = CrawlerAgent(client=mock_client)
    res = crawler.run("شتران", symbol_dir)

    assert res["success"] is True
    codal_reports = list((symbol_dir / "codal_reports").iterdir())

    # Check that NO file with .pdf or .xlsx contains HTML tags or fails magic bytes
    for f in codal_reports:
        if f.suffix.lower() in (".pdf", ".xlsx", ".xls"):
            content = f.read_bytes()
            assert CodalFetcher.validate_file_magic_bytes(content, f.name), (
                f"Corrupted file {f.name} contains invalid magic bytes: {content[:30]}"
            )


def test_cleanup_corrupted_codal_reports(tmp_path):
    # Setup simulated سهام structure
    stock1_dir = tmp_path / "سهام" / "فولاد" / "codal_reports"
    stock2_dir = tmp_path / "سهام" / "شتران" / "codal_reports"
    stock1_dir.mkdir(parents=True)
    stock2_dir.mkdir(parents=True)

    # 1. Corrupted PDF starting with \r\n<!doctype
    corrupt1 = stock1_dir / "1_گزارش.pdf"
    corrupt1.write_bytes(b"\r\n<!doctype html><html><body>Error</body></html>")

    # 2. Corrupted XLSX starting with \r\n<html
    corrupt2 = stock1_dir / "2_صورت_مالی.xlsx"
    corrupt2.write_bytes(b"\r\n<html xmlns:v=\"urn\"><body>Redirect</body></html>")

    # 3. Valid PDF
    valid_pdf = stock2_dir / "3_گزارش_معتبر.pdf"
    valid_pdf.write_bytes(b"%PDF-1.4\n\x00\x01\x02valid pdf binary")

    # 4. Valid XLSX
    valid_xlsx = stock2_dir / "4_اکسل_معتبر.xlsx"
    valid_xlsx.write_bytes(b"PK\x03\x04\x14\x00\x06\x00valid xlsx zip")

    # 5. Normal HTML
    normal_html = stock2_dir / "5_اطلاعیه.html"
    normal_html.write_text("<!DOCTYPE html><html><body>Normal</body></html>", encoding="utf-8")

    cleaned_files = clean_corrupted_codal_reports(tmp_path / "سهام")

    # Corrupt files must have been cleaned
    assert corrupt1 in cleaned_files
    assert corrupt2 in cleaned_files
    assert not corrupt1.exists()
    assert not corrupt2.exists()

    # Valid files must NOT be deleted
    assert valid_pdf.exists()
    assert valid_xlsx.exists()
    assert normal_html.exists()
