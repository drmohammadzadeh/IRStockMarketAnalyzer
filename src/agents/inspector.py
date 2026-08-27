import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Union, Optional


@dataclass
class InspectionResult:
    """Inspection and audit result for a pipeline stage."""
    is_passed: bool
    score: float
    defects: List[str] = field(default_factory=list)
    feedback: str = ""


class QualityInspector:
    """Quality Inspector Agent & Evaluation Rubric.

    Audits artifacts and generated outputs for each stage in the multi-agent analysis pipeline:
    - crawler
    - summarizer
    - analysts
    - strategy
    """

    def __init__(self):
        pass

    def inspect_crawler(self, symbol_dir: Union[str, Path]) -> InspectionResult:
        """Inspects crawler stage outputs."""
        symbol_path = Path(symbol_dir)
        defects: List[str] = []
        critical = False
        score = 10.0

        # 1. codal_reports/letters_index.json
        letters_file = symbol_path / "codal_reports" / "letters_index.json"
        if not letters_file.exists():
            defects.append("فایل اطلاعیه‌های کدال (codal_reports/letters_index.json) وجود ندارد.")
            critical = True
            score -= 2.5
        else:
            try:
                content = letters_file.read_text(encoding="utf-8")
                parsed = json.loads(content)
                if not isinstance(parsed, (list, dict)):
                    defects.append("ساختار فایل letters_index.json باید لیست یا دیکشنری معتبر باشد.")
                    score -= 1.0
            except Exception as e:
                defects.append(f"فایل letters_index.json ساختار JSON معتبر ندارد: {str(e)}")
                critical = True
                score -= 2.5

        # 2. news/news_archive.json
        news_file = symbol_path / "news" / "news_archive.json"
        if not news_file.exists():
            defects.append("فایل آرشیو اخبار (news/news_archive.json) وجود ندارد.")
            critical = True
            score -= 2.5
        else:
            try:
                content = news_file.read_text(encoding="utf-8")
                parsed = json.loads(content)
                if not isinstance(parsed, (list, dict)):
                    defects.append("ساختار فایل news_archive.json باید لیست یا دیکشنری معتبر باشد.")
                    score -= 1.0
            except Exception as e:
                defects.append(f"فایل news_archive.json ساختار JSON معتبر ندارد: {str(e)}")
                critical = True
                score -= 2.5

        # 3. market_data/trade_history.csv
        trade_file = symbol_path / "market_data" / "trade_history.csv"
        if not trade_file.exists():
            defects.append("فایل سابقه معاملات (market_data/trade_history.csv) یافت نشد.")
            critical = True
            score -= 2.5
        else:
            try:
                content = trade_file.read_text(encoding="utf-8").strip()
                if not content:
                    defects.append("فایل سابقه معاملات (market_data/trade_history.csv) خالی است.")
                    critical = True
                    score -= 2.5
            except Exception as e:
                defects.append(f"خطا در خواندن فایل سابقه معاملات: {str(e)}")
                critical = True
                score -= 2.5

        # 4. market_data/orderbook_tape.json
        orderbook_file = symbol_path / "market_data" / "orderbook_tape.json"
        if not orderbook_file.exists():
            defects.append("فایل تابلوی معاملات و سفارشات (market_data/orderbook_tape.json) یافت نشد.")
            critical = True
            score -= 2.5
        else:
            try:
                content = orderbook_file.read_text(encoding="utf-8")
                parsed = json.loads(content)
                if not isinstance(parsed, (dict, list)):
                    defects.append("ساختار فایل orderbook_tape.json معتبر نیست.")
                    score -= 1.0
            except Exception as e:
                defects.append(f"فایل orderbook_tape.json ساختار JSON معتبر ندارد: {str(e)}")
                critical = True
                score -= 2.5

        score = max(0.0, min(10.0, round(score, 1)))
        is_passed = (score >= 8.0) and not critical

        if is_passed:
            feedback = f"خروجی مرحله دریافت داده (Crawler) با امتیاز {score}/10 با موفقیت تأیید شد."
        else:
            feedback = f"نقص‌های شناسایی‌شده در خروجی مرحله دریافت داده (Crawler) (امتیاز: {score}/10):\n" + "\n".join(
                f"- {d}" for d in defects
            )

        return InspectionResult(
            is_passed=is_passed,
            score=score,
            defects=defects,
            feedback=feedback,
        )

    def inspect_summarizer(self, symbol_dir: Union[str, Path]) -> InspectionResult:
        """Inspects summarizer stage outputs."""
        symbol_path = Path(symbol_dir)
        defects: List[str] = []
        critical = False
        score = 10.0

        # 1. codal_reports/codal_summaries.md
        codal_summary = symbol_path / "codal_reports" / "codal_summaries.md"
        if not codal_summary.exists():
            defects.append("فایل خلاصه گزارش‌های کدال (codal_reports/codal_summaries.md) وجود ندارد.")
            critical = True
            score -= 5.0
        else:
            try:
                content = codal_summary.read_text(encoding="utf-8")
                if len(content.encode("utf-8")) <= 100:
                    defects.append("فایل خلاصه کدال بسیار کوتاه و ناکافی است (کمتر از 100 بایت).")
                    critical = True
                    score -= 3.0
                if not any(h in content for h in ["#", "کدال", "صورت", "خلاصه", "گزارش"]):
                    defects.append("فایل خلاصه کدال فاقد سرفصل‌ها و ساختار استاندارد است.")
                    score -= 2.0
            except Exception as e:
                defects.append(f"خطا در بررسی فایل خلاصه کدال: {str(e)}")
                critical = True
                score -= 5.0

        # 2. news/news_summary.md
        news_summary = symbol_path / "news" / "news_summary.md"
        if not news_summary.exists():
            defects.append("فایل خلاصه اخبار (news/news_summary.md) وجود ندارد.")
            critical = True
            score -= 5.0
        else:
            try:
                content = news_summary.read_text(encoding="utf-8")
                if len(content.encode("utf-8")) <= 100:
                    defects.append("فایل خلاصه اخبار بسیار کوتاه و ناکافی است (کمتر از 100 بایت).")
                    critical = True
                    score -= 3.0
                if not any(h in content for h in ["#", "اخبار", "خلاصه", "ریسک", "رویداد"]):
                    defects.append("فایل خلاصه اخبار فاقد سرفصل‌ها و ساختار استاندارد است.")
                    score -= 2.0
            except Exception as e:
                defects.append(f"خطا در بررسی فایل خلاصه اخبار: {str(e)}")
                critical = True
                score -= 5.0

        score = max(0.0, min(10.0, round(score, 1)))
        is_passed = (score >= 8.0) and not critical

        if is_passed:
            feedback = f"خروجی مرحله تلخیص و پردازش محتوا (Summarizer) با امتیاز {score}/10 با موفقیت تأیید شد."
        else:
            feedback = f"نقص‌های شناسایی‌شده در خروجی مرحله تلخیص (Summarizer) (امتیاز: {score}/10):\n" + "\n".join(
                f"- {d}" for d in defects
            )

        return InspectionResult(
            is_passed=is_passed,
            score=score,
            defects=defects,
            feedback=feedback,
        )

    def inspect_analysts(self, symbol_dir: Union[str, Path]) -> InspectionResult:
        """Inspects technical and fundamental analysts stage outputs, including charts."""
        symbol_path = Path(symbol_dir)
        defects: List[str] = []
        critical = False
        score = 10.0

        # 1. technical_report.md
        tech_report = symbol_path / "technical_report.md"
        if not tech_report.exists():
            defects.append("فایل گزارش تحلیل تکنیکال (technical_report.md) وجود ندارد.")
            critical = True
            score -= 3.5
        else:
            try:
                content = tech_report.read_text(encoding="utf-8")
                if len(content.encode("utf-8")) <= 300:
                    defects.append("گزارش تحلیل تکنیکال ناقص یا بسیار کوتاه است (کمتر از 300 بایت).")
                    score -= 1.5
                # Check for indicators, fibonacci, tape reading
                has_indicators = any(k in content for k in ["اندیکاتور", "شاخص", "RSI", "اسیلاتور", "مومنتوم", "indicator"])
                has_fibonacci = any(k in content for k in ["فیبوناچی", "حمایت", "مقاومت", "fibonacci", "سطوح"])
                has_tape = any(k in content for k in ["تابلو", "پول هوشمند", "خریدار", "orderbook", "tape"])
                if not (has_indicators and has_fibonacci and has_tape):
                    missing_tech = []
                    if not has_indicators:
                        missing_tech.append("اندیکاتورها")
                    if not has_fibonacci:
                        missing_tech.append("سطوح فیبوناچی و حمایت/مقاومت")
                    if not has_tape:
                        missing_tech.append("تابلوخوانی و پول هوشمند")
                    defects.append(f"گزارش تکنیکال فاقد بخش‌های ضروری است: {', '.join(missing_tech)}")
                    score -= 1.0
            except Exception as e:
                defects.append(f"خطا در بررسی فایل گزارش تکنیکال: {str(e)}")
                critical = True
                score -= 3.5

        # 2. fundamental_report.md
        fund_report = symbol_path / "fundamental_report.md"
        if not fund_report.exists():
            defects.append("فایل گزارش تحلیل بنیادی (fundamental_report.md) وجود ندارد.")
            critical = True
            score -= 3.5
        else:
            try:
                content = fund_report.read_text(encoding="utf-8")
                if len(content.encode("utf-8")) <= 300:
                    defects.append("گزارش تحلیل بنیادی ناقص یا بسیار کوتاه است (کمتر از 300 بایت).")
                    score -= 1.5
                # Check for financial statements, margins, PE/valuation
                has_financials = any(k in content for k in ["صورت‌های مالی", "صورتهای مالی", "ترازنامه", "سودآوری", "financial statements"])
                has_margins = any(k in content for k in ["حاشیه سود", "حاشیه", "margin", "ناخالص", "عملیاتی"])
                has_pe = any(k in content for k in ["P/E", "ارزش‌گذاری", "ارزش ذاتی", "قیمت منصفانه", "valuation", "EPS"])
                if not (has_financials and has_margins and has_pe):
                    missing_fund = []
                    if not has_financials:
                        missing_fund.append("صورت‌های مالی")
                    if not has_margins:
                        missing_fund.append("ساختار حاشیه سود")
                    if not has_pe:
                        missing_fund.append("نسبت‌های مالی و ارزش‌گذاری P/E")
                    defects.append(f"گزارش بنیادی فاقد بخش‌های ضروری است: {', '.join(missing_fund)}")
                    score -= 1.0
            except Exception as e:
                defects.append(f"خطا در بررسی فایل گزارش بنیادی: {str(e)}")
                critical = True
                score -= 3.5

        # 3. charts (candlestick_overview.png, indicators_momentum.png, tape_reading_money_flow.png)
        chart_files = [
            "candlestick_overview.png",
            "indicators_momentum.png",
            "tape_reading_money_flow.png",
        ]
        charts_dir = symbol_path / "charts"
        for chart_name in chart_files:
            c_path = charts_dir / chart_name
            if not c_path.exists():
                defects.append(f"نمودار تحلیل گرافیکی ({chart_name}) یافت نشد.")
                score -= 1.0
            elif c_path.stat().st_size == 0:
                defects.append(f"فایل تصویر نمودار ({chart_name}) خالی است.")
                score -= 1.0

        score = max(0.0, min(10.0, round(score, 1)))
        is_passed = (score >= 8.0) and not critical

        if is_passed:
            feedback = f"خروجی مرحله تحلیل‌گران (Analysts) با امتیاز {score}/10 با موفقیت تأیید شد."
        else:
            feedback = f"نقص‌های شناسایی‌شده در خروجی مرحله تحلیل‌گران (Analysts) (امتیاز: {score}/10):\n" + "\n".join(
                f"- {d}" for d in defects
            )

        return InspectionResult(
            is_passed=is_passed,
            score=score,
            defects=defects,
            feedback=feedback,
        )

    def inspect_strategy(self, symbol_dir: Union[str, Path]) -> InspectionResult:
        """Inspects strategy and recommendation stage outputs."""
        symbol_path = Path(symbol_dir)
        defects: List[str] = []
        critical = False
        score = 10.0

        # 1. final_recommendation.md
        strat_report = symbol_path / "final_recommendation.md"
        if not strat_report.exists():
            defects.append("فایل توصیه استراتژیک نهایی (final_recommendation.md) وجود ندارد.")
            critical = True
            score = 0.0
        else:
            try:
                content = strat_report.read_text(encoding="utf-8")
                if len(content.encode("utf-8")) <= 200:
                    defects.append("گزارش توصیه نهایی ناقص یا بسیار کوتاه است (کمتر از 200 بایت).")
                    score -= 3.0

                has_signal = any(k in content for k in ["خرید", "فروش", "نگهداری", "سیگنال", "توصیه", "signal", "recommendation"])
                has_table = ("|" in content) or ("جدول" in content) or ("table" in content)
                has_horizons = any(k in content for k in ["کوتاه‌مدت", "کوتاه مدت", "میان‌مدت", "میان مدت", "بلندمدت", "بلند مدت", "افق", "horizon"])
                has_stop_loss = any(k in content for k in ["حد ضرر", "stop loss", "stop-loss", "Stop Loss"])
                has_invalidation = any(k in content for k in ["ابطال", "invalidation", "شروط ابطال", "شرایط ابطال"])

                missing_elements = []
                if not has_signal:
                    missing_elements.append("سیگنال و حکم معاملاتی")
                    score -= 1.5
                if not has_table:
                    missing_elements.append("جدول عملیاتی معاملات")
                    score -= 1.5
                if not has_horizons:
                    missing_elements.append("تفکیک افق‌های سه‌گانه زمانی")
                    score -= 1.5
                if not has_stop_loss:
                    missing_elements.append("تعیین حد ضرر پویا")
                    score -= 1.5
                if not has_invalidation:
                    missing_elements.append("شروط ابطال تحلیل")
                    score -= 1.5

                if missing_elements:
                    defects.append(f"گزارش استراتژی فاقد بخش‌های کلیدی است: {', '.join(missing_elements)}")

            except Exception as e:
                defects.append(f"خطا در بررسی فایل توصیه نهایی: {str(e)}")
                critical = True
                score = 0.0

        score = max(0.0, min(10.0, round(score, 1)))
        is_passed = (score >= 8.0) and not critical

        if is_passed:
            feedback = f"خروجی مرحله تدوین استراتژی (Strategy) با امتیاز {score}/10 با موفقیت تأیید شد."
        else:
            feedback = f"نقص‌های شناسایی‌شده در خروجی مرحله استراتژی (Strategy) (امتیاز: {score}/10):\n" + "\n".join(
                f"- {d}" for d in defects
            )

        return InspectionResult(
            is_passed=is_passed,
            score=score,
            defects=defects,
            feedback=feedback,
        )

    def inspect_stage(self, stage_name: str, symbol_dir: Union[str, Path]) -> InspectionResult:
        """Inspects the outputs of a given stage name."""
        stage = (stage_name or "").strip().lower()
        if stage in ("crawler", "crawl", "fetch"):
            return self.inspect_crawler(symbol_dir)
        elif stage in ("summarizer", "summary", "summarize"):
            return self.inspect_summarizer(symbol_dir)
        elif stage in ("analysts", "analyst", "analysis", "technical_fundamental"):
            return self.inspect_analysts(symbol_dir)
        elif stage in ("strategy", "recommender", "recommendation"):
            return self.inspect_strategy(symbol_dir)
        else:
            return InspectionResult(
                is_passed=False,
                score=0.0,
                defects=[f"مرحله ناشناخته یا نامعتبر: '{stage_name}'"],
                feedback=f"نام مرحله نامعتبر است: '{stage_name}'. مراحل معتبر: crawler, summarizer, analysts, strategy.",
            )
