import pytest
import pandas as pd
from src.data.validator import DataValidator, ValidationResult


def test_validate_healthy_data():
    dates = pd.date_range("2026-01-01", periods=100)
    df = pd.DataFrame({
        "date": dates,
        "open": [1000.0] * 100,
        "high": [1050.0] * 100,
        "low": [980.0] * 100,
        "close": [1020.0] * 100,
        "last": [1020.0] * 100,
        "volume": [500000.0] * 100,
        "value": [510000000.0] * 100,
    })
    tsetmc_data = {
        "symbol": "زهلال",
        "success": True,
        "history": df,
        "client_type": {"buyer_power": 1.5},
    }
    codal_data = {
        "symbol": "زهلال",
        "success": True,
        "letters_count": 5,
        "categorized": {"financial_statements": [{"Title": "گزارش ۶ ماهه"}]},
    }

    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert isinstance(val, ValidationResult)
    assert val.is_valid is True
    assert val.candles_count == 100
    assert val.latest_close == 1020.0
    assert len(val.warnings) == 0
    assert len(val.errors) == 0
    assert val.metrics_summary["client_power"] == 1.5
    assert val.metrics_summary["codal_letters_count"] == 5


def test_validate_empty_history():
    tsetmc_data = {"symbol": "زهلال", "success": False, "history": pd.DataFrame()}
    codal_data = {"symbol": "زهلال", "success": True}
    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert val.is_valid is False
    assert "No price history available from TSETMC" in val.errors


def test_validate_none_or_missing_history():
    tsetmc_data = {"symbol": "زهلال", "success": False, "history": None}
    val = DataValidator.validate_all(tsetmc_data, {})
    assert val.is_valid is False
    assert "No price history available from TSETMC" in val.errors

    val_empty_dict = DataValidator.validate_all({}, {})
    assert val_empty_dict.is_valid is False
    assert "No price history available from TSETMC" in val_empty_dict.errors


def test_validate_short_history_warning():
    dates = pd.date_range("2026-01-01", periods=20)
    df = pd.DataFrame({
        "date": dates,
        "open": [1000.0] * 20,
        "high": [1050.0] * 20,
        "low": [980.0] * 20,
        "close": [1020.0] * 20,
        "last": [1020.0] * 20,
        "volume": [500000.0] * 20,
        "value": [510000000.0] * 20,
    })
    tsetmc_data = {"symbol": "زهلال", "success": True, "history": df}
    codal_data = {"symbol": "زهلال", "success": True}

    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert val.is_valid is True
    assert val.candles_count == 20
    assert any("Short price history (20 candles)" in w for w in val.warnings)


def test_validate_non_positive_prices():
    dates = pd.date_range("2026-01-01", periods=50)
    df = pd.DataFrame({
        "date": dates,
        "open": [1000.0] * 50,
        "high": [1050.0] * 50,
        "low": [980.0] * 50,
        "close": [1020.0] * 50,
        "last": [1020.0] * 50,
        "volume": [500000.0] * 50,
        "value": [510000000.0] * 50,
    })
    df.loc[10, "close"] = 0.0
    df.loc[20, "low"] = -5.0

    tsetmc_data = {"symbol": "زهلال", "success": True, "history": df}
    codal_data = {"symbol": "زهلال", "success": True}

    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert val.is_valid is False
    assert any("Found 2 candles with non-positive prices." in e for e in val.errors)


def test_validate_high_less_than_low():
    dates = pd.date_range("2026-01-01", periods=50)
    df = pd.DataFrame({
        "date": dates,
        "open": [1000.0] * 50,
        "high": [1050.0] * 50,
        "low": [980.0] * 50,
        "close": [1020.0] * 50,
        "last": [1020.0] * 50,
        "volume": [500000.0] * 50,
        "value": [510000000.0] * 50,
    })
    df.loc[5, "high"] = 900.0
    df.loc[5, "low"] = 1000.0

    tsetmc_data = {"symbol": "زهلال", "success": True, "history": df}
    codal_data = {"symbol": "زهلال", "success": True}

    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert val.is_valid is False
    assert any("Found 1 candles where High < Low." in e for e in val.errors)


def test_validate_halted_streak_zero_volume():
    dates = pd.date_range("2026-01-01", periods=50)
    df = pd.DataFrame({
        "date": dates,
        "open": [1000.0] * 50,
        "high": [1050.0] * 50,
        "low": [980.0] * 50,
        "close": [1020.0] * 50,
        "last": [1020.0] * 50,
        "volume": [500000.0] * 50,
        "value": [510000000.0] * 50,
    })
    df.loc[46:, "volume"] = 0.0

    tsetmc_data = {"symbol": "زهلال", "success": True, "history": df}
    codal_data = {"symbol": "زهلال", "success": True}

    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert val.is_valid is True
    assert any("zero trading volume for recent sessions" in w for w in val.warnings)


def test_validate_default_client_power_and_letters_count():
    dates = pd.date_range("2026-01-01", periods=40)
    df = pd.DataFrame({
        "date": dates,
        "open": [1000.0] * 40,
        "high": [1050.0] * 40,
        "low": [980.0] * 40,
        "close": [1020.0] * 40,
        "last": [1020.0] * 40,
        "volume": [500000.0] * 40,
        "value": [510000000.0] * 40,
    })
    tsetmc_data = {"symbol": "زهلال", "success": True, "history": df}
    codal_data = {"symbol": "زهلال", "success": True}

    val = DataValidator.validate_all(tsetmc_data, codal_data)
    assert val.metrics_summary["client_power"] == 1.0
    assert val.metrics_summary["codal_letters_count"] == 0
