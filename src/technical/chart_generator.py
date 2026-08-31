from pathlib import Path
from typing import List, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import arabic_reshaper

    def fa_text(text: str) -> str:
        """Reshapes Persian/Arabic text for correct cursive display in matplotlib."""
        if not text:
            return text
        return arabic_reshaper.reshape(text)
except ImportError:

    def fa_text(text: str) -> str:
        """Fallback when arabic_reshaper is unavailable."""
        return text

# Configure high-quality Persian/Arabic fonts for Matplotlib
plt.rcParams["font.sans-serif"] = ["Tahoma", "Segoe UI", "B Nazanin", "Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False


class ChartGenerator:
    """Generates visual charts with Persian typography and technical indicator overlays."""

    @staticmethod
    def generate_all_charts(
        df: pd.DataFrame, symbol: str, output_dir: Union[str, Path]
    ) -> List[Path]:
        """Generates all 3 analysis charts and saves them to output_dir.

        Args:
            df: DataFrame containing OHLCV and indicator data.
            symbol: Ticker symbol name in Persian.
            output_dir: Directory where charts will be saved.

        Returns:
            List of Path objects for the generated PNG chart files.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        created = []

        # 1. Candlestick & Overlays Overview
        p1 = out_dir / "candlestick_overview.png"
        ChartGenerator._plot_candlestick_overview(df, symbol, p1)
        created.append(p1)

        # 2. Indicators & Momentum (RSI & MACD)
        p2 = out_dir / "indicators_momentum.png"
        ChartGenerator._plot_indicators(df, symbol, p2)
        created.append(p2)

        # 3. Tape Reading & Money Flow
        p3 = out_dir / "tape_reading_money_flow.png"
        ChartGenerator._plot_money_flow(df, symbol, p3)
        created.append(p3)

        return created

    @staticmethod
    def _plot_candlestick_overview(
        df: pd.DataFrame, symbol: str, out_path: Path
    ) -> None:
        """Plots price trends, EMAs, Bollinger Bands, and Volume bars."""
        subset = df.tail(80).reset_index(drop=True)
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 7), gridspec_kw={"height_ratios": [3, 1]}, dpi=150
        )

        if df.empty or "close" not in df.columns:
            ax1.text(0.5, 0.5, fa_text(f"نماد {symbol} - در مرحله عرضه اولیه / سابقه معاملاتی ثبت نشده است"),
                     ha="center", va="center", transform=ax1.transAxes, fontsize=13, color="#555555")
            ax2.text(0.5, 0.5, fa_text("اطلاعات حجم معاملات پس از شروع دادوستد نمایش داده می‌شود"),
                     ha="center", va="center", transform=ax2.transAxes, fontsize=11, color="#777777")
            ax1.set_title(fa_text(f"نمودار روند قیمتی نماد {symbol} (عرضه اولیه)"), fontsize=14, fontweight="bold")
            ax1.grid(True, alpha=0.3)
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(out_path)
            plt.close(fig)
            return

        # Plot price and EMAs
        if "close" in subset.columns:
            ax1.plot(
                subset.index,
                subset["close"],
                label=fa_text("قیمت پایانی"),
                color="#1f77b4",
                lw=1.8,
            )
        if "ema20" in subset.columns:
            ax1.plot(
                subset.index,
                subset["ema20"],
                label="EMA 20",
                color="#ff7f0e",
                lw=1.2,
                ls="--",
            )
        if "ema50" in subset.columns:
            ax1.plot(
                subset.index,
                subset["ema50"],
                label="EMA 50",
                color="#2ca02c",
                lw=1.2,
                ls="--",
            )
        if "bb_upper" in subset.columns and "bb_lower" in subset.columns:
            ax1.fill_between(
                subset.index,
                subset["bb_lower"],
                subset["bb_upper"],
                color="gray",
                alpha=0.15,
                label=fa_text("باند بولینگر"),
            )

        ax1.set_title(
            fa_text(f"نمودار روند قیمتی و میانگین‌های متحرک نماد {symbol}"),
            fontsize=14,
            fontweight="bold",
        )
        ax1.set_ylabel(fa_text("قیمت (ریال)"))
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="upper left")

        # Volume bars
        if "volume" in subset.columns:
            if "open" in subset.columns and "close" in subset.columns:
                colors = [
                    "#2ca02c"
                    if subset["close"].iloc[i] >= subset["open"].iloc[i]
                    else "#d62728"
                    for i in range(len(subset))
                ]
            else:
                colors = "#1f77b4"
            ax2.bar(
                subset.index,
                subset["volume"],
                color=colors,
                alpha=0.7,
                label=fa_text("حجم معاملات"),
            )
        if "vol_ma20" in subset.columns:
            ax2.plot(
                subset.index,
                subset["vol_ma20"],
                color="blue",
                lw=1.2,
                label=fa_text("میانگین حجم ۲۰ روزه"),
            )
        ax2.set_ylabel(fa_text("حجم"))
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="upper left")

        plt.tight_layout()
        plt.savefig(out_path)
        plt.close(fig)

    @staticmethod
    def _plot_indicators(df: pd.DataFrame, symbol: str, out_path: Path) -> None:
        """Plots momentum indicators (RSI and MACD)."""
        subset = df.tail(80).reset_index(drop=True)
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 6), sharex=True, dpi=150
        )

        if df.empty or "rsi" not in df.columns:
            ax1.text(0.5, 0.5, fa_text(f"اسیلاتورهای تکانه نماد {symbol} پس از آغاز معاملات محاسبه خواهند شد"),
                     ha="center", va="center", transform=ax1.transAxes, fontsize=12, color="#555555")
            ax2.text(0.5, 0.5, fa_text("هیستوگرام و خط سیگنال MACD نیازمند ثبت سوابق معاملاتی است"),
                     ha="center", va="center", transform=ax2.transAxes, fontsize=11, color="#777777")
            ax1.set_title(fa_text(f"اسیلاتورهای تکانه نماد {symbol} (عرضه اولیه)"), fontsize=13, fontweight="bold")
            ax1.grid(True, alpha=0.3)
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(out_path)
            plt.close(fig)
            return

        # RSI
        if "rsi" in subset.columns:
            ax1.plot(
                subset.index, subset["rsi"], color="purple", lw=1.8, label="RSI (14)"
            )
            ax1.axhline(
                70, color="red", ls="--", alpha=0.6, label=fa_text("اشباع خرید (70)")
            )
            ax1.axhline(
                30,
                color="green",
                ls="--",
                alpha=0.6,
                label=fa_text("اشباع فروش (30)"),
            )
            ax1.set_ylabel("RSI")
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc="upper left")
        ax1.set_title(
            fa_text(f"اسیلاتورهای تکانه (RSI و MACD) نماد {symbol}"),
            fontsize=13,
            fontweight="bold",
        )

        # MACD
        if "macd" in subset.columns and "macd_signal" in subset.columns:
            ax2.plot(
                subset.index, subset["macd"], color="blue", lw=1.5, label="MACD"
            )
            ax2.plot(
                subset.index,
                subset["macd_signal"],
                color="orange",
                lw=1.5,
                label="Signal",
            )
            if "macd_hist" in subset.columns:
                hist_colors = [
                    "green" if val >= 0 else "red" for val in subset["macd_hist"]
                ]
                ax2.bar(
                    subset.index,
                    subset["macd_hist"],
                    color=hist_colors,
                    alpha=0.5,
                    label="Histogram",
                )
            ax2.axhline(0, color="black", lw=0.8)
            ax2.set_ylabel("MACD")
            ax2.grid(True, alpha=0.3)
            ax2.legend(loc="upper left")

        plt.tight_layout()
        plt.savefig(out_path)
        plt.close(fig)

    @staticmethod
    def _plot_money_flow(df: pd.DataFrame, symbol: str, out_path: Path) -> None:
        """Plots cumulative money flow approximation."""
        subset = df.tail(80).reset_index(drop=True)
        fig, ax = plt.subplots(figsize=(12, 4.5), dpi=150)

        if df.empty or "close" not in df.columns:
            ax.text(0.5, 0.5, fa_text(f"روند جریان نقدینگی و قدرت خریداران نماد {symbol} پس از روز اول عرضه ثبت می‌شود"),
                    ha="center", va="center", transform=ax.transAxes, fontsize=12, color="#555555")
            ax.set_title(fa_text(f"جریان نقدینگی نماد {symbol} (عرضه اولیه)"), fontsize=13, fontweight="bold")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(out_path)
            plt.close(fig)
            return

        # Approximate flow based on price change * volume
        if "close" in subset.columns and "volume" in subset.columns:
            approx_flow = (
                subset["close"].pct_change().fillna(0)
                * subset["volume"]
                * subset["close"]
                / 1e10
            ).cumsum()
            ax.plot(
                subset.index,
                approx_flow,
                color="#008080",
                lw=2,
                label=fa_text("جریان نقدینگی تجمعی (میلیارد تومان)"),
            )
            ax.fill_between(subset.index, 0, approx_flow, color="#008080", alpha=0.2)
        ax.set_title(
            fa_text(f"روند جریان نقدینگی و قدرت خریداران نماد {symbol}"),
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel(fa_text("میلیارد تومان"))
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left")

        plt.tight_layout()
        plt.savefig(out_path)
        plt.close(fig)
