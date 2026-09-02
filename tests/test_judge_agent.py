# Author: alimohammadzadeh@ut.ac.ir
"""Tests for Supreme Judge Agent (JudgeAgent) & 5-Pillar Arbitration Rubric."""

import json
from pathlib import Path
import pytest

from src.agents.judge import JudgeAgent, JudgementVerdict
from src.agents import JudgeAgent as JudgeAgentExport, JudgementVerdict as JudgementVerdictExport


def test_exports_in_init():
    """Verify JudgeAgent and JudgementVerdict are exported properly from src.agents."""
    assert JudgeAgentExport is JudgeAgent
    assert JudgementVerdictExport is JudgementVerdict


def test_judge_agent_passes_fully_compliant_stock(tmp_path):
    """Test Pillar 1-5 compliance producing score >= 8.5, APPROVED status, and valid certificate."""
    symbol_dir = tmp_path / "زهلال"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "charts").mkdir(parents=True)

    # Pillar 1: Valid magic bytes for PDF and XLSX
    (symbol_dir / "codal_reports" / "report.pdf").write_bytes(b"%PDF-1.4\nvalid pdf binary content")
    (symbol_dir / "codal_reports" / "sheet.xlsx").write_bytes(b"PK\x03\x04\x14\x00valid xlsx zip data")
    (symbol_dir / "codal_reports" / "letters_index.json").write_text('[{"Title": "صورت مالی"}]', encoding="utf-8")

    # Pillar 2: Valid trade history and orderbook tape
    trade_csv = "date,open,high,low,close,volume\n1405-06-11,1000,1050,980,1030,500000\n1405-06-12,1030,1080,1020,1070,600000"
    (symbol_dir / "market_data" / "trade_history.csv").write_text(trade_csv, encoding="utf-8")
    orderbook = {
        "buyer_power": 1.75,
        "order_count": 1250,
        "individual_buy_vol": 800000,
        "individual_sell_vol": 450000,
    }
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text(json.dumps(orderbook), encoding="utf-8")

    # Pillar 3: Social sentiment
    sentiment_data = {
        "symbol": "زهلال",
        "composite_sentiment_score": 8.5,
        "sentiment_verdict": "بسیار صعودی و مثبت",
        "sahamyab": {"total_posts": 10, "bullish_count": 8, "bearish_count": 1},
        "rahavard365": {"total_posts": 5, "bullish_count": 4, "bearish_count": 0},
    }
    (symbol_dir / "news" / "social_sentiment.json").write_text(json.dumps(sentiment_data), encoding="utf-8")

    # Pillar 4: Analytical depth & quality + educational guide + 3 charts
    fund_md = (
        "# گزارش تحلیل بنیادی زهلال\n"
        "## نسبت‌های مالی و ارزش‌گذاری\n"
        "- نسبت P/E جاری: ۵.۲\n"
        "- حاشیه سود ناخالص: ۴۲٪\n"
        "- حاشیه سود خالص: ۲۸٪\n"
        "- سود خالص هر سهم (EPS): ۱۲۰۰ ریال\n"
        "- ارزش ذاتی برآورد شده: ۱۵۵۰۰ ریال\n"
    )
    (symbol_dir / "fundamental_report.md").write_text(fund_md, encoding="utf-8")

    tech_md = (
        "# گزارش تحلیل تکنیکال زهلال\n"
        "## وضعیت اندیکاتورها و اسیلاتورها\n"
        "شاخص RSI در سطح ۵۸ و مکدی مثبت است.\n"
        "## راهنمای آموزشی و نحوه خواندن نمودارها\n"
        "- نحوه خواندن کندل‌ها و میانگین‌های متحرک EMA 20 و 50.\n"
        "- آموزش اسیلاتور RSI و تفکیک اشباع خرید و فروش.\n"
        "- تحلیل قدرت خریدار و ورود پول هوشمند.\n"
    )
    (symbol_dir / "technical_report.md").write_text(tech_md, encoding="utf-8")

    (symbol_dir / "charts" / "candlestick_overview.png").write_bytes(b"\x89PNG\r\n\x1a\nchart1")
    (symbol_dir / "charts" / "indicators_momentum.png").write_bytes(b"\x89PNG\r\n\x1a\nchart2")
    (symbol_dir / "charts" / "tape_reading_money_flow.png").write_bytes(b"\x89PNG\r\n\x1a\nchart3")

    # Pillar 5: 3-Tier recommendation validity
    strat_md = (
        "# استراتژی و توصیه نهایی سرمایه‌گذاری زهلال\n"
        "## جدول جامع امتیازدهی سه‌گانه توصیه خرید/فروش\n"
        "| رویکرد ارزیابی | امتیاز (از ۵) | وزن | امتیاز وزنی |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| رویکرد ۱: مدل تجمیع وزنی چندعاملی | ۴.۲ | ۰.۴۰ | ۱.۶۸ |\n"
        "| رویکرد ۲: مدل درخت تصمیم و فیلترهای وتو | ۴.۵ | ۰.۳۵ | ۱.۵۸ |\n"
        "| رویکرد ۳: مدل همگرایی افق‌های زمانی و R/R | ۴.۰ | ۰.۲۵ | ۱.۰۰ |\n"
        "**امتیاز نهایی اجماع:** ۴.۲۶ / ۵.۰\n"
    )
    (symbol_dir / "final_recommendation.md").write_text(strat_md, encoding="utf-8")

    strat_json = {
        "verdict": "خرید قوی (Strong Buy)",
        "entry_zone": [1000, 1050],
        "stop_loss": 920,
        "scoring": {
            "score_weighted": 4.2,
            "score_rules": 4.5,
            "score_horizon": 4.0,
            "score_final": 4.26,
            "stars": "⭐⭐⭐⭐",
        },
    }
    (symbol_dir / "strategy_recommendation.json").write_text(json.dumps(strat_json), encoding="utf-8")

    judge = JudgeAgent()
    verdict = judge.audit_symbol("زهلال", symbol_dir)

    assert isinstance(verdict, JudgementVerdict)
    assert verdict.is_approved is True
    assert verdict.status == "APPROVED"
    assert verdict.score >= 8.5
    assert len(verdict.critical_defects) == 0
    assert len(verdict.remedial_actions) == 0

    # Verify audit details breakdown
    assert "pillar1_file_integrity" in verdict.audit_details
    assert "pillar2_data_freshness" in verdict.audit_details
    assert "pillar3_social_sentiment" in verdict.audit_details
    assert "pillar4_analytical_depth" in verdict.audit_details
    assert "pillar5_recommendation_validity" in verdict.audit_details

    # Verify certificate
    assert "🛡️ تأیید ممیزی داور سامانه" in verdict.certificate_markdown
    assert "زهلال" in verdict.certificate_markdown
    assert "alimohammadzadeh@ut.ac.ir" in verdict.certificate_markdown


