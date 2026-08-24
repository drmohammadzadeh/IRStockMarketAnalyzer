import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Calculates technical indicators for financial price time series."""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """Calculates trend, momentum, volatility, volume, and cloud indicators on OHLCV data.

        Args:
            df: DataFrame containing 'open', 'high', 'low', 'close', and 'volume' columns.

        Returns:
            DataFrame with all calculated indicators appended.
        """
        res = df.copy()
        if res.empty:
            return res

        c = res["close"]
        h = res["high"]
        l = res["low"]
        v = res["volume"]

        # EMAs
        res["ema20"] = c.ewm(span=20, adjust=False).mean()
        res["ema50"] = c.ewm(span=50, adjust=False).mean()
        res["ema100"] = c.ewm(span=100, adjust=False).mean()
        res["ema200"] = c.ewm(span=200, adjust=False).mean()

        # RSI (14) using Wilder's smoothing
        delta = c.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        gain_vals = gain.to_numpy(dtype=float)
        loss_vals = loss.to_numpy(dtype=float)
        n = len(res)
        avg_gain_vals = np.full(n, np.nan)
        avg_loss_vals = np.full(n, np.nan)

        if n >= 14:
            # First average gain/loss is SMA of first 14 periods (index 1 to 14, where index 0 has diff NaN/0)
            avg_gain_vals[13] = np.nanmean(gain_vals[:14])
            avg_loss_vals[13] = np.nanmean(loss_vals[:14])
            for i in range(14, n):
                avg_gain_vals[i] = (avg_gain_vals[i - 1] * 13 + gain_vals[i]) / 14
                avg_loss_vals[i] = (avg_loss_vals[i - 1] * 13 + loss_vals[i]) / 14

        rs = avg_gain_vals / (avg_loss_vals + 1e-10)
        res["rsi"] = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        ema12 = c.ewm(span=12, adjust=False).mean()
        ema26 = c.ewm(span=26, adjust=False).mean()
        res["macd"] = ema12 - ema26
        res["macd_signal"] = res["macd"].ewm(span=9, adjust=False).mean()
        res["macd_hist"] = res["macd"] - res["macd_signal"]

        # Bollinger Bands (20, 2)
        bb_mid = c.rolling(20).mean()
        bb_std = c.rolling(20).std()
        res["bb_upper"] = bb_mid + 2 * bb_std
        res["bb_lower"] = bb_mid - 2 * bb_std
        res["bb_mid"] = bb_mid

        # ATR (14)
        prev_close = c.shift(1)
        tr1 = h - l
        tr2 = (h - prev_close).abs()
        tr3 = (l - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["atr"] = tr.rolling(14).mean()

        # Ichimoku Kinko Hyo
        res["tenkan_sen"] = (h.rolling(9).max() + l.rolling(9).min()) / 2
        res["kijun_sen"] = (h.rolling(26).max() + l.rolling(26).min()) / 2
        res["senkou_span_a"] = ((res["tenkan_sen"] + res["kijun_sen"]) / 2).shift(26)
        res["senkou_span_b"] = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
        res["chikou_span"] = c.shift(-26)

        # Volume MA 20
        res["vol_ma20"] = v.rolling(20).mean()
        res["vol_surge"] = res["volume"] > (res["vol_ma20"] * 2)

        return res
