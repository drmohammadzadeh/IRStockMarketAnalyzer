# Author: alimohammadzadeh@ut.ac.ir
"""Supreme Judge Agent (JudgeAgent) & 5-Pillar Arbitration Rubric.

Evaluates the complete output of a stock's analysis against a strict 5-pillar rubric:
1. File Integrity (Magic Bytes validation for PDF/Excel)
2. Data Freshness & Market Data Completeness
3. Social Sentiment Coverage (Sahamyab & Rahavard)
4. Analytical Depth & Quality (Fundamental, Technical, Educational Guides & PNG Charts)
5. 3-Tier Recommendation Validity (Multi-factor scoring, stop-loss, horizons)

Issues an official JudgementVerdict with PASS/REJECT status, remediation directives,
and an official Persian Arbitration Certificate.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

try:
    import jdatetime
except ImportError:
    jdatetime = None


@dataclass
class JudgementVerdict:
    """Official judgement and arbitration verdict for a stock's analysis artifacts."""
    is_approved: bool
    score: float
    status: str
    critical_defects: List[str] = field(default_factory=list)
    remedial_actions: List[str] = field(default_factory=list)
    audit_details: Dict[str, Any] = field(default_factory=dict)
    certificate_markdown: str = ""


class JudgeAgent:
    """Supreme Judge Agent enforcing the 5-Pillar Arbitration Rubric.

    Author: alimohammadzadeh@ut.ac.ir
    """

    def __init__(self):
        pass

    @staticmethod
    def _validate_magic_bytes(content: bytes, filename: str) -> bool:
        """Validates binary magic bytes for PDF, Excel, and PNG documents."""
        if not content or len(content) < 4:
            return False
        lower_fn = filename.lower()
        if lower_fn.endswith(".pdf"):
            return content.startswith(b"%PDF-")
        elif lower_fn.endswith(".xlsx"):
            return content.startswith(b"PK\x03\x04")
        elif lower_fn.endswith(".xls"):
            return content.startswith(b"\xd0\xcf\x11\xe0")
        elif lower_fn.endswith(".png"):
            return content.startswith(b"\x89PNG")
        return True

    @staticmethod
    def _is_html_or_empty(content: bytes) -> bool:
        """Checks if content is empty or contains HTML error page markers."""
        if not content or len(content.strip()) == 0:
            return True
        lstripped = content.lstrip()
        html_markers = (b"<!doctype", b"<!DOCTYPE", b"<html", b"<HTML", b"<?xml", b"\r\n<!doctype", b"\r\n<html")
        return any(lstripped.startswith(marker) for marker in html_markers)

    def audit_symbol(self, symbol: str, symbol_dir: Union[str, Path]) -> JudgementVerdict:
        """Audits all artifacts for a given symbol against the 5-Pillar Arbitration Rubric.

        Returns an official JudgementVerdict with pass/reject decision and arbitration certificate.
        """
        path = Path(symbol_dir)
        critical_defects: List[str] = []
        remedial_actions: List[str] = []
        audit_details: Dict[str, Any] = {}

        # =========================================================================
        # Pillar 1: File Integrity (Weight: 2.5)
        # =========================================================================
        p1_score = 2.5
        p1_defects: List[str] = []
        codal_dir = path / "codal_reports"

        if not codal_dir.exists():
            p1_score = 0.0
            p1_defects.append("پوشه گزارش‌های کدال (codal_reports) وجود ندارد.")
            remedial_actions.append("ایجاد پوشه codal_reports و اجرای Crawler برای دریافت گزارش‌های کدال.")
        else:
            # Check letters_index.json
            index_file = codal_dir / "letters_index.json"
            if not index_file.exists():
                p1_score = max(0.0, p1_score - 1.0)
                p1_defects.append("فایل فهرست اطلاعیه‌ها (codal_reports/letters_index.json) یافت نشد.")
                remedial_actions.append("دریافت فهرست اطلاعیه‌های کدال و ذخیره در letters_index.json.")
            else:
                try:
                    idx_content = json.loads(index_file.read_text(encoding="utf-8"))
                    if not isinstance(idx_content, (list, dict)):
                        p1_score = max(0.0, p1_score - 0.5)
                        p1_defects.append("ساختار فایل letters_index.json معتبر نیست.")
                except Exception as e:
                    p1_score = max(0.0, p1_score - 1.0)
                    p1_defects.append(f"خطا در خواندن فایل letters_index.json: {str(e)}")

            # Check binary files magic bytes
            binary_files = [f for f in codal_dir.iterdir() if f.is_file() and f.suffix.lower() in (".pdf", ".xlsx", ".xls")]
            corrupt_files = []
            for f in binary_files:
                try:
                    content = f.read_bytes()
                    if self._is_html_or_empty(content) or not self._validate_magic_bytes(content, f.name):
                        corrupt_files.append(f.name)
                except Exception:
                    corrupt_files.append(f.name)

            if corrupt_files:
                p1_score = 0.0
                defect_msg = f"فایل‌های معیوب و نامعتبر (عدم تطابق بایت‌های جادویی یا صفحات خطای HTML) در کدال: {', '.join(corrupt_files)}"
                critical_defects.append(defect_msg)
                p1_defects.append(defect_msg)
                remedial_actions.append(f"پاکسازی فایل‌های خراب کدال ({', '.join(corrupt_files)}) و دانلود مجدد با اعتبارسنجی بایت‌های جادویی.")

        p1_score = max(0.0, min(2.5, round(p1_score, 2)))
        audit_details["pillar1_file_integrity"] = {
            "score": p1_score,
            "max_score": 2.5,
            "passed": p1_score >= 2.0 and not any("کدال" in d and "معیوب" in d for d in critical_defects),
            "defects": p1_defects,
        }

        # =========================================================================
        # Pillar 2: Data Freshness & Completeness (Weight: 2.5)
        # =========================================================================
        p2_score = 2.5
        p2_defects: List[str] = []
        market_dir = path / "market_data"

        # Check trade_history.csv
        trade_file = market_dir / "trade_history.csv"
        if not trade_file.exists():
            p2_score = max(0.0, p2_score - 1.5)
            defect_msg = "فایل سابقه معاملات (market_data/trade_history.csv) یافت نشد."
            critical_defects.append(defect_msg)
            p2_defects.append(defect_msg)
            remedial_actions.append("دریافت سابقه معاملات نماد از سامانه TSETMC و ذخیره در market_data/trade_history.csv.")
        else:
            try:
                trade_content = trade_file.read_text(encoding="utf-8").strip()
                if not trade_content or len(trade_content.splitlines()) <= 1:
                    p2_score = max(0.0, p2_score - 1.5)
                    defect_msg = "فایل سابقه معاملات (market_data/trade_history.csv) خالی یا فاقد سطرهای معاملاتی است."
                    critical_defects.append(defect_msg)
                    p2_defects.append(defect_msg)
                    remedial_actions.append("تکمیل سابقه معاملات نماد با اطلاعات معتبر کندل‌ها از TSETMC.")
            except Exception as e:
                p2_score = max(0.0, p2_score - 1.5)
                defect_msg = f"خطا در خواندن فایل سابقه معاملات: {str(e)}"
                critical_defects.append(defect_msg)
                p2_defects.append(defect_msg)
                remedial_actions.append("رفع خطای فرمت یا ساختار فایل سابقه معاملات.")

        # Check orderbook_tape.json
        orderbook_file = market_dir / "orderbook_tape.json"
        if not orderbook_file.exists():
            p2_score = max(0.0, p2_score - 1.0)
            defect_msg = "فایل تابلوی معاملات و سفارشات (market_data/orderbook_tape.json) یافت نشد."
            p2_defects.append(defect_msg)
            remedial_actions.append("استخراج تابلوی لحظه‌ای، سرانه خریدار/فروشنده و صف‌های معاملات در orderbook_tape.json.")
        else:
            try:
                ob_data = json.loads(orderbook_file.read_text(encoding="utf-8"))
                if not isinstance(ob_data, (dict, list)):
                    p2_score = max(0.0, p2_score - 0.5)
                    p2_defects.append("ساختار orderbook_tape.json معتبر نیست.")
            except Exception as e:
                p2_score = max(0.0, p2_score - 1.0)
                p2_defects.append(f"خطا در پارس orderbook_tape.json: {str(e)}")

        p2_score = max(0.0, min(2.5, round(p2_score, 2)))
        audit_details["pillar2_data_freshness"] = {
            "score": p2_score,
            "max_score": 2.5,
            "passed": p2_score >= 2.0 and not any("trade_history.csv" in d for d in critical_defects),
            "defects": p2_defects,
        }

        # =========================================================================
        # Pillar 3: Social Sentiment Coverage (Weight: 1.5)
        # =========================================================================
        p3_score = 1.5
        p3_defects: List[str] = []
        sentiment_file = path / "news" / "social_sentiment.json"

        if not sentiment_file.exists():
            p3_score = 0.0
            p3_defects.append("فایل شاخص احساسات شبکه‌های اجتماعی (news/social_sentiment.json) یافت نشد.")
            remedial_actions.append("اجرای خزشگر نظرات شبکه‌های اجتماعی (سهامیاب/رهاورد) و ذخیره تحلیل در social_sentiment.json.")
        else:
            try:
                sent_data = json.loads(sentiment_file.read_text(encoding="utf-8"))
                if "composite_sentiment_score" not in sent_data:
                    p3_score = max(0.0, p3_score - 0.75)
                    p3_defects.append("فایل social_sentiment.json فاقد نمره ترکیبی احساسات (composite_sentiment_score) است.")
                    remedial_actions.append("محاسبه امتیاز تجمیعی سنتیمنت شبکه‌های اجتماعی بر مبنای نظرات جمع‌آوری‌شده.")
            except Exception as e:
                p3_score = 0.0
                p3_defects.append(f"خطا در خواندن فایل social_sentiment.json: {str(e)}")
                remedial_actions.append("اصلاح ساختار JSON فایل تحلیل احساسات شبکه‌های اجتماعی.")

        p3_score = max(0.0, min(1.5, round(p3_score, 2)))
        audit_details["pillar3_social_sentiment"] = {
            "score": p3_score,
            "max_score": 1.5,
            "passed": p3_score >= 1.0,
            "defects": p3_defects,
        }

        # =========================================================================
        # Pillar 4: Analytical Depth & Quality (Weight: 2.0)
        # =========================================================================
        p4_score = 2.0
        p4_defects: List[str] = []

        # 1. fundamental_report.md
        fund_file = path / "fundamental_report.md"
        if not fund_file.exists():
            p4_score = max(0.0, p4_score - 0.7)
            p4_defects.append("گزارش تحلیل بنیادی (fundamental_report.md) یافت نشد.")
            remedial_actions.append("تولید گزارش جامع تحلیل بنیادی شامل نسبت‌های مالی، حاشیه سود و ارزش‌گذاری.")
        else:
            try:
                fund_text = fund_file.read_text(encoding="utf-8")
                has_metrics = any(k in fund_text for k in ["P/E", "حاشیه", "سود", "EPS", "ارزش", "صورت‌های مالی", "financial"])
                if len(fund_text) < 150 or not has_metrics:
                    p4_score = max(0.0, p4_score - 0.4)
                    p4_defects.append("گزارش تحلیل بنیادی فاقد نسبت‌های مالی و ارزیابی کافی است.")
                    remedial_actions.append("تکمیل شاخص‌های کلیدی بنیادی (حاشیه سود، نسبت P/E و ارزش ذاتی) در گزارش بنیادی.")
            except Exception as e:
                p4_score = max(0.0, p4_score - 0.7)
                p4_defects.append(f"خطا در بررسی گزارش بنیادی: {str(e)}")

        # 2. technical_report.md & educational guide
        tech_file = path / "technical_report.md"
        if not tech_file.exists():
            p4_score = max(0.0, p4_score - 0.7)
            p4_defects.append("گزارش تحلیل تکنیکال (technical_report.md) یافت نشد.")
            remedial_actions.append("تولید گزارش جامع تحلیل تکنیکال همراه با راهنمای آموزشی.")
        else:
            try:
                tech_text = tech_file.read_text(encoding="utf-8")
                has_edu = any(k in tech_text for k in ["راهنمای آموزشی", "آموزش", "نحوه خواندن", "تفسیر آموزشی", "آموزشی"])
                if not has_edu:
                    p4_score = max(0.0, p4_score - 0.5)
                    p4_defects.append("گزارش تکنیکال فاقد راهنمای آموزشی و توضیحات ساده‌فهم نمودارها است.")
                    remedial_actions.append("افزودن بخش راهنمای آموزشی و تفسیر ساده نمودارها به گزارش تحلیل تکنیکال.")
            except Exception as e:
                p4_score = max(0.0, p4_score - 0.7)
                p4_defects.append(f"خطا در بررسی گزارش تکنیکال: {str(e)}")

        # 3. charts (3 PNG charts with magic bytes)
        charts_dir = path / "charts"
        chart_names = [
            "candlestick_overview.png",
            "indicators_momentum.png",
            "tape_reading_money_flow.png",
        ]
        missing_charts = []
        for c_name in chart_names:
            c_file = charts_dir / c_name
            if not c_file.exists() or c_file.stat().st_size == 0:
                missing_charts.append(c_name)
            else:
                try:
                    c_bytes = c_file.read_bytes()
                    if not self._validate_magic_bytes(c_bytes, c_name):
                        missing_charts.append(c_name)
                except Exception:
                    missing_charts.append(c_name)

        if missing_charts:
            deduction = min(0.6, len(missing_charts) * 0.2)
            p4_score = max(0.0, p4_score - deduction)
            p4_defects.append(f"نمودارهای گرافیکی مفقود یا نامعتبر: {', '.join(missing_charts)}")
            remedial_actions.append(f"تولید و اعتبارسنجی نمودارهای گرافیکی ({', '.join(missing_charts)}) در پوشه charts.")

        p4_score = max(0.0, min(2.0, round(p4_score, 2)))
        audit_details["pillar4_analytical_depth"] = {
            "score": p4_score,
            "max_score": 2.0,
            "passed": p4_score >= 1.6,
            "defects": p4_defects,
        }

        # =========================================================================
        # Pillar 5: 3-Tier Recommendation Validity (Weight: 1.5)
        # =========================================================================
        p5_score = 1.5
        p5_defects: List[str] = []

        # final_recommendation.md
        final_md = path / "final_recommendation.md"
        if not final_md.exists():
            p5_score = max(0.0, p5_score - 0.8)
            p5_defects.append("فایل توصیه نهایی (final_recommendation.md) یافت نشد.")
            remedial_actions.append("تولید گزارش توصیه نهایی استراتژیک با جدول امتیازدهی سه‌گانه.")
        else:
            try:
                rec_text = final_md.read_text(encoding="utf-8")
                has_3tier = any(k in rec_text for k in ["امتیازدهی سه‌گانه", "امتیازدهی سه گانه", "رویکرد ۱", "رویکرد 1", "توصیه", "سیگنال"])
                if not has_3tier or len(rec_text) < 100:
                    p5_score = max(0.0, p5_score - 0.4)
                    p5_defects.append("گزارش توصیه نهایی فاقد جدول امتیازدهی سه‌گانه یا ناقص است.")
                    remedial_actions.append("درج جدول جامع امتیازدهی سه‌گانه (رویکرد وزنی، وتو و افق زمانی) در final_recommendation.md.")
            except Exception as e:
                p5_score = max(0.0, p5_score - 0.8)
                p5_defects.append(f"خطا در بررسی final_recommendation.md: {str(e)}")

        # strategy_recommendation.json
        strat_json_file = path / "strategy_recommendation.json"
        if not strat_json_file.exists():
            p5_score = max(0.0, p5_score - 0.7)
            p5_defects.append("فایل ساختاریافته استراتژی (strategy_recommendation.json) یافت نشد.")
            remedial_actions.append("ذخیره متغیرهای عملیاتی و امتیازات استراتژی در strategy_recommendation.json.")
        else:
            try:
                strat_data = json.loads(strat_json_file.read_text(encoding="utf-8"))
                if not isinstance(strat_data, dict):
                    p5_score = max(0.0, p5_score - 0.3)
                    p5_defects.append("فرمت strategy_recommendation.json معتبر نیست.")
            except Exception as e:
                p5_score = max(0.0, p5_score - 0.7)
                p5_defects.append(f"خطا در خواندن strategy_recommendation.json: {str(e)}")

        p5_score = max(0.0, min(1.5, round(p5_score, 2)))
        audit_details["pillar5_recommendation_validity"] = {
            "score": p5_score,
            "max_score": 1.5,
            "passed": p5_score >= 1.2,
            "defects": p5_defects,
        }

        # =========================================================================
        # Final Score & Approval Decision
        # =========================================================================
        total_score = round(p1_score + p2_score + p3_score + p4_score + p5_score, 1)
        total_score = max(0.0, min(10.0, total_score))

        is_approved = (total_score >= 8.5) and (len(critical_defects) == 0)
        status = "APPROVED" if is_approved else "REJECTED"

        # Deduplicate remedial actions
        deduped_actions: List[str] = []
        for a in remedial_actions:
            if a not in deduped_actions:
                deduped_actions.append(a)

        if is_approved:
            deduped_actions = []

        # Generate Certificate
        certificate_markdown = self._generate_certificate(
            symbol=symbol,
            score=total_score,
            is_approved=is_approved,
            status=status,
            p1_score=p1_score,
            p2_score=p2_score,
            p3_score=p3_score,
            p4_score=p4_score,
            p5_score=p5_score,
            critical_defects=critical_defects,
            remedial_actions=deduped_actions,
            audit_details=audit_details,
        )

        return JudgementVerdict(
            is_approved=is_approved,
            score=total_score,
            status=status,
            critical_defects=critical_defects,
            remedial_actions=deduped_actions,
            audit_details=audit_details,
            certificate_markdown=certificate_markdown,
        )

    def _generate_certificate(
        self,
        symbol: str,
        score: float,
        is_approved: bool,
        status: str,
        p1_score: float,
        p2_score: float,
        p3_score: float,
        p4_score: float,
        p5_score: float,
        critical_defects: List[str],
        remedial_actions: List[str],
        audit_details: Dict[str, Any],
    ) -> str:
        """Generates the official Persian Arbitration Certificate."""
        if jdatetime:
            try:
                now_shamsi = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")
            except Exception:
                now_shamsi = "1405/06/12"
        else:
            now_shamsi = "1405/06/12"

        verdict_badge = "🛡️ تأیید ممیزی داور سامانه (APPROVED)" if is_approved else "⚠️ مردود در ممیزی داور (REJECTED)"

        p1_status = "✅ تأیید" if audit_details.get("pillar1_file_integrity", {}).get("passed", False) else "❌ نقص"
        p2_status = "✅ تأیید" if audit_details.get("pillar2_data_freshness", {}).get("passed", False) else "❌ نقص"
        p3_status = "✅ تأیید" if audit_details.get("pillar3_social_sentiment", {}).get("passed", False) else "❌ نقص"
        p4_status = "✅ تأیید" if audit_details.get("pillar4_analytical_depth", {}).get("passed", False) else "❌ نقص"
        p5_status = "✅ تأیید" if audit_details.get("pillar5_recommendation_validity", {}).get("passed", False) else "❌ نقص"

        p1_desc = "سلامت بایت‌های جادویی PDF/Excel و عدم وجود فایل‌های HTML خطا" if p1_score == 2.5 else "نقص در ساختار یا بایت‌های جادویی اسناد"
        p2_desc = "جامعیت سابقه معاملات TSETMC و تابلوی عمق بازار" if p2_score == 2.5 else "کمبود یا نقص در داده‌های بازار یا تابلوی سفارشات"
        p3_desc = "پوشش دیدگاه‌های سهامیاب/رهاورد و محاسبه شاخص سنتیمنت" if p3_score == 1.5 else "عدم دسترسی یا نقص در داده‌های احساسات بازار"
        p4_desc = "تحلیل بنیادی، تکنیکال، نمودارهای سه‌گانه و راهنمای آموزشی" if p4_score == 2.0 else "نقص در نمودارها یا عدم درج راهنمای آموزشی"
        p5_desc = "مدل امتیازدهی سه‌گانه، حد ضرر پویا و تفکیک افق‌های زمانی" if p5_score == 1.5 else "نقص در ساختار جدول امتیازدهی سه‌گانه یا سیگنال"

        defects_section = ""
        if critical_defects:
            defects_section += "\n### 🚨 نقص‌های بحرانی شناسایی‌شده (Critical Defects):\n"
            for d in critical_defects:
                defects_section += f"- ❌ {d}\n"

        actions_section = ""
        if remedial_actions:
            actions_section += "\n### 🛠️ دستورالعمل‌های اصلاحی و اقدامات ترمیمی (Remediation Directives):\n"
            for idx, a in enumerate(remedial_actions, 1):
                actions_section += f"{idx}. {a}\n"

        cert = (
            f"# 🏛️ گواهی رسمی داوری و ممیزی نهایی نماد {symbol}\n\n"
            f"- **نماد تحت ممیزی:** `{symbol}`\n"
            f"- **تاریخ صدور گواهی:** `{now_shamsi}`\n"
            f"- **وضعیت ارزیابی:** **{verdict_badge}**\n"
            f"- **نمره ممیزی کسب‌شده:** **{score:.1f} از ۱۰.۰** (حدنصاب قبولی: ۸.۵)\n\n"
            f"---\n\n"
            f"## 📊 کارنامه ممیزی ارکان پنج‌گانه (5-Pillar Scorecard)\n\n"
            f"| رکن ممیزی | سقف امتیاز | امتیاز مکتسبه | وضعیت | شرح وضعیت |\n"
            f"| :--- | :---: | :---: | :---: | :--- |\n"
            f"| ۱. اصالت و سلامت فایل‌ها (File Integrity) | ۲.۵ | {p1_score:.1f} | {p1_status} | {p1_desc} |\n"
            f"| ۲. جامعیت و تازگی داده‌های بازار (Data Freshness) | ۲.۵ | {p2_score:.1f} | {p2_status} | {p2_desc} |\n"
            f"| ۳. پوشش احساسات شبکه‌های اجتماعی (Social Sentiment) | ۱.۵ | {p3_score:.1f} | {p3_status} | {p3_desc} |\n"
            f"| ۴. عمق تحلیلی، نمودارها و راهنمای آموزشی (Analytical Depth) | ۲.۰ | {p4_score:.1f} | {p4_status} | {p4_desc} |\n"
            f"| ۵. مدل امتیازدهی سه‌گانه و توصیه استراتژیک (3-Tier Recommendation) | ۱.۵ | {p5_score:.1f} | {p5_status} | {p5_desc} |\n"
            f"| **مجموع کل امتیازات** | **۱۰.۰** | **{score:.1f}** | **{status}** | **{'دارای صلاحیت و تأیید نهایی' if is_approved else 'عدم احراز صلاحیت و نیازمند بازبینی'}** |\n\n"
            f"---\n"
            f"{defects_section}"
            f"{actions_section}\n"
            f"---\n\n"
            f"**نهاد داور:** سامانه داوری عالی هوشمند بازار سرمایه (Supreme Judge Agent)\n\n"
            f"**نویسنده و توسعه دهنده:** alimohammadzadeh@ut.ac.ir\n"
        )
        return cert
