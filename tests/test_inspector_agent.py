import pytest
import json
from pathlib import Path
from src.agents.inspector import QualityInspector, InspectionResult
from src.agents import QualityInspector as QualityInspectorExport, InspectionResult as InspectionResultExport


def test_exports_in_init():
    assert QualityInspectorExport is QualityInspector
    assert InspectionResultExport is InspectionResult


def test_inspector_passes_healthy_crawler_stage(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)

    (symbol_dir / "codal_reports" / "letters_index.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "news" / "news_archive.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "market_data" / "trade_history.csv").write_text("date,close\n2026-01-01,1000", encoding="utf-8")
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text("{}", encoding="utf-8")

    inspector = QualityInspector()
    res = inspector.inspect_stage("crawler", symbol_dir)
    assert isinstance(res, InspectionResult)
    assert res.is_passed is True
    assert res.score >= 8.0
    assert len(res.defects) == 0
    assert "تأیید" in res.feedback or "Passed" in res.feedback or "موفقیت" in res.feedback


def test_inspector_fails_missing_files(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir()
    inspector = QualityInspector()
    res = inspector.inspect_stage("crawler", symbol_dir)
    assert isinstance(res, InspectionResult)
    assert res.is_passed is False
    assert res.score < 8.0
    assert len(res.defects) > 0
    assert "Defects found" in res.feedback or "نقص" in res.feedback


def test_inspector_crawler_corrupted_json_and_empty_csv(tmp_path):
    symbol_dir = tmp_path / "فولاد"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)

    (symbol_dir / "codal_reports" / "letters_index.json").write_text("{invalid json", encoding="utf-8")
    (symbol_dir / "news" / "news_archive.json").write_text("[{\"title\": \"test\"}]", encoding="utf-8")
    (symbol_dir / "market_data" / "trade_history.csv").write_text("", encoding="utf-8")  # empty
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text("invalid json", encoding="utf-8")

    inspector = QualityInspector()
    res = inspector.inspect_crawler(symbol_dir)
    assert res.is_passed is False
    assert res.score < 8.0
    assert any("letters_index.json" in d for d in res.defects)
    assert any("trade_history.csv" in d for d in res.defects)
    assert any("orderbook_tape.json" in d for d in res.defects)


def test_inspector_passes_healthy_summarizer_stage(tmp_path):
    symbol_dir = tmp_path / "شپنا"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)

    codal_content = (
        "# خلاصه نکات کلیدی گزارش‌های کدال نماد شپنا\n"
        "## ۱. گزارش‌های صورت‌های مالی و سودآوری\n"
        "اطلاعیه صورت مالی با سود عملیاتی مناسب منتشر شد و روند سودآوری افزایشی است.\n"
        "## ۲. فعالیت ماهانه\n"
        "تولید و فروش شرکت در سطح مطلوبی قرار دارد و نرخ فروش باثبات است.\n"
    )
    news_content = (
        "# خلاصه و تحلیل اخبار و تحولات نماد شپنا\n"
        "## ۱. سرخط مهم‌ترین اخبار و رویدادها\n"
        "طرح توسعه پالایشگاه به بهره‌برداری رسیده و اثرات مثبتی بر جریان درآمدی دارد.\n"
        "## ۲. جمع‌بندی ریسک‌ها و فرصت‌ها\n"
        "فرصت صادرات فرآورده‌های ویژه و ریسک نوسان کرک اسپرد بررسی شده است.\n"
    )

    (symbol_dir / "codal_reports" / "codal_summaries.md").write_text(codal_content, encoding="utf-8")
    (symbol_dir / "news" / "news_summary.md").write_text(news_content, encoding="utf-8")

    inspector = QualityInspector()
    res = inspector.inspect_summarizer(symbol_dir)
    assert res.is_passed is True
    assert res.score >= 8.0
    assert len(res.defects) == 0


def test_inspector_fails_summarizer_stage_short_or_missing(tmp_path):
    symbol_dir = tmp_path / "شپنا"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)

    # Very short file (< 100 bytes) and no headers
    (symbol_dir / "codal_reports" / "codal_summaries.md").write_text("کوتاه", encoding="utf-8")
    # Missing news_summary.md

    inspector = QualityInspector()
    res = inspector.inspect_stage("summarizer", symbol_dir)
    assert res.is_passed is False
    assert res.score < 8.0
    assert len(res.defects) >= 2


