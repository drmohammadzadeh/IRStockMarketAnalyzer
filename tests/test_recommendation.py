import pytest
from src.strategy.recommendation import StrategyEngine

def test_generate_recommendation_buy():
    tech_data = {
        "rsi": 42.0,
        "ema20_above_ema50": True,
        "nearest_support": 4500.0,
        "nearest_resistance": 5800.0,
        "swing_high": 6200.0,
        "swing_low": 4200.0,
        "buyer_power": 1.6
    }
    fund_data = {"pe_ratio": 5.2, "fundamental_score": 8.0, "dividend_yield_pct": 14.0}
    current_price = 4700.0
    atr = 150.0

    rec = StrategyEngine.generate_recommendation(tech_data, fund_data, current_price, atr)
    assert rec["overall_verdict"] in ["خرید قوی (Strong Buy)", "خرید پله‌ای (Accumulate)"]
    assert rec["stop_loss"] < current_price
    assert rec["target_1"] > current_price
    assert rec["risk_reward_ratio"] >= 1.5
    assert "short_term" in rec["horizons"]
    assert "mid_term" in rec["horizons"]
    assert "long_term" in rec["horizons"]
    assert rec["current_price"] == current_price
    assert "ریال" in rec["entry_zone"]


def test_generate_recommendation_sell_exit():
    tech_data = {
        "rsi": 82.0,
        "nearest_support": 3000.0,
        "nearest_resistance": 5100.0,
        "buyer_power": 0.6
    }
    fund_data = {"fundamental_score": 2.5}
    current_price = 5000.0
    atr = 200.0

    rec = StrategyEngine.generate_recommendation(tech_data, fund_data, current_price, atr)
    assert rec["overall_verdict"] == "سیو سود / خروج (Sell / Exit)"
    assert rec["stop_loss"] <= current_price
    assert rec["risk_reward_ratio"] < 1.0


def test_generate_recommendation_hold():
    tech_data = {
        "rsi": 60.0,
        "nearest_support": 4700.0,
        "nearest_resistance": 5200.0,
        "buyer_power": 1.0
    }
    fund_data = {"fundamental_score": 5.5}
    current_price = 5000.0
    atr = 100.0

    rec = StrategyEngine.generate_recommendation(tech_data, fund_data, current_price, atr)
    assert rec["overall_verdict"] == "نگهداری با رعایت حد ضرر (Hold)"


def test_generate_recommendation_accumulate():
    tech_data = {
        "rsi": 45.0,  # score +1
        "nearest_support": 4600.0,
        "nearest_resistance": 5500.0,  # reward = 500
        "buyer_power": 1.4  # score +2 -> total 3 (Accumulate)
    }
    fund_data = {"fundamental_score": 5.0}  # score 0
    current_price = 5000.0
    atr = 100.0  # stop = max(4600 - 50, 4650) = 4650 -> risk = 350 -> rr = 500/350 = 1.43 (score 0)

    rec = StrategyEngine.generate_recommendation(tech_data, fund_data, current_price, atr)
    assert rec["overall_verdict"] == "خرید پله‌ای (Accumulate)"


def test_generate_recommendation_defaults_and_edge_cases():
    # Empty dictionaries and zero ATR
    rec = StrategyEngine.generate_recommendation({}, {}, 1000.0, 0.0)
    assert rec["current_price"] == 1000.0
    assert rec["stop_loss"] < 1000.0
    assert rec["target_1"] > 1000.0
    assert "short_term" in rec["horizons"]
    assert "mid_term" in rec["horizons"]
    assert "long_term" in rec["horizons"]

    # When support is somehow higher than current_price
    rec_inv = StrategyEngine.generate_recommendation({"nearest_support": 1200.0}, {}, 1000.0, 50.0)
    assert rec_inv["stop_loss"] < 1000.0
    assert rec_inv["stop_loss"] == 950.0
