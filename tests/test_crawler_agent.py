import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from src.agents.crawler import CrawlerAgent


def test_crawler_creates_expected_directories_and_files(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir()

    crawler = CrawlerAgent()
    with patch.object(crawler, "_fetch_codal_letters", return_value=[{"Title": "گزارش ۶ ماهه", "TracingNo": 123, "PublishDateTime": "1403/08/15", "Url": "http://example.com"}]), \
         patch.object(crawler, "_download_letter_content", return_value="<html>گزارش مالی</html>"), \
         patch.object(crawler, "_fetch_news", return_value=[{"title": "رشد سود زهلال", "source": "سنا", "date": "1403/08/16", "url": "http://sena.ir", "body": "سود سهم رشد کرد"}]), \
         patch.object(crawler, "_fetch_market_data", return_value=(pd.DataFrame([{"date": "1403-08-15", "close": 4500, "volume": 1000}]), {"buy_real_count": 100})):

        res = crawler.run("زهلال", symbol_dir)
        assert res["success"] is True
        assert res["symbol"] == "زهلال"
        assert res["codal_count"] == 1
        assert res["codal_downloaded"] == 1
        assert res["news_count"] == 1
        assert res["has_market_history"] is True

        assert (symbol_dir / "codal_reports" / "letters_index.json").exists()
        assert (symbol_dir / "news" / "news_archive.json").exists()
        assert (symbol_dir / "market_data" / "trade_history.csv").exists()
        assert (symbol_dir / "market_data" / "orderbook_tape.json").exists()

        # Check downloaded html letter
        html_files = list((symbol_dir / "codal_reports").glob("*.html"))
        assert len(html_files) == 1
        assert "گزارش مالی" in html_files[0].read_text(encoding="utf-8")


def test_crawler_handles_empty_market_data(tmp_path):
    symbol_dir = tmp_path / "خپارس"
    symbol_dir.mkdir()

    crawler = CrawlerAgent()
    with patch.object(crawler, "_fetch_codal_letters", return_value=[]), \
         patch.object(crawler, "_fetch_news", return_value=[]), \
         patch.object(crawler, "_fetch_market_data", return_value=(pd.DataFrame(), {})):

        res = crawler.run("خپارس", symbol_dir)
        assert res["success"] is True
        assert res["has_market_history"] is False

        csv_file = symbol_dir / "market_data" / "trade_history.csv"
        assert csv_file.exists()
        content = csv_file.read_text(encoding="utf-8")
        assert "date,open,high,low,close,volume" in content


def test_crawler_fetch_codal_letters_delegates_to_codal_fetcher(tmp_path):
    symbol_dir = tmp_path / "فولاد"
    symbol_dir.mkdir()
    links_file = symbol_dir / "links.txt"
    links_file.write_text("https://codal.ir/ReportList.aspx?Symbol=فولاد", encoding="utf-8")

    crawler = CrawlerAgent()
    mock_codal = MagicMock()
    mock_codal.fetch_codal_reports.return_value = {
        "raw_letters": [{"Title": "اطلاعیه آزمایشی", "Url": "http://codal.ir/1"}]
    }
    crawler.codal = mock_codal

    letters = crawler._fetch_codal_letters("فولاد", symbol_dir)
    assert len(letters) == 1
    assert letters[0]["Title"] == "اطلاعیه آزمایشی"
    mock_codal.fetch_codal_reports.assert_called_once_with("فولاد", links_file)


def test_crawler_download_letter_content():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html>محتوای گزارش</html>"
    mock_client.get.return_value = mock_resp

    crawler = CrawlerAgent(client=mock_client)
    content = crawler._download_letter_content("http://codal.ir/report")
    assert content == "<html>محتوای گزارش</html>"

    # Empty url
    assert crawler._download_letter_content("") == ""

    # Exception handling
    mock_client.get.side_effect = Exception("Connection error")
    assert crawler._download_letter_content("http://codal.ir/fail") == ""


def test_crawler_fetch_news_fallback():
    mock_client = MagicMock()
    mock_client.get.side_effect = Exception("Network down")

    crawler = CrawlerAgent(client=mock_client)
    news = crawler._fetch_news("زهلال")
    assert len(news) >= 1
    assert "زهلال" in news[0]["title"]


def test_crawler_fetch_market_data():
    crawler = CrawlerAgent()
    mock_tsetmc = MagicMock()
    df = pd.DataFrame([{"date": "1403-01-01", "close": 1000}])
    client_dict = {"buyer_power": 1.5}
    mock_tsetmc.fetch_symbol_data.return_value = {
        "history": df,
        "client_type": client_dict
    }
    crawler.tsetmc = mock_tsetmc

    history, client_data = crawler._fetch_market_data("زهلال")
    assert not history.empty
    assert client_data["buyer_power"] == 1.5
    mock_tsetmc.fetch_symbol_data.assert_called_once_with("زهلال")


def test_crawler_recursive_depth_and_file_cap(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    symbol_dir.mkdir(parents=True)
    links_file = symbol_dir / "links.txt"
    links_file.write_text("https://www.bourse24.ir/news/tag/وتجارت\n", encoding="utf-8")

    mock_client = MagicMock()

    # Level 1 page with 60 child news links
    child_links_html = "".join([f'<a href="/news/{i}">خبر شماره {i} وتجارت</a>\n' for i in range(1, 65)])
    level1_html = f"<html><head><title>اخبار وتجارت</title></head><body>{child_links_html}</body></html>"

    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        url_str = str(url)
        if "bourse24.ir/news/tag" in url_str:
            resp.text = level1_html
            resp.content = level1_html.encode("utf-8")
        elif "/news/" in url_str:
            resp.text = "<html><body><p>متن خبر تفصیلی بانک تجارت و رویدادهای مالی اخیر این بانک.</p></body></html>"
            resp.content = resp.text.encode("utf-8")
        elif "search.codal.ir" in url_str:
            resp.json.return_value = {
                "Letters": [{"Title": f"گزارش {i}", "TracingNo": 1000 + i, "LetterSerial": 2000 + i, "Url": f"Decision.aspx?LetterSerial={2000+i}"} for i in range(1, 25)]
            }
            resp.text = json.dumps(resp.json.return_value)
            resp.content = resp.text.encode("utf-8")
        elif "DownloadFile.aspx" in url_str or ".pdf" in url_str:
            resp.content = b"%PDF-1.4 sample codal pdf content"
            resp.text = "%PDF-1.4 sample codal pdf content"
        elif "excel.codal.ir" in url_str or ".xls" in url_str or ".xlsx" in url_str:
            resp.content = b"PK\x03\x04 sample excel content"
            resp.text = "sample excel"
        else:
            resp.text = "<html><p>محتوای گزارش کدال</p></body></html>"
            resp.content = resp.text.encode("utf-8")
        return resp

    mock_client.get.side_effect = mock_get

    crawler = CrawlerAgent(client=mock_client)
    res = crawler.run("وتجارت", symbol_dir)

    assert res["success"] is True
    assert "total_downloaded_files" in res
    assert res["total_downloaded_files"] <= 50


def test_crawler_guarantees_pdf_xlsx_reports_quota(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    symbol_dir.mkdir(parents=True)

    mock_client = MagicMock()
    letters_data = [
        {
            "Title": f"صورت‌های مالی دوره {i}",
            "TracingNo": 10000 + i,
            "LetterSerial": 50000 + i,
            "PublishDateTime": f"1403/0{i%9+1}/15",
            "Url": f"Decision.aspx?LetterSerial={50000+i}",
            "PdfUrl": f"https://codal.ir/Reports/DownloadFile.aspx?LetterSerial={50000+i}&type=pdf",
            "ExcelUrl": f"https://excel.codal.ir/service/Excel/GetAll/{50000+i}",
        }
        for i in range(1, 26)
    ]

    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        url_str = str(url)
        if "search.codal.ir" in url_str:
            resp.json.return_value = {"Letters": letters_data}
            resp.text = json.dumps(resp.json.return_value)
            resp.content = resp.text.encode("utf-8")
        elif "DownloadFile.aspx" in url_str or ".pdf" in url_str:
            resp.content = b"%PDF-1.4 binary pdf content"
            resp.text = "%PDF-1.4 binary pdf content"
        elif "excel.codal.ir" in url_str or ".xlsx" in url_str or ".xls" in url_str:
            resp.content = b"PK\x03\x04 binary excel content"
            resp.text = "binary excel"
        else:
            resp.text = "<html><body>گزارش مالی</body></html>"
            resp.content = resp.text.encode("utf-8")
        return resp

    mock_client.get.side_effect = mock_get

    crawler = CrawlerAgent(client=mock_client)
    res = crawler.run("وتجارت", symbol_dir)

    assert res["success"] is True
    assert res["pdf_xlsx_count"] >= 20
    assert res["total_downloaded_files"] <= 50

    codal_reports = list((symbol_dir / "codal_reports").iterdir())
    pdf_xlsx_files = [f for f in codal_reports if f.suffix.lower() in (".pdf", ".xlsx", ".xls")]
    assert len(pdf_xlsx_files) >= 20


def test_codal_fetcher_extracts_pdf_and_excel_urls():
    from src.data.codal_fetcher import CodalFetcher
    letter1 = {
        "LetterSerial": 12345,
        "PdfUrl": "/Reports/DownloadFile.aspx?LetterSerial=12345&type=pdf",
        "ExcelUrl": "https://excel.codal.ir/service/Excel/GetAll/12345",
        "Url": "/Reports/Decision.aspx?LetterSerial=12345",
    }
    pdf_url = CodalFetcher.get_pdf_url(letter1)
    excel_url = CodalFetcher.get_excel_url(letter1)
    html_url = CodalFetcher.get_html_url(letter1)

    assert "DownloadFile.aspx" in pdf_url
    assert "excel.codal.ir" in excel_url
    assert "Decision.aspx" in html_url

    letter2 = {
        "Url": "/Reports/Decision.aspx?LetterSerial=67890",
    }
    pdf_url2 = CodalFetcher.get_pdf_url(letter2)
    excel_url2 = CodalFetcher.get_excel_url(letter2)
    assert "LetterSerial=67890" in pdf_url2
    assert "67890" in excel_url2


def test_crawler_downloads_third_party_documents_depth_2(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    symbol_dir.mkdir(parents=True)
    links_file = symbol_dir / "links.txt"
    links_file.write_text("https://rahavard365.com/asset/461\n", encoding="utf-8")

    mock_client = MagicMock()

    portal_html = """
    <html>
      <head><title>بانک تجارت در رهآورد</title></head>
      <body>
        <a href="https://cdn.rahavard365.com/reports/vtejarat_quarterly.pdf">دانلود گزارش فصلی PDF</a>
        <a href="https://cdn.rahavard365.com/financials/balance_sheet.xlsx">دانلود صورت مالی اکسل</a>
        <a href="/news/88899">خبر افزایش سرمایه وتجارت</a>
      </body>
    </html>
    """
    news_html = "<html><head><title>خبر افزایش سرمایه</title></head><body><p>بانک تجارت قصد افزایش سرمایه دارد.</p></body></html>"

    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        url_str = str(url)
        if "rahavard365.com/asset" in url_str:
            resp.text = portal_html
            resp.content = portal_html.encode("utf-8")
        elif "vtejarat_quarterly.pdf" in url_str:
            resp.content = b"%PDF-1.4 sample pdf document"
            resp.text = "%PDF-1.4 sample pdf document"
        elif "balance_sheet.xlsx" in url_str:
            resp.content = b"PK\x03\x04 sample excel sheet"
            resp.text = "sample excel"
        elif "/news/88899" in url_str:
            resp.text = news_html
            resp.content = news_html.encode("utf-8")
        elif "search.codal.ir" in url_str:
            resp.json.return_value = {"Letters": []}
            resp.text = json.dumps({"Letters": []})
            resp.content = resp.text.encode("utf-8")
        else:
            resp.text = "<html><body>داده</body></html>"
            resp.content = resp.text.encode("utf-8")
        return resp

    mock_client.get.side_effect = mock_get

    crawler = CrawlerAgent(client=mock_client)
    res = crawler.run("وتجارت", symbol_dir)

    assert res["success"] is True
    codal_reports = list((symbol_dir / "codal_reports").iterdir())
    news_files = list((symbol_dir / "news").glob("*.html"))

    assert any(f.suffix == ".pdf" for f in codal_reports)
    assert any(f.suffix == ".xlsx" for f in codal_reports)
    assert len(news_files) >= 1


