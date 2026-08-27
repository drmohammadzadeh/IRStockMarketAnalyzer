import json
from pathlib import Path
import pytest
from src.agents.summarizer import SummarizerAgent


def test_summarizer_generates_summaries(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    codal_dir = symbol_dir / "codal_reports"
    news_dir = symbol_dir / "news"
    codal_dir.mkdir(parents=True)
    news_dir.mkdir(parents=True)

    letters = [
        {"Title": "گزارش فعالیت ماهانه دوره ۱ ماهه منتهی به ۱۴۰۳/۰۸/۳۰", "PublishDateTime": "1403/09/05", "Url": "http://codal.ir/1"},
        {"Title": "اطلاعات و صورت‌های مالی میاندوره‌ای دوره ۶ ماهه", "PublishDateTime": "1403/08/15", "Url": "http://codal.ir/2"},
        {"Title": "افشای اطلاعات بااهمیت - (تغییر در ترکیب هیئت مدیره - گروه ب)", "PublishDateTime": "1403/08/10", "Url": "http://codal.ir/3"}
    ]
    (codal_dir / "letters_index.json").write_text(json.dumps(letters, ensure_ascii=False), encoding="utf-8")

    news = [
        {"title": "رشد چشمگیر فروش شرکت", "source": "سنا", "date": "1403/08/21", "body": "فروش شرکت با افزایش ۳۰ درصدی نسبت به ماه قبل همراه شد."}
    ]
    (news_dir / "news_archive.json").write_text(json.dumps(news, ensure_ascii=False), encoding="utf-8")

    agent = SummarizerAgent()
    res = agent.run("زهلال", symbol_dir)

    assert res["success"] is True
    assert res["symbol"] == "زهلال"
    assert (codal_dir / "codal_summaries.md").exists()
    assert (news_dir / "news_summary.md").exists()

    codal_summary = (codal_dir / "codal_summaries.md").read_text(encoding="utf-8")
    assert "خلاصه نکات کلیدی گزارش‌های کدال" in codal_summary
    assert "گزارش‌های صورت‌های مالی و سودآوری" in codal_summary
    assert "گزارش‌های فعالیت ماهانه" in codal_summary
    assert "افشاها، مجامع و افزایش سرمایه" in codal_summary
    assert "اطلاعات و صورت‌های مالی میاندوره‌ای" in codal_summary

    news_summary = (news_dir / "news_summary.md").read_text(encoding="utf-8")
    assert "خلاصه و تحلیل اخبار" in news_summary
    assert "رشد چشمگیر فروش شرکت" in news_summary
    assert "سنا" in news_summary


def test_summarizer_handles_missing_and_corrupt_files(tmp_path):
    symbol_dir = tmp_path / "فولاد"
    codal_dir = symbol_dir / "codal_reports"
    news_dir = symbol_dir / "news"
    codal_dir.mkdir(parents=True)
    news_dir.mkdir(parents=True)

    # Write corrupt JSON to test exception handling
    (codal_dir / "letters_index.json").write_text("invalid json content", encoding="utf-8")
    (news_dir / "news_archive.json").write_text("{broken json", encoding="utf-8")

    agent = SummarizerAgent()
    res = agent.run("فولاد", symbol_dir)

    assert res["success"] is True
    assert (codal_dir / "codal_summaries.md").exists()
    assert (news_dir / "news_summary.md").exists()

    codal_summary = (codal_dir / "codal_summaries.md").read_text(encoding="utf-8")
    assert "در بازه اخیر، صورت مالی جدید منتشر نشده است" in codal_summary
    assert "گزارش ماهانه جدیدی در ۳۰ روز اخیر ثبت نشده است" in codal_summary

    news_summary = (news_dir / "news_summary.md").read_text(encoding="utf-8")
    assert "خبر منفی یا شوک خبری بااهمیتی در رسانه‌های رسمی" in news_summary


def test_summarizer_handles_nonexistent_directories(tmp_path):
    symbol_dir = tmp_path / "شستا"
    # Directories not created beforehand

    agent = SummarizerAgent()
    res = agent.run("شستا", symbol_dir)

    assert res["success"] is True
    assert (symbol_dir / "codal_reports" / "codal_summaries.md").exists()
    assert (symbol_dir / "news" / "news_summary.md").exists()


def test_summarize_codal_letters_categories():
    agent = SummarizerAgent()
    letters = [
        {"Title": "صورتهای مالی سالانه منتهی به ۱۴۰۲/۱۲/۲۹", "PublishDateTime": "1403/04/10"},
        {"Title": "گزارش فعالیت ماهانه ۱ ماهه منتهی به ۱۴۰۳/۰۵/۳۱", "PublishDateTime": "1403/06/05"},
        {"Title": "آگهی دعوت به مجمع عمومی عادی سالیانه", "PublishDateTime": "1403/04/15"}
    ]
    summary = agent.summarize_codal_letters(letters, "خودرو")
    assert "نماد خودرو" in summary
    assert "صورتهای مالی سالانه" in summary
    assert "فعالیت ماهانه ۱ ماهه" in summary
    assert "آگهی دعوت به مجمع عمومی عادی سالیانه" in summary


def test_summarize_news_empty_and_filled():
    agent = SummarizerAgent()
    empty_summary = agent.summarize_news([], "شپنا")
    assert "**تعداد اخبار پایش‌شده:** 0 خبر" in empty_summary

    filled_summary = agent.summarize_news([
        {"title": "قرارداد جدید پالایشگاه", "source": "بورس نیوز", "date": "1403/07/01", "body": "قرارداد صادراتی منعقد گردید."}
    ], "شپنا")
    assert "قرارداد جدید پالایشگاه" in filled_summary
    assert "بورس نیوز" in filled_summary
