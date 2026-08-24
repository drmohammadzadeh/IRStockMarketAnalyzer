from typing import Any, Dict
import pandas as pd


class PriceLevels:
    """Computes technical price levels including Fibonacci retracements and support/resistance."""

    @staticmethod
    def find_key_levels(df: pd.DataFrame, lookback: int = 120) -> Dict[str, Any]:
        """Identifies key Fibonacci levels and nearest support and resistance levels.

        Args:
            df: DataFrame containing 'high', 'low', and 'close' columns.
            lookback: Lookback period for finding swing high and swing low (default: 120).

        Returns:
            Dictionary containing swing highs, lows, Fibonacci levels, and nearest support/resistance.
        """
        subset = df.tail(lookback)
        swing_high = float(subset["high"].max())
        swing_low = float(subset["low"].min())
        diff = swing_high - swing_low

        fib_levels = {
            "fib_0.0": swing_high,
            "fib_0.236": round(swing_high - 0.236 * diff, 2),
            "fib_0.382": round(swing_high - 0.382 * diff, 2),
            "fib_0.5": round(swing_high - 0.500 * diff, 2),
            "fib_0.618": round(swing_high - 0.618 * diff, 2),
            "fib_0.786": round(swing_high - 0.786 * diff, 2),
            "fib_1.0": swing_low,
        }

        latest_close = float(subset["close"].iloc[-1])
        supports = [v for k, v in fib_levels.items() if v < latest_close]
        resistances = [v for k, v in fib_levels.items() if v > latest_close]

        nearest_support = max(supports) if supports else swing_low
        nearest_resistance = min(resistances) if resistances else swing_high

        return {
            "swing_high": swing_high,
            "swing_low": swing_low,
            "fibonacci": fib_levels,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
        }
