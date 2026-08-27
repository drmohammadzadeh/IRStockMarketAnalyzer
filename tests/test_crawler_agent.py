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
