import pandas as pd
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool
    candles_count: int = 0
    latest_date: str = ""
    latest_close: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)


class DataValidator:
    """Validator for extracted TSETMC and Codal stock data."""

    @staticmethod
    def validate_all(tsetmc_data: Dict[str, Any], codal_data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        metrics: Dict[str, Any] = {}

        if not isinstance(tsetmc_data, dict):
            errors.append("No price history available from TSETMC")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        df = tsetmc_data.get("history")
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            errors.append("No price history available from TSETMC")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        candles_count = len(df)
        if candles_count < 30:
            warnings.append(
                f"Short price history ({candles_count} candles). Some long-term indicators (EMA200) may be unavailable."
            )

        latest_row = df.iloc[-1]
        latest_close = float(latest_row.get("close", 0.0))
        latest_date = str(latest_row.get("date", ""))

        # Check for non-positive prices
        invalid_prices = df[(df["close"] <= 0) | (df["high"] <= 0) | (df["low"] <= 0)]
        if not invalid_prices.empty:
            errors.append(f"Found {len(invalid_prices)} candles with non-positive prices.")

        # Check high >= low
        broken_range = df[df["high"] < df["low"]]
        if not broken_range.empty:
            errors.append(f"Found {len(broken_range)} candles where High < Low.")

        # Check zero-volume streaks (halted symbol indicator)
        recent_zero_vols = (df["volume"].iloc[-5:] == 0).sum() if len(df) >= 5 else 0
        if recent_zero_vols >= 4:
            warnings.append("Symbol shows zero trading volume for recent sessions (possibly halted/closed).")

        metrics["latest_close"] = latest_close
        metrics["latest_date"] = latest_date
        metrics["candles_count"] = candles_count

        client_type = tsetmc_data.get("client_type")
        if isinstance(client_type, dict):
            metrics["client_power"] = client_type.get("buyer_power", 1.0)
        else:
            metrics["client_power"] = 1.0

        codal_dict = codal_data if isinstance(codal_data, dict) else {}
        metrics["codal_letters_count"] = codal_dict.get("letters_count", 0)

        return ValidationResult(
            is_valid=(len(errors) == 0),
            candles_count=candles_count,
            latest_date=latest_date,
            latest_close=latest_close,
            errors=errors,
            warnings=warnings,
            metrics_summary=metrics,
        )