def test_inspector_passes_healthy_analysts_stage(tmp_path):
    symbol_dir = tmp_path / "فملی"
    (symbol_dir / "charts").mkdir(parents=True)

    tech_content = (
        "# گزارش تحلیل تکنیکال و تابلوخوانی پیشرفته نماد فملی\n"
        "## وضعیت اندیکاتورها و اسیلاتورها\n"
        "اندیکاتور RSI در تراز 55 قرار دارد و مومنتوم صعودی تثبیت شده است.\n"
        "## سطوح فیبوناچی و تارگت‌های قیمتی\n"
        "ترازهای فیبوناچی ریتریسمنت 0.382 و 0.618 به عنوان حمایت کلیدی عمل می‌کنند.\n"
        "## تحلیل تابلوخوانی، قدرت خریدار و جریان پول هوشمند\n"
        "نسبت سرانه قدرت خریدار به فروشنده 1.8 بوده و ورود پول هوشمند تایید می‌شود.\n"
    ) * 2

    fund_content = (
        "# گزارش تحلیل بنیادی و ارزیابی ارزش ذاتی نماد فملی\n"
        "## صورت‌های مالی و تحلیل سودآوری\n"
        "بررسی صورت‌های مالی حاکی از تداوم سودآوری ناخالص و عملیاتی شرکت است.\n"
        "## ساختار حاشیه سودها (Margins)\n"
        "حاشیه سود ناخالص شرکت 45% و حاشیه سود خالص 32% ثبت گردیده است.\n"
        "## نسبت‌های مالی و ارزیابی P/E\n"
        "نسبت P/E جاری برابر با 5.8 بوده و P/E آینده‌نگر (Forward P/E) جذاب ارزیابی می‌شود.\n"
    ) * 2

    (symbol_dir / "technical_report.md").write_text(tech_content, encoding="utf-8")
    (symbol_dir / "fundamental_report.md").write_text(fund_content, encoding="utf-8")

    # Chart images
    (symbol_dir / "charts" / "candlestick_overview.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (symbol_dir / "charts" / "indicators_momentum.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (symbol_dir / "charts" / "tape_reading_money_flow.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")

    inspector = QualityInspector()
    res = inspector.inspect_analysts(symbol_dir)
    assert res.is_passed is True
    assert res.score >= 8.0
    assert len(res.defects) == 0


def test_inspector_fails_analysts_missing_charts_or_reports(tmp_path):
    symbol_dir = tmp_path / "فملی"
    symbol_dir.mkdir()

    # Missing all reports and charts
    inspector = QualityInspector()
    res = inspector.inspect_stage("analysts", symbol_dir)
    assert res.is_passed is False
    assert res.score < 8.0
    assert any("technical_report.md" in d for d in res.defects)
    assert any("fundamental_report.md" in d for d in res.defects)
    assert any("charts" in d or "candlestick_overview.png" in d for d in res.defects)


def test_inspector_passes_healthy_strategy_stage(tmp_path):
    symbol_dir = tmp_path / "خودرو"
    symbol_dir.mkdir()

    strategy_content = (
        "# استراتژی معاملاتی و توصیه نهایی سرمایه‌گذاری نماد خودرو\n"
        "## ۱. سیگنال نهایی و حکم استراتژیک\n"
        "**سیگنال پیشنهادی:** خرید پله‌ای (Accumulate)\n"
        "## ۲. جدول عملیاتی برنامه معاملاتی\n"
        "| پارامتر معاملاتی | مقدار / تراز | توضیحات |\n"
        "| :--- | :--- | :--- |\n"
        "| نقطه ورود بهینه | ۱۰۰۰ ریال | محدوده حمایتی |\n"
        "| حد ضرر (Stop Loss) | ۹۰۰ ریال | خروج در صورت شکست |\n"
        "## ۳. تحلیل افق‌های سه‌گانه سرمایه‌گذاری\n"
        "- **کوتاه‌مدت (۱ تا ۴ هفته):** نوسان‌گیری با تابلوخوانی.\n"
        "- **میان‌مدت (۱ تا ۳ ماه):** شکست الگو و گزارش کدال.\n"
        "- **بلندمدت (۶ تا ۱۲ ماه):** ارزش ذاتی و مجمع سالانه.\n"
        "## ۴. شروط ابطال سناریوی صعودی (Invalidation Triggers)\n"
        "- شکست قطعی حد ضرر ۹۰۰ ریال با حجم معاملاتی سنگین موجب ابطال سناریو است.\n"
    )

    (symbol_dir / "final_recommendation.md").write_text(strategy_content, encoding="utf-8")

    inspector = QualityInspector()
    res = inspector.inspect_strategy(symbol_dir)
    assert res.is_passed is True
    assert res.score >= 8.0
    assert len(res.defects) == 0


def test_inspector_fails_strategy_missing_components(tmp_path):
    symbol_dir = tmp_path / "خودرو"
    symbol_dir.mkdir()

    # Incomplete strategy report (missing stop loss and horizons)
    incomplete_content = (
        "# گزارش ناقص\n"
        "این یک متن کوتاه بدون سیگنال و بدون جدول و بدون حد ضرر است.\n"
    )
    (symbol_dir / "final_recommendation.md").write_text(incomplete_content, encoding="utf-8")

    inspector = QualityInspector()
    res = inspector.inspect_stage("strategy", symbol_dir)
    assert res.is_passed is False
    assert res.score < 8.0
    assert len(res.defects) > 0


def test_inspector_unknown_stage(tmp_path):
    inspector = QualityInspector()
    res = inspector.inspect_stage("unknown_stage", tmp_path)
    assert res.is_passed is False
    assert res.score == 0.0
    assert len(res.defects) > 0


def test_inspector_accepts_string_path(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)

    (symbol_dir / "codal_reports" / "letters_index.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "news" / "news_archive.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "market_data" / "trade_history.csv").write_text("date,close\n2026-01-01,1000", encoding="utf-8")
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text("{}", encoding="utf-8")

    inspector = QualityInspector()
    # Pass str instead of Path
    res = inspector.inspect_stage("crawler", str(symbol_dir))
    assert res.is_passed is True
