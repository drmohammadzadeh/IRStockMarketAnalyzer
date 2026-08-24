import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.data.codal_fetcher import CodalFetcher


def test_extract_symbol_from_links(tmp_path):
    links_file = tmp_path / "links.txt"
    links_file.write_text("https://codal.ir/ReportList.aspx?search&Symbol=%D8%B2%D9%87%D9%84%D8%A7%D9%84", encoding="utf-8")
    extracted = CodalFetcher.extract_symbol_from_file(links_file)
    assert extracted == "زهلال"


def test_extract_symbol_from_file_non_existent():
    non_existent = Path("non_existent_links.txt")
    assert CodalFetcher.extract_symbol_from_file(non_existent) is None


def test_extract_symbol_from_file_no_symbol(tmp_path):
    links_file = tmp_path / "links.txt"
    links_file.write_text("https://codal.ir/ReportList.aspx?search", encoding="utf-8")
    assert CodalFetcher.extract_symbol_from_file(links_file) is None


def test_parse_letter_types():
    raw_letters = [
        {"Title": "اطلاعات و صورت‌های مالی میاندوره‌ای دوره ۶ ماهه منتهی به ۱۴۰۳/۰۶/۳۱ (حسابرسی شده)", "TracingNo": 12345, "PublishDateTime": "1403/08/15 10:00:00", "Url": "http://codal.ir/Reports/Decision.aspx?LetterSerial=123"},
        {"Title": "صورتهای مالی سالانه منتهی به ۱۴۰۲/۱۲/۲۹", "TracingNo": 12346},
        {"Title": "گزارش فعالیت ماهانه ۱ ماهه منتهی به ۱۴۰۳/۰۹/۳۰", "TracingNo": 12347, "PublishDateTime": "1403/10/05 11:00:00", "Url": "http://codal.ir/Reports/Decision.aspx?LetterSerial=124"},
        {"Title": "افشای اطلاعات بااهمیت - (دریافت مجوز تغییر بیش از ۱۰ درصد در نرخ فروش محصولات)", "TracingNo": 12348},
        {"Title": "شفاف‌سازی در خصوص شایعه، خبر یا گزارش منتشر شده", "TracingNo": 12349},
        {"Title": "تصمیمات مجمع عمومی عادی سالیانه صاحبان سهام برای سال مالی منتهی به ۱۴۰۲/۱۲/۲۹", "TracingNo": 12350},
        {"Title": "پیشنهاد هیئت مدیره به مجمع عمومی فوق‌العاده در خصوص افزایش سرمایه", "TracingNo": 12351},
        {"Title": "آگهی دعوت به مجمع عمومی عادی به طور فوق‌العاده", "TracingNo": 12352},
        {"Title": "سایر اطلاعیه‌ها و پیام‌های ناظر", "TracingNo": 12353}
    ]
    categorized = CodalFetcher.categorize_letters(raw_letters)
    assert len(categorized["financial_statements"]) == 2
    assert len(categorized["monthly_reports"]) == 1
    assert len(categorized["material_disclosures"]) == 2
    assert len(categorized["assemblies"]) == 2
    assert len(categorized["capital_increases"]) == 1
    assert len(categorized["others"]) == 1


def test_fetch_codal_reports_success(tmp_path):
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "Letters": [
            {"Title": "صورت‌های مالی میاندوره‌ای ۶ ماهه", "TracingNo": 111},
            {"Title": "گزارش فعالیت ماهانه ۱ ماهه", "TracingNo": 222}
        ]
    }
    mock_client.get.return_value = mock_resp

    links_file = tmp_path / "links.txt"
    links_file.write_text("https://codal.ir/ReportList.aspx?search&Symbol=%D8%B2%D9%87%D9%84%D8%A7%D9%84", encoding="utf-8")

    fetcher = CodalFetcher(client=mock_client)
    res = fetcher.fetch_codal_reports("dummy", links_file=links_file)

    assert res["success"] is True
    assert res["symbol"] == "زهلال"
    assert res["letters_count"] == 2
    assert len(res["categorized"]["financial_statements"]) == 1
    assert len(res["categorized"]["monthly_reports"]) == 1


def test_fetch_codal_reports_api_error():
    mock_client = MagicMock()
    mock_client.get.side_effect = Exception("Connection error")

    fetcher = CodalFetcher(client=mock_client)
    res = fetcher.fetch_codal_reports("زهلال")

    assert res["success"] is False
    assert "error" in res
    assert res["symbol"] == "زهلال"
    assert res["categorized"]["financial_statements"] == []


def test_fetch_codal_reports_non_200():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_client.get.return_value = mock_resp

    fetcher = CodalFetcher(client=mock_client)
    res = fetcher.fetch_codal_reports("زهلال")

    assert res["success"] is True
    assert res["letters_count"] == 0
    assert res["symbol"] == "زهلال"