def test_judge_agent_rejects_corrupted_magic_bytes(tmp_path):
    """Corrupted PDF in codal_reports must trigger a CRITICAL DEFECT and REJECTED status."""
    symbol_dir = tmp_path / "فولاد"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "charts").mkdir(parents=True)

    # Corrupted PDF with HTML error page
    (symbol_dir / "codal_reports" / "corrupt_letter.pdf").write_bytes(b"\r\n<!doctype html><html><body>Error 500</body></html>")
    (symbol_dir / "codal_reports" / "letters_index.json").write_text("[]", encoding="utf-8")

    (symbol_dir / "market_data" / "trade_history.csv").write_text("date,close\n1405-06-11,5000", encoding="utf-8")
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text("{}", encoding="utf-8")
    (symbol_dir / "news" / "social_sentiment.json").write_text('{"composite_sentiment_score": 6.0}', encoding="utf-8")
    (symbol_dir / "fundamental_report.md").write_text("# گزارش بنیادی\nP/E: 6, حاشیه سود", encoding="utf-8")
    (symbol_dir / "technical_report.md").write_text("# گزارش تکنیکال\nراهنمای آموزشی", encoding="utf-8")
    (symbol_dir / "charts" / "candlestick_overview.png").write_bytes(b"\x89PNG")
    (symbol_dir / "charts" / "indicators_momentum.png").write_bytes(b"\x89PNG")
    (symbol_dir / "charts" / "tape_reading_money_flow.png").write_bytes(b"\x89PNG")
    (symbol_dir / "final_recommendation.md").write_text("# توصیه نهایی\nامتیازدهی سه‌گانه", encoding="utf-8")
    (symbol_dir / "strategy_recommendation.json").write_text('{"scoring": {}}', encoding="utf-8")

    judge = JudgeAgent()
    verdict = judge.audit_symbol("فولاد", symbol_dir)

    assert verdict.is_approved is False
    assert verdict.status == "REJECTED"
    assert len(verdict.critical_defects) > 0
    assert any("corrupt_letter.pdf" in d or "جادویی" in d or "magic" in d or "HTML" in d for d in verdict.critical_defects)
    assert any("پاکسازی" in a or "دانلود مجدد" in a or "clean" in a or "کدال" in a for a in verdict.remedial_actions)
    assert "⚠️ مردود در ممیزی داور" in verdict.certificate_markdown


