import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from src.technical.indicators import TechnicalIndicators
from src.technical.chart_generator import ChartGenerator, fa_text


def test_generate_charts(tmp_path):
    dates = pd.date_range("2026-01-01", periods=60)
    closes = 1000 + np.cumsum(np.random.randn(60) * 10)
    df = pd.DataFrame({
        "date": dates,
        "open": closes - 2,
        "high": closes + 10,
        "low": closes - 10,
        "close": closes,
        "volume": np.random.randint(100000, 1000000, 60),
    })
    calc_df = TechnicalIndicators.calculate_all(df)
    charts_dir = tmp_path / "charts"

    generated = ChartGenerator.generate_all_charts(calc_df, "زهلال", charts_dir)
    assert len(generated) == 3
    for path in generated:
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0


def test_fa_text():
    text = "زهلال"
    reshaped = fa_text(text)
    assert isinstance(reshaped, str)
    assert len(reshaped) > 0


def test_generate_charts_with_missing_columns(tmp_path):
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=20),
        "open": [100.0] * 20,
        "high": [105.0] * 20,
        "low": [95.0] * 20,
        "close": [102.0] * 20,
        "volume": [50000] * 20,
    })
    charts_dir = tmp_path / "charts_minimal"
    generated = ChartGenerator.generate_all_charts(df, "تست", str(charts_dir))
    assert len(generated) == 3
    for path in generated:
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0
