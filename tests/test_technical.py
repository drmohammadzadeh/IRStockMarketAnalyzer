import pytest
import pandas as pd
import numpy as np
from src.technical.indicators import TechnicalIndicators
from src.technical.levels import PriceLevels


def test_indicators_calculation():
    np.random.seed(42)
    closes = 1000 + np.cumsum(np.random.randn(100) * 10)
    highs = closes + 15
    lows = closes - 15
    opens = closes - 2
    vols = np.random.randint(100000, 5000000, 100)
    df = pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols})

    calc_df = TechnicalIndicators.calculate_all(df)
    assert "ema20" in calc_df.columns
    assert "ema50" in calc_df.columns
    assert "ema100" in calc_df.columns
    assert "ema200" in calc_df.columns
    assert "rsi" in calc_df.columns
    assert "macd" in calc_df.columns
    assert "macd_signal" in calc_df.columns
    assert "macd_hist" in calc_df.columns
    assert "bb_upper" in calc_df.columns
    assert "bb_mid" in calc_df.columns
    assert "bb_lower" in calc_df.columns
    assert "tenkan_sen" in calc_df.columns
    assert "kijun_sen" in calc_df.columns
    assert "senkou_span_a" in calc_df.columns
    assert "senkou_span_b" in calc_df.columns
    assert "chikou_span" in calc_df.columns
    assert "atr" in calc_df.columns
    assert "vol_ma20" in calc_df.columns
    assert "vol_surge" in calc_df.columns
    assert 0 <= calc_df["rsi"].dropna().iloc[-1] <= 100


def test_fibonacci_and_pivot_levels():
    df = pd.DataFrame({
        "high": [1000, 1200, 1500, 1400, 1300],
        "low": [800, 950, 1100, 1050, 1000],
        "close": [950, 1150, 1450, 1250, 1100]
    })
    levels = PriceLevels.find_key_levels(df)
    assert "fibonacci" in levels
    assert levels["swing_high"] == 1500
    assert levels["swing_low"] == 800
    assert levels["fibonacci"]["fib_0.0"] == 1500
    assert levels["fibonacci"]["fib_1.0"] == 800
    assert levels["fibonacci"]["fib_0.618"] == round(1500 - 0.618 * 700, 2)
    assert levels["nearest_support"] == 1067.4  # fib_0.618 (1067.4) is max fib < 1100
    assert levels["nearest_resistance"] == 1150.0  # fib_0.5 (1150.0) is min fib > 1100


def test_levels_edge_cases():
    # When price is above all fib levels (e.g. latest close == swing high)
    df_high = pd.DataFrame({
        "high": [100, 200],
        "low": [50, 100],
        "close": [80, 200]
    })
    levels_high = PriceLevels.find_key_levels(df_high)
    assert levels_high["nearest_resistance"] == 200.0

    # When price is below all fib levels (e.g. latest close == swing low)
    df_low = pd.DataFrame({
        "high": [200, 150],
        "low": [100, 50],
        "close": [120, 50]
    })
    levels_low = PriceLevels.find_key_levels(df_low)
    assert levels_low["nearest_support"] == 50.0


def test_rsi_constant_price():
    df = pd.DataFrame({
        "open": [100] * 30,
        "high": [100] * 30,
        "low": [100] * 30,
        "close": [100] * 30,
        "volume": [1000] * 30
    })
    calc_df = TechnicalIndicators.calculate_all(df)
    # When price doesn't change, avg_gain=0, avg_loss=0 -> rs=0 -> rsi=0
    assert calc_df["rsi"].iloc[-1] == 0.0