def test_judge_agent_rejects_missing_or_empty_trade_history(tmp_path):
    """Missing or empty market_data/trade_history.csv must cause critical defect."""
    symbol_dir = tmp_path / "شتران"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)

    # Empty trade history
    (symbol_dir / "market_data" / "trade_history.csv").write_text("", encoding="utf-8")

    judge = JudgeAgent()
    verdict = judge.audit_symbol("شتران", symbol_dir)

    assert verdict.is_approved is False
    assert verdict.status == "REJECTED"
    assert any("trade_history.csv" in d for d in verdict.critical_defects)
    assert any("سابقه معاملات" in a or "TSETMC" in a or "trade_history" in a for a in verdict.remedial_actions)


def test_judge_agent_rejects_missing_social_sentiment(tmp_path):
    """Missing social_sentiment.json causes Pillar 3 failure and remediation directive."""
    symbol_dir = tmp_path / "شپنا"
    symbol_dir.mkdir(parents=True)

    judge = JudgeAgent()
    verdict = judge.audit_symbol("شپنا", symbol_dir)

    assert verdict.is_approved is False
    assert verdict.status == "REJECTED"
    assert any("social_sentiment.json" in str(verdict.audit_details) or "social_sentiment" in a for a in verdict.remedial_actions)


def test_judge_agent_rejects_missing_educational_guide(tmp_path):
    """Missing educational explanations in technical report must be penalized and reported."""
    symbol_dir = tmp_path / "فملی"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "charts").mkdir(parents=True)

    (symbol_dir / "codal_reports" / "letters_index.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "market_data" / "trade_history.csv").write_text("date,close\n1405-06-11,1000", encoding="utf-8")
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text("{}", encoding="utf-8")
    (symbol_dir / "news" / "news_summary.md").write_text("# اخبار", encoding="utf-8")
    # Missing social_sentiment.json to ensure rejection and generation of remediation actions
    (symbol_dir / "fundamental_report.md").write_text("# بنیادی\nP/E, حاشیه سود", encoding="utf-8")

    # Technical report WITHOUT educational guide
    (symbol_dir / "technical_report.md").write_text("# تحلیل تکنیکال فملی\nقیمت در کانال صعودی قرار دارد و RSI برابر با 55 است.", encoding="utf-8")
    (symbol_dir / "charts" / "candlestick_overview.png").write_bytes(b"\x89PNG")
    (symbol_dir / "charts" / "indicators_momentum.png").write_bytes(b"\x89PNG")
    (symbol_dir / "charts" / "tape_reading_money_flow.png").write_bytes(b"\x89PNG")

    (symbol_dir / "final_recommendation.md").write_text("# توصیه\nامتیازدهی سه‌گانه", encoding="utf-8")
    (symbol_dir / "strategy_recommendation.json").write_text("{}", encoding="utf-8")

    judge = JudgeAgent()
    verdict = judge.audit_symbol("فملی", symbol_dir)

    assert verdict.is_approved is False
    assert verdict.status == "REJECTED"
    assert any("راهنمای آموزشی" in d for d in verdict.audit_details["pillar4_analytical_depth"]["defects"])
    assert any("راهنمای آموزشی" in a or "آموزش" in a for a in verdict.remedial_actions)


def test_judge_agent_accepts_string_path_and_generates_certificate(tmp_path):
    """Ensure audit_symbol accepts str as symbol_dir and outputs well-formed certificate."""
    symbol_dir = tmp_path / "خودرو"
    symbol_dir.mkdir(parents=True)

    judge = JudgeAgent()
    verdict = judge.audit_symbol("خودرو", str(symbol_dir))

    assert isinstance(verdict, JudgementVerdict)
    assert verdict.is_approved is False
    assert "خودرو" in verdict.certificate_markdown
    assert "alimohammadzadeh@ut.ac.ir" in verdict.certificate_markdown
    assert "| رکن ممیزی |" in verdict.certificate_markdown
