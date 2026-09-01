import pytest
from pathlib import Path
from src.reporting.markdown_generator import ReportGenerator


def test_generate_markdown_reports(tmp_path):
    symbol_dir = tmp_path / "سهام" / "زهلال"
    symbol_dir.mkdir(parents=True)

    tech_data = {
        "rsi": 45.0,
        "ema20": 4600.0,
        "nearest_support": 4400.0,
        "nearest_resistance": 5200.0,
        "buyer_power": 1.45,
    }
    fund_data = {
        "pe_ratio": 5.4,
        "ps_ratio": 0.8,
        "pb_ratio": 2.1,
        "fundamental_score": 8.0,
        "dividend_yield_pct": 12.0,
    }
    rec_data = {
        "overall_verdict": "خرید پله‌ای (Accumulate)",
        "action_desc": "ارزندگی مطلوب",
        "current_price": 4700.0,
        "entry_zone": "4,600 تا 4,800 ریال",
        "target_1": 5200.0,
        "target_2": 6000.0,
        "stop_loss": 4350.0,
        "risk_reward_ratio": 2.1,
        "horizons": {
            "short_term": {
                "title": "کوتاه‌مدت",
                "strategy": "نوسان‌گیری",
                "target": 5200.0,
                "expected_return_pct": 10.6,
                "stop_loss": 4350.0,
                "risk_pct": 7.4,
            },
            "mid_term": {
                "title": "میان‌مدت",
                "strategy": "رشد تولید",
                "target": 6000.0,
                "expected_return_pct": 27.6,
                "stop_loss": 4200.0,
                "risk_pct": 10.6,
            },
            "long_term": {
                "title": "بلندمدت",
                "strategy": "دید مجمعی",
                "target": 7500.0,
                "expected_return_pct": 59.5,
                "stop_loss": 4000.0,
                "risk_pct": 14.8,
            },
        },
    }

    files = ReportGenerator.generate_all_reports(
        "زهلال", symbol_dir, tech_data, fund_data, rec_data, []
    )

    assert "fundamental" in files
    assert "technical" in files
    assert "recommendation" in files

    fund_file = symbol_dir / "fundamental_report.md"
    tech_file = symbol_dir / "technical_report.md"
    rec_file = symbol_dir / "final_recommendation.md"

    assert fund_file.exists()
    assert tech_file.exists()
    assert rec_file.exists()

    fund_text = fund_file.read_text(encoding="utf-8")
    assert "گزارش تحلیلی بنیادی نماد زهلال" in fund_text
    assert "5.4" in fund_text
    assert "8" in fund_text
    assert "ارزنده" in fund_text

    tech_text = tech_file.read_text(encoding="utf-8")
    assert "گزارش تحلیلی تکنیکال و تابلوخوانی نماد زهلال" in tech_text
    assert "4,700" in tech_text
    assert "45.0" in tech_text
    assert "ورود پول هوشمند" in tech_text

    rec_text = rec_file.read_text(encoding="utf-8")
    assert "جمع‌بندی تحلیلی و پیشنهاد معاملاتی نماد زهلال" in rec_text
    assert "خرید پله‌ای (Accumulate)" in rec_text
    assert "4,600 تا 4,800 ریال" in rec_text
    assert "5,200" in rec_text
    assert "4,350" in rec_text


def test_generate_markdown_reports_handles_empty_or_none_data(tmp_path):
    symbol_dir = tmp_path / "reports"
    files = ReportGenerator.generate_all_reports("فولاد", symbol_dir, {}, {}, {}, [])

    assert (symbol_dir / "fundamental_report.md").exists()
    assert (symbol_dir / "technical_report.md").exists()
    assert (symbol_dir / "final_recommendation.md").exists()


def test_generate_markdown_reports_accepts_str_path(tmp_path):
    str_dir = str(tmp_path / "str_reports")
    files = ReportGenerator.generate_all_reports(
        "شستا", str_dir, {"rsi": 80.0}, {"pe_ratio": 12.0}, {"current_price": 1000.0}, None
    )

    assert Path(files["fundamental"]).exists()
    assert Path(files["technical"]).exists()
    assert Path(files["recommendation"]).exists()


def test_generate_portfolio_summary_table():
    sample_stocks = [
        {
            "symbol": "تابان",
            "name": "گروه پتروشیمی تابان فردا",
            "score_weighted": 4.8,
            "score_rules": 5.0,
            "score_horizon": 4.9,
            "score_final": 4.9,
            "stars": "★★★★★",
            "badge": "🚀 خرید قاطع (Strong Buy)",
            "rationale": "نسبت P/NAV حدود ۴۰٪، تخفیف ۶۰٪ در عرضه اولیه",
        },
        {
            "symbol": "تلیسه",
            "name": "دامداری تلیسه نمونه",
            "score_weighted": 3.2,
            "score_rules": 3.0,
            "score_horizon": 3.1,
            "score_final": 3.1,
            "stars": "★★★☆☆",
            "badge": "🟡 نگهداری (Hold)",
            "rationale": "سودآوری عملیاتی مطلوب، قیمت منصفانه",
        },
    ]

    table_md = ReportGenerator.generate_portfolio_summary_table(sample_stocks)
    assert "| نماد |" in table_md
    assert "تابان" in table_md
    assert "تلیسه" in table_md
    assert "4.9" in table_md
    assert "3.1" in table_md
    assert "Strong Buy" in table_md
    assert "Hold" in table_md

