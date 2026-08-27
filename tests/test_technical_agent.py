import json
from pathlib import Path
import pandas as pd
import pytest
from src.agents.technical_agent import TechnicalAnalystAgent


def test_technical_agent_generates_deep_report(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir(parents=True)
    mkt_dir = symbol_dir / "market_data"
    mkt_dir.mkdir()

    dates = pd.date_range("2026-01-01", periods=100)
    df = pd.DataFrame({
        "date": dates,
        "open": [4000.0 + i * 5 for i in range(100)],
        "high": [4050.0 + i * 5 for i in range(100)],
        "low": [3950.0 + i * 5 for i in range(100)],
        "close": [4020.0 + i * 5 for i in range(100)],
        "volume": [1000000.0] * 100,
    })
    df.to_csv(mkt_dir / "trade_history.csv", index=False)

    agent = TechnicalAnalystAgent()
    res = agent.run("زهلال", symbol_dir)
    assert res["success"] is True
    assert (symbol_dir / "technical_report.md").exists()

    content = (symbol_dir / "technical_report.md").read_text(encoding="utf-8")
    assert "تحلیل ساختار روند و امواج" in content
    assert "تحلیل سیستم معاملاتی ایچیموکو" in content
    assert "اسیلاتورهای تکانه و واگرایی‌ها" in content
    assert "ترازهای فیبوناچی" in content
    assert "تابلوخوانی و رفتارشناسی حقیقی/حقوقی" in content
    assert (symbol_dir / "charts" / "candlestick_overview.png").exists()
    assert (symbol_dir / "charts" / "indicators_momentum.png").exists()
    assert (symbol_dir / "charts" / "tape_reading_money_flow.png").exists()

    # Check metrics
    metrics = res.get("metrics", {})
    assert "price" in metrics
    assert "rsi" in metrics
    assert "ema20" in metrics
    assert "nearest_support" in metrics
    assert "nearest_resistance" in metrics
    assert "swing_high" in metrics
    assert "swing_low" in metrics
    assert "atr" in metrics
    assert "buyer_power" in metrics


def test_technical_agent_with_orderbook_tape(tmp_path):
    symbol_dir = tmp_path / "فولاد"
    symbol_dir.mkdir(parents=True)
    mkt_dir = symbol_dir / "market_data"
    mkt_dir.mkdir()

    dates = pd.date_range("2026-01-01", periods=100)
    df = pd.DataFrame({
        "date": dates,
        "open": [5000.0 + (i % 10) * 10 for i in range(100)],
        "high": [5100.0 + (i % 10) * 10 for i in range(100)],
        "low": [4900.0 + (i % 10) * 10 for i in range(100)],
        "close": [5050.0 + (i % 10) * 10 for i in range(100)],
        "volume": [2000000.0] * 100,
    })
    df.to_csv(mkt_dir / "trade_history.csv", index=False)

    tape_data = {
        "buy_real_count": 50,
        "buy_legal_count": 2,
        "sell_real_count": 100,
        "sell_legal_count": 5,
        "buy_real_vol": 1000000.0,
        "buy_legal_vol": 200000.0,
        "sell_real_vol": 1000000.0,
        "sell_legal_vol": 200000.0,
        "buy_real_capita": 20000.0,
        "sell_real_capita": 10000.0,
        "buyer_power": 2.0,
    }
    (mkt_dir / "orderbook_tape.json").write_text(json.dumps(tape_data, ensure_ascii=False), encoding="utf-8")

    agent = TechnicalAnalystAgent()
    res = agent.run("فولاد", symbol_dir)
    assert res["success"] is True
    assert res["metrics"]["buyer_power"] == 2.0

    content = (symbol_dir / "technical_report.md").read_text(encoding="utf-8")
    assert "2.00" in content or "2.0" in content


def test_technical_agent_handles_empty_history(tmp_path):
    symbol_dir = tmp_path / "شستا"
    symbol_dir.mkdir(parents=True)
    mkt_dir = symbol_dir / "market_data"
    mkt_dir.mkdir()
    (mkt_dir / "trade_history.csv").write_text("date,open,high,low,close,volume\n", encoding="utf-8")

    agent = TechnicalAnalystAgent()
    res = agent.run("شستا", symbol_dir)
    assert res["success"] is True
    assert (symbol_dir / "technical_report.md").exists()
    content = (symbol_dir / "technical_report.md").read_text(encoding="utf-8")
    assert "داده‌های سابقه قیمتی" in content or "شستا" in content


def test_technical_agent_handles_missing_market_data_dir(tmp_path):
    symbol_dir = tmp_path / "خودرو"
    # Do not create market_data dir

    agent = TechnicalAnalystAgent()
    res = agent.run("خودرو", symbol_dir)
    assert res["success"] is True
    assert (symbol_dir / "technical_report.md").exists()
