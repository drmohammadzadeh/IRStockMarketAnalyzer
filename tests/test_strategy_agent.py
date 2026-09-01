import json
from pathlib import Path
import pytest
from src.agents.strategy_agent import StrategyAgent


def test_strategy_agent_generates_recommendation(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir(parents=True)

    tech_metrics = {
        "current_price": 47500.0,
        "rsi": 55.0,
        "buyer_power": 2.5,
        "nearest_support": 46000.0,
        "nearest_resistance": 52000.0,
        "swing_high": 58000.0,
        "swing_low": 42000.0,
        "atr": 1200.0,
    }
    fund_metrics = {
        "fundamental_score": 8.5,
        "pe_ratio": 5.2,
        "ps_ratio": 0.8,
        "dividend_yield_pct": 12.0,
    }

    agent = StrategyAgent()
    res = agent.run("زهلال", symbol_dir, tech_metrics, fund_metrics)

    assert res["success"] is True
    assert res["symbol"] == "زهلال"
    assert (symbol_dir / "final_recommendation.md").exists()
    assert (symbol_dir / "strategy_recommendation.json").exists()

    content = (symbol_dir / "final_recommendation.md").read_text(encoding="utf-8")
    assert "جدول راهنمای معامله (Actionable Plan)" in content
    assert "راهبرد در ۳ افق زمانی" in content
    assert "شروط ابطال تحلیل" in content
    assert "مدیریت ریسک" in content
    assert res["verdict"] in [
        "خرید قوی (Strong Buy)",
        "خرید پله‌ای (Accumulate)",
        "نگهداری با رعایت حد ضرر (Hold)",
        "سیو سود / خروج (Sell / Exit)",
    ]

    plan = res["plan"]
    assert plan["current_price"] == 47500.0
    assert plan["stop_loss"] < 47500.0
    assert plan["target_1"] > 47500.0
    assert plan["target_2"] >= plan["target_1"]
    assert "short_term" in plan["horizons"]
    assert "mid_term" in plan["horizons"]
    assert "long_term" in plan["horizons"]


def test_strategy_agent_with_news_and_codal_context(tmp_path):
    symbol_dir = tmp_path / "فولاد"
    symbol_dir.mkdir(parents=True)

    news_dir = symbol_dir / "news"
    news_dir.mkdir(parents=True)
    (news_dir / "news_summary.md").write_text(
        "# اخبار نماد فولاد\n- افزایش چشمگیر صادرات و نرخ شمش در بورس کالا با تقاضای پایدار.",
        encoding="utf-8",
    )

    codal_dir = symbol_dir / "codal_reports"
    codal_dir.mkdir(parents=True)
    (codal_dir / "codal_summaries.md").write_text(
        "# گزارش کدال فولاد\n- رشد ۴۵ درصدی مبلغ فروش ماهانه نسبت به میانگین بهار.",
        encoding="utf-8",
    )

    tech_metrics = {
        "current_price": 6200.0,
        "rsi": 48.0,
        "buyer_power": 1.8,
        "nearest_support": 5900.0,
        "nearest_resistance": 7100.0,
        "swing_high": 7800.0,
        "swing_low": 5500.0,
        "atr": 180.0,
    }
    fund_metrics = {
        "fundamental_score": 9.0,
        "pe_ratio": 4.8,
        "ps_ratio": 1.1,
        "dividend_yield_pct": 16.5,
    }

    agent = StrategyAgent()
    res = agent.run("فولاد", symbol_dir, tech_metrics, fund_metrics)

    assert res["success"] is True
    assert res["verdict"] == "خرید قوی (Strong Buy)"
    content = (symbol_dir / "final_recommendation.md").read_text(encoding="utf-8")
    assert "فولاد" in content
    assert "ماتریس همگرایی تحلیلی" in content
    assert "صادرات" in content or "کدال" in content or "تقاضا" in content


def test_strategy_agent_sell_exit_scenario(tmp_path):
    symbol_dir = tmp_path / "شتران"
    symbol_dir.mkdir(parents=True)

    tech_metrics = {
        "current_price": 5000.0,
        "rsi": 84.0,
        "buyer_power": 0.55,
        "nearest_support": 3800.0,
        "nearest_resistance": 5150.0,
        "swing_high": 5200.0,
        "swing_low": 3500.0,
        "atr": 250.0,
    }
    fund_metrics = {
        "fundamental_score": 2.5,
        "pe_ratio": 14.5,
        "ps_ratio": 4.2,
        "dividend_yield_pct": 3.0,
    }

    agent = StrategyAgent()
    res = agent.run("شتران", str(symbol_dir), tech_metrics, fund_metrics)

    assert res["success"] is True
    assert res["verdict"] == "سیو سود / خروج (Sell / Exit)"
    assert res["plan"]["risk_reward_ratio"] < 1.5


def test_strategy_agent_hold_scenario(tmp_path):
    symbol_dir = tmp_path / "شستا"
    symbol_dir.mkdir(parents=True)

    tech_metrics = {
        "current_price": 1400.0,
        "rsi": 58.0,
        "buyer_power": 1.02,
        "nearest_support": 1340.0,
        "nearest_resistance": 1480.0,
        "swing_high": 1600.0,
        "swing_low": 1280.0,
        "atr": 35.0,
    }
    fund_metrics = {
        "fundamental_score": 5.8,
        "pe_ratio": 6.8,
        "ps_ratio": 1.6,
        "dividend_yield_pct": 10.0,
    }

    agent = StrategyAgent()
    res = agent.run("شستا", symbol_dir, tech_metrics, fund_metrics)

    assert res["success"] is True
    assert res["verdict"] == "نگهداری با رعایت حد ضرر (Hold)"


def test_strategy_agent_defaults_and_missing_inputs(tmp_path):
    symbol_dir = tmp_path / "خپارس"
    # Do not create subdirectories, test missing metrics
    agent = StrategyAgent()
    res = agent.run("خپارس", symbol_dir, None, None)

    assert res["success"] is True
    assert (symbol_dir / "final_recommendation.md").exists()
    assert (symbol_dir / "strategy_recommendation.json").exists()

    json_data = json.loads((symbol_dir / "strategy_recommendation.json").read_text(encoding="utf-8"))
    assert "verdict" in json_data
    assert "entry_zone" in json_data
    assert "stop_loss" in json_data


def test_strategy_agent_three_tier_scores(tmp_path):
    symbol_dir = tmp_path / "تلیسه"
    symbol_dir.mkdir(parents=True)

    tech_metrics = {
        "current_price": 10060.0,
        "rsi": 72.1,
        "buyer_power": 1.18,
        "nearest_support": 9054.0,
        "nearest_resistance": 10190.0,
        "swing_high": 11209.0,
        "swing_low": 8500.0,
        "atr": 355.0,
        "ema20": 9400.0,
        "ema50": 8900.0,
    }
    fund_metrics = {
        "fundamental_score": 5.5,
        "pe_ratio": 8.9,
        "ps_ratio": 2.7,
        "dividend_yield_pct": 8.5,
    }

    agent = StrategyAgent()
    res = agent.run("تلیسه", symbol_dir, tech_metrics, fund_metrics)

    assert res["success"] is True
    plan = res["plan"]
    assert "scoring" in plan
    scoring = plan["scoring"]
    assert 1.0 <= scoring["score_weighted"] <= 5.0
    assert 1.0 <= scoring["score_rules"] <= 5.0
    assert 1.0 <= scoring["score_horizon"] <= 5.0
    assert 1.0 <= scoring["score_final"] <= 5.0
    assert "stars" in scoring
    assert "table_markdown" in scoring

    content = (symbol_dir / "final_recommendation.md").read_text(encoding="utf-8")
    assert "جدول جامع امتیازدهی سه‌گانه توصیه خرید/فروش" in content
    assert "رویکرد ۱: مدل تجمیع وزنی چندعاملی" in content
    assert "رویکرد ۲: مدل درخت تصمیم و فیلترهای وتو" in content
    assert "رویکرد ۳: مدل همگرایی افق‌های زمانی و R/R" in content
    assert "امتیاز نهایی اجماع" in content

