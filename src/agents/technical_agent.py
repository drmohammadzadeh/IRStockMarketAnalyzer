import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import jdatetime
import numpy as np
import pandas as pd

from src.technical.indicators import TechnicalIndicators
from src.technical.levels import PriceLevels
from src.technical.chart_generator import ChartGenerator


class TechnicalAnalystAgent:
    """Technical analysis and tape reading agent for Iranian stock market symbols."""

    def __init__(self):
        pass

    def _load_history(self, symbol_dir: Path) -> pd.DataFrame:
        """Loads and parses trade history CSV from market_data directory."""
        csv_file = symbol_dir / "market_data" / "trade_history.csv"
        if not csv_file.exists():
            return pd.DataFrame()

        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                return pd.DataFrame()

            # Ensure required numeric columns exist and are numeric
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    df[col] = 0.0

            df = df.dropna(subset=["close"])
            if df.empty:
                return pd.DataFrame()

            return df.reset_index(drop=True)
        except Exception:
            return pd.DataFrame()

    def _load_tape_data(self, symbol_dir: Path) -> Dict[str, Any]:
        """Loads client type and tape reading data from JSON."""
        json_file = symbol_dir / "market_data" / "orderbook_tape.json"
        if not json_file.exists():
            return {}

        try:
            content = json_file.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _detect_divergences(self, df: pd.DataFrame) -> Dict[str, str]:
        """Checks for price-RSI and price-MACD divergences in recent swings."""
        if len(df) < 20 or "rsi" not in df.columns:
            return {
                "rsi_divergence": "داده‌های کافی برای پایش واگرایی معتبر در دسترس نیست.",
                "macd_divergence": "داده‌های کافی برای پایش واگرایی مکدی در دسترس نیست.",
            }

        subset = df.tail(30).reset_index(drop=True)
        closes = subset["close"].to_numpy()
        rsis = subset["rsi"].to_numpy()
        macds = subset["macd"].to_numpy() if "macd" in subset.columns else np.zeros(len(subset))

        # Check lowest price points vs RSI/MACD (Bullish Divergence RD+)
        min_idx_1 = int(np.argmin(closes[:15]))
        min_idx_2 = int(np.argmin(closes[15:])) + 15

        rsi_div = "واگرایی واضحی در اسیلاتور RSI مشاهده نشده و تکانه همگام با نوسانات قیمت است."
        if closes[min_idx_2] < closes[min_idx_1] and rsis[min_idx_2] > rsis[min_idx_1] + 2:
            rsi_div = "تشکیل واگرایی مثبت معمولی (RD+) در کف‌های قیمتی (سیگنال بالقوه بازگشت صعودی)."
        elif closes[min_idx_2] > closes[min_idx_1] and rsis[min_idx_2] < rsis[min_idx_1] - 2:
            rsi_div = "تشکیل واگرایی منفی معمولی (RD-) در سقف‌های قیمتی (هشدار ضعف مومنتوم خریداران)."

        macd_div = "هیستوگرام و خط مکدی در تعادل با رفتار روند قیمتی نوسان می‌کنند."
        if closes[min_idx_2] < closes[min_idx_1] and macds[min_idx_2] > macds[min_idx_1]:
            macd_div = "تشکیل واگرایی مثبت مکدی (تضعیف مومنتوم نزولی و احتمال چرخش روند به سمت بالا)."
        elif closes[min_idx_2] > closes[min_idx_1] and macds[min_idx_2] < macds[min_idx_1]:
            macd_div = "تشکیل واگرایی منفی مکدی (کاهش انرژی تقاضا در قله‌های قیمتی)."

        return {
            "rsi_divergence": rsi_div,
            "macd_divergence": macd_div,
        }

    def _build_report_content(
        self,
        symbol: str,
        df: pd.DataFrame,
        levels: Dict[str, Any],
        tape_data: Dict[str, Any],
        divergences: Dict[str, str],
        chart_paths: List[Path],
    ) -> str:
        """Constructs an exhaustive, multi-sectional Persian technical report."""
        try:
            now_shamsi = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")
        except Exception:
            now_shamsi = "نامشخص"

        if df.empty:
            return f"""# گزارش تحلیلی جامع تکنیکال و تابلوخوانی نماد {symbol}

**تاریخ گزارش:** {now_shamsi}  
**وضعیت:** داده‌های سابقه قیمتی معتبر برای نماد {symbol} یافت نشد یا در سامانه ثبت نگردیده است.

---
## تحلیل ساختار روند و امواج
- داده‌های معاملاتی برای ترسیم روند در دسترس نیست.

## تحلیل سیستم معاملاتی ایچیموکو
- سیستم ایچیموکو نیازمند حداقل ۵۲ دوره معاملاتی است.

## اسیلاتورهای تکانه و واگرایی‌ها
- اسیلاتورهای RSI و MACD نیازمند دیتای معتبر قیمتی هستند.

## ترازهای فیبوناچی
- ترازهای فیبوناچی قابل محاسبه نمی‌باشند.

## تابلوخوانی و رفتارشناسی حقیقی/حقوقی
- داده‌های تابلوی معاملات دریافت نگردید.
"""

        last_row = df.iloc[-1]
        current_price = float(last_row.get("close", 0.0))
        open_price = float(last_row.get("open", current_price))
        high_price = float(last_row.get("high", current_price))
        low_price = float(last_row.get("low", current_price))
        vol = float(last_row.get("volume", 0.0))
        vol_ma = float(last_row.get("vol_ma20", vol)) if pd.notna(last_row.get("vol_ma20")) else vol

        ema20 = float(last_row.get("ema20", current_price)) if pd.notna(last_row.get("ema20")) else current_price
        ema50 = float(last_row.get("ema50", current_price)) if pd.notna(last_row.get("ema50")) else current_price
        ema100 = float(last_row.get("ema100", current_price)) if pd.notna(last_row.get("ema100")) else current_price
        ema200 = float(last_row.get("ema200", current_price)) if pd.notna(last_row.get("ema200")) else current_price

        rsi = float(last_row.get("rsi", 50.0)) if pd.notna(last_row.get("rsi")) else 50.0
        macd = float(last_row.get("macd", 0.0)) if pd.notna(last_row.get("macd")) else 0.0
        macd_signal = float(last_row.get("macd_signal", 0.0)) if pd.notna(last_row.get("macd_signal")) else 0.0
        macd_hist = float(last_row.get("macd_hist", 0.0)) if pd.notna(last_row.get("macd_hist")) else 0.0

        bb_upper = float(last_row.get("bb_upper", current_price)) if pd.notna(last_row.get("bb_upper")) else current_price
        bb_lower = float(last_row.get("bb_lower", current_price)) if pd.notna(last_row.get("bb_lower")) else current_price
        bb_mid = float(last_row.get("bb_mid", current_price)) if pd.notna(last_row.get("bb_mid")) else current_price
        atr = float(last_row.get("atr", 0.0)) if pd.notna(last_row.get("atr")) else 0.0

        tenkan = float(last_row.get("tenkan_sen", current_price)) if pd.notna(last_row.get("tenkan_sen")) else current_price
        kijun = float(last_row.get("kijun_sen", current_price)) if pd.notna(last_row.get("kijun_sen")) else current_price
        span_a = float(last_row.get("senkou_span_a", current_price)) if pd.notna(last_row.get("senkou_span_a")) else current_price
        span_b = float(last_row.get("senkou_span_b", current_price)) if pd.notna(last_row.get("senkou_span_b")) else current_price

        swing_high = float(levels.get("swing_high", current_price))
        swing_low = float(levels.get("swing_low", current_price))
        fibs = levels.get("fibonacci", {})
        nearest_support = float(levels.get("nearest_support", current_price * 0.95))
        nearest_resistance = float(levels.get("nearest_resistance", current_price * 1.05))

        # Tape metrics
        buyer_power = float(tape_data.get("buyer_power", 1.0))
        buy_real_capita = float(tape_data.get("buy_real_capita", 0.0))
        sell_real_capita = float(tape_data.get("sell_real_capita", 0.0))
        buy_real_vol = float(tape_data.get("buy_real_vol", 0.0))
        buy_legal_vol = float(tape_data.get("buy_legal_vol", 0.0))
        sell_real_vol = float(tape_data.get("sell_real_vol", 0.0))
        sell_legal_vol = float(tape_data.get("sell_legal_vol", 0.0))

        # Trend Structure Interpretation
        if current_price >= ema20 >= ema50:
            trend_desc = "صعودی تثبیت‌شده (قیمت بالاتر از میانگین‌های کوتاه و میان‌مدت قرار دارد)"
            trend_signal = "🟢 صعودی"
        elif current_price < ema20 < ema50:
            trend_desc = "نزولی / اصلاحی (قیمت پایین‌تر از میانگین‌های معتبر معامله می‌شود)"
            trend_signal = "🔴 نزولی"
        else:
            trend_desc = "خنثی / رنج (نوسان در محدوده متراکم میانگین‌های متحرک)"
            trend_signal = "🟡 خنثی"

        # Ichimoku Evaluation
        tk_cross = "تنکان‌سن بالای کیجون‌سن (سیگنال تقاطع صعودی TK Cross)" if tenkan >= kijun else "تنکان‌سن زیر کیجون‌سن (فشار اصلاحی کوتاه‌مدت)"
        if current_price > max(span_a, span_b):
            cloud_status = "قیمت بالای ابر کومو قرار دارد (موقعیت روند صعودی پرقدرت و حمایت ابر کومو)"
        elif current_price < min(span_a, span_b):
            cloud_status = "قیمت زیر ابر کومو قرار دارد (موقعیت روند نزولی و مقاومت سقف کومو)"
        else:
            cloud_status = "قیمت درون ابر کومو نوسان می‌کند (فاز تعادلی، خنثی و عدم قطعیت جهت حرکت)"

        # RSI Evaluation
        if rsi >= 70:
            rsi_eval = "اشباع خرید (احتمال شناسایی سود یا استراحت موقت روند)"
        elif rsi <= 30:
            rsi_eval = "اشباع فروش (تخلیه هیجان عرضه و پتانسیل بالای بازگشت تکنیکال)"
        elif 50 <= rsi < 70:
            rsi_eval = "تکانه مثبت و برتری نسبی خریداران"
        else:
            rsi_eval = "تکانه ضعیف و حرکت در فاز رنج منفی"

        # Tape reading evaluation
        if buyer_power >= 1.5:
            bp_eval = "قدرت خریدار بسیار عالی (ورود پول هوشمند و خرید قدرتمند توسط کدهای درشت حقیقی)"
        elif buyer_power >= 1.1:
            bp_eval = "برتری خریداران حقیقی بر فروشندگان"
        elif buyer_power <= 0.8:
            bp_eval = "برتری فروشندگان و فشار عرضه از سوی کدهای حقیقی"
        else:
            bp_eval = "تعادل نسبی میان قدرت خریدار و فروشنده"

        vol_surge_flag = vol > (vol_ma * 2) if vol_ma > 0 else False
        vol_desc = "ثبت حجم مشکوک و بیش از ۲ برابر میانگین ۲۰ روزه (نشانه‌ای از تحرکات مهم بازیگران)" if vol_surge_flag else "حجم معاملات در محدوده نرمال و نزدیک به میانگین دوره‌ای"

        lines = [
            f"# گزارش تحلیلی جامع تکنیکال و تابلوخوانی نماد {symbol}",
            f"**تاریخ تحلیل:** {now_shamsi}  ",
            f"**آخرین قیمت معاملاتی:** {current_price:,.0f} ریال | **دامنه روز:** {low_price:,.0f} تا {high_price:,.0f} ریال  ",
            f"**حجم معاملات آخرین روز:** {vol:,.0f} برگه سهم (میانگین ۲۰ روزه: {vol_ma:,.0f})",
            "",
            "---",
            "",
            "## ۱. تحلیل ساختار روند و امواج (Trend Structure & Wave Patterns)",
            f"- **وضعیت کلی روند:** {trend_signal} - {trend_desc}",
            f"- **سقف ماژور دوره (Swing High):** {swing_high:,.0f} ریال",
            f"- **کف ماژور دوره (Swing Low):** {swing_low:,.0f} ریال",
            f"- **دامنه نوسان واقعی (ATR 14):** {atr:,.0f} ریال",
            "",
            "### جدول میانگین‌های متحرک نمایی (Exponential Moving Averages)",
            "| شاخص میانگین | مقدار عددی (ریال) | فاصله با قیمت فعلی | موقعیت تکنیکال |",
            "| :--- | :--- | :--- | :--- |",
            f"| **EMA 20** | {ema20:,.0f} | {((current_price - ema20) / ema20 * 100):+.1f}% | {'حمایت پویا' if current_price >= ema20 else 'مقاومت نزدیک'} |",
            f"| **EMA 50** | {ema50:,.0f} | {((current_price - ema50) / ema50 * 100):+.1f}% | {'حمایت میان‌مدت' if current_price >= ema50 else 'مقاومت میان‌مدت'} |",
            f"| **EMA 100** | {ema100:,.0f} | {((current_price - ema100) / ema100 * 100):+.1f}% | حمایت / مقاومت تراز میانی |",
            f"| **EMA 200** | {ema200:,.0f} | {((current_price - ema200) / ema200 * 100):+.1f}% | مرز روند بلندمدت و استراتژیک |",
            "",
            "### وضعیت باندهای بولینگر (Bollinger Bands)",
            f"- **باند بالایی (Upper Band):** {bb_upper:,.0f} ریال",
            f"- **باند میانی (SMA 20):** {bb_mid:,.0f} ریال",
            f"- **باند پایینی (Lower Band):** {bb_lower:,.0f} ریال",
            f"- **عرض باند (Bandwidth):** {((bb_upper - bb_lower) / (bb_mid + 1e-6) * 100):.1f}% (سنجش میزان فشردگی نوسانات)",
            "",
            "---",
            "",
            "## ۲. تحلیل سیستم معاملاتی ایچیموکو (Ichimoku Kinko Hyo)",
            f"- **خط تنکان‌سن (Tenkan-sen 9):** {tenkan:,.0f} ریال",
            f"- **خط کیجون‌سن (Kijun-sen 26):** {kijun:,.0f} ریال",
            f"- **ابر کومو اسپن A (Senkou Span A):** {span_a:,.0f} ریال",
            f"- **ابر کومو اسپن B (Senkou Span B):** {span_b:,.0f} ریال",
            f"- **ارزیابی تقاطع خطوط:** {tk_cross}",
            f"- **موقعیت قیمت نسبت به ابر کومو:** {cloud_status}",
            "",
            "---",
            "",
            "## ۳. اسیلاتورهای تکانه و واگرایی‌ها (Momentum Oscillators & Divergences)",
            f"- **شاخص قدرت نسبی (RSI 14):** **{rsi:.1f}** ({rsi_eval})",
            f"- **مکدی (MACD 12,26,9):** {macd:.2f} | **خط سیگنال:** {macd_signal:.2f} | **هیستوگرام:** {macd_hist:.2f}",
            "",
            "### بررسی وضعیت واگرایی‌های تکنیکال (Divergence Analysis)",
            f"- **واگرایی در اسیلاتور RSI:** {divergences.get('rsi_divergence', '')}",
            f"- **واگرایی در اندیکاتور MACD:** {divergences.get('macd_divergence', '')}",
            "",
            "---",
            "",
            "## ۴. ترازهای فیبوناچی (Fibonacci Retracement & Expansion Levels)",
            f"مبنای محاسبه ترازهای فیبوناچی اصلاحی بر اساس آخرین موج حرکتی بین کف {swing_low:,.0f} و سقف {swing_high:,.0f} ریال:",
            "",
            "| نسبت فیبوناچی | سطح قیمتی (ریال) | فاصله با قیمت فعلی | نقش تکنیکال |",
            "| :--- | :--- | :--- | :--- |",
        ]

        fib_roles = {
            "fib_0.0": "سقف موج (Pivot High)",
            "fib_0.236": "حمایت / مقاومت اول اصلاحی (23.6%)",
            "fib_0.382": "تراز اصلاحی نرمال (38.2%)",
            "fib_0.5": "تراز میانی تعادلی (50.0%)",
            "fib_0.618": "تراز طلایی و پرتقاضا (61.8%)",
            "fib_0.786": "آخرین سد دفاعی روند (78.6%)",
            "fib_1.0": "کف موج (Pivot Low)",
        }

        for k in ["fib_0.0", "fib_0.236", "fib_0.382", "fib_0.5", "fib_0.618", "fib_0.786", "fib_1.0"]:
            if k in fibs:
                f_val = float(fibs[k])
                dist = ((current_price - f_val) / (f_val + 1e-6)) * 100
                role = fib_roles.get(k, "تراز تکنیکال")
                lines.append(f"| **{k.replace('fib_', '')}** | {f_val:,.0f} | {dist:+.1f}% | {role} |")

        lines.extend([
            "",
            f"- **نزدیک‌ترین سطح حمایت معتبر:** **{nearest_support:,.0f} ریال**",
            f"- **نزدیک‌ترین سطح مقاومت معتبر:** **{nearest_resistance:,.0f} ریال**",
            "",
            "---",
            "",
            "## ۵. تابلوخوانی و رفتارشناسی حقیقی/حقوقی (Tape Reading & Smart Money Flow)",
            f"- **نسبت قدرت خریدار به فروشنده:** **{buyer_power:.2f}** ({bp_eval})",
            f"- **سرانه خرید حقیقی:** {buy_real_capita:,.0f} سهم | **سرانه فروش حقیقی:** {sell_real_capita:,.0f} سهم",
            f"- **حجم خرید حقیقی:** {buy_real_vol:,.0f} سهم | **حجم خرید حقوقی:** {buy_legal_vol:,.0f} سهم",
            f"- **حجم فروش حقیقی:** {sell_real_vol:,.0f} سهم | **حجم فروش حقوقی:** {sell_legal_vol:,.0f} سهم",
            f"- **وضعیت حجم معاملات:** {vol_desc}",
            "",
            "---",
            "",
            "## ۶. نمودارهای تحلیل تکنیکال و بصری همراه با راهنمای تحلیلی و آموزشی",
            "",
            "### ۱. نمودار شمعی (Candlestick)، میانگین‌های متحرک نمایی و باندهای بولینگر",
            "![نمودار شمعی و میانگین‌های متحرک](charts/candlestick_overview.png)",
            "",
            "#### 📚 راهنمای آموزشی و تحلیل نمودار شمعی و روند:",
            "- **کندل‌ها (شمع‌های ژاپنی):** هر کندل نوسانات قیمت در یک روز معاملاتی را نشان می‌دهد. بدنه سبز به معنی پیروزی خریداران (قیمت پایانی بالاتر از قیمت شروع) و بدنه قرمز به معنی غلبه فروشندگان است. سایه‌های بالا و پایین نیز سقف و کف قیمت روز را نشان می‌دهند.",
            "- **میانگین‌های متحرک نمایی (EMA 20 و EMA 50):** این خطوط میانگین قیمت در ۲۰ و ۵۰ روز اخیر را به صورت هموار ترسیم می‌کنند:",
            "  * **اگر قیمت بالای میانگین‌ها باشد:** روند سهم صعودی و پرقدرت است و خطوط میانگین مانند تکیه‌گاه و «حمایت پویا» عمل می‌کنند تا مانع از افت بیشتر قیمت شوند.",
            "  * **اگر قیمت زیر میانگین‌ها بیاید:** نشانه ضعف روند، فشار عرضه و هشدار اصلاح قیمتی است.",
            "- **باندهای بولینگر (Bollinger Bands):** کانالی متشکل از سقف، خط میانی و کف که دامنه طبیعی نوسان سهم را نشان می‌دهد. برخورد قیمت به سقف باند نشانه داغ شدن معاملات و هیجان خرید، و برخورد به کف باند نشانه قیمت‌های ارزان و فرصت خرید بالقوه است.",
            f"- **تحلیل وضعیت فعلی نماد:** آخرین قیمت در سطح **{current_price:,.0f} ریال** در مقایسه با میانگین ۲۰ روزه ({ema20:,.0f} ریال) و میانگین ۵۰ روزه ({ema50:,.0f} ریال) موقعیت **{trend_desc}** را ثبت کرده است.",
            "",
            "---",
            "",
            "### ۲. اسیلاتورهای تکانه و مومنتوم (RSI و MACD)",
            "![اسیلاتورهای تکانه و مومنتوم](charts/indicators_momentum.png)",
            "",
            "#### 📚 راهنمای آموزشی و تحلیل اسیلاتورهای تکانه (RSI و MACD):",
            "- **شاخص قدرت نسبی (RSI):** اسیلاتوری بین ۰ تا ۱۰۰ که شتاب و هیجان معاملات را اندازه می‌گیرد:",
            "  * **اگر RSI بالای ۷۰ باشد (اشباع خرید - Overbought):** یعنی قیمت با سرعت بسیار بالایی رشد کرده و خریداران زیادی هجوم آورده‌اند؛ در این نقطه نباید با هیجان وارد شد، چون ریسک استراحت، شناسایی سود یا اصلاح کوتاه‌مدت برای تخلیه هیجان وجود دارد.",
            "  * **اگر RSI زیر ۳۰ باشد (اشباع فروش - Oversold):** یعنی سهم بیش از حد افت کرده و فروشندگان تخلیه شده‌اند؛ این ناحیه اغلب یک فرصت خرید جذاب با قیمت کف و نقطه بازگشت صعودی احتمالی به شمار می‌رود.",
            "  * **محدوده بین ۳۰ تا ۷۰ (منطقه تعادل):** نوسان طبیعی سهم را نشان می‌دهد (بالای ۵۰ نشانه برتری خریداران و زیر ۵۰ نشانه برتری نسبی فروشندگان).",
            "- **شاخص همگرایی/واگرایی میانگین متحرک (MACD):**",
            "  * تقاطع خط آبی (MACD) به بالای خط نارنجی (Signal) و سبز شدن میله‌های هیستوگرام نشانه شروع یک موج صعودی پرشتاب است.",
            "  * برعکس، تقاطع به سمت پایین و قرمز شدن میله‌ها علامت کاهش قدرت خریداران و شروع فاز اصلاحی است.",
            f"- **تحلیل وضعیت فعلی نماد:** مقدار فعلی RSI برابر با **{rsi:.1f}** ({rsi_eval}) است و هیستوگرام مکدی در وضعیت **{macd_hist:+.2f}** نوسان می‌کند.",
            "",
            "---",
            "",
            "### ۳. تابلوخوانی، قدرت خریدار حقیقی و جریان نقدینگی",
            "![جریان نقدینگی و تابلوخوانی](charts/tape_reading_money_flow.png)",
            "",
            "#### 📚 راهنمای آموزشی و تحلیل جریان پول و تابلوخوانی:",
            "- **قدرت خریدار حقیقی (Buyer Power):** این شاخص از تقسیم «میانگین خرید هر فرد حقیقی» بر «میانگین فروش هر فرد حقیقی» به دست می‌آید:",
            "  * **اگر این نسبت بالای ۱ باشد (به‌ویژه بالای ۱.۵ یا ۲):** یعنی هر خریدار با پول درشت‌تر و سنگین‌تری (مثلا چندصد میلیون تومان) نسبت به فروشندگان خرد وارد شده است؛ این رفتار نشان‌دهنده «ورود پول هوشمند» و تمایل بازیگران بزرگ به جمع‌آوری سهم است.",
            "  * **اگر این نسبت زیر ۱ باشد (مثلا ۰.۷):** یعنی خریداران خرد و کم‌سرمایه در حال خرید از فروشندگان درشت هستند که معمولاً نشانه خروج پول و ریسک توزیع سهم است.",
            "- **نمودار جریان نقدینگی تجمعی (Cumulative Money Flow):** این منحنی ردپای سرمایه‌های ورودی و خروجی به سهم را نشان می‌دهد. شیب صعودی خط به معنی ورود مداوم نقدینگی و تقویت روند صعودی است، در حالی که شیب نزولی علامت خروج پول از بازار سهم است.",
            f"- **تحلیل وضعیت فعلی نماد:** نسبت قدرت خریدار به فروشنده سهم برابر با **{buyer_power:.2f}** ({bp_eval}) با سرانه خرید **{buy_real_capita:,.0f} سهم** ثبت گردیده است.",
            "",
            "---",
            "*نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir*",
        ])

        return "\n".join(lines)

    def generate_report(
        self,
        symbol: str,
        levels_or_df: Any = None,
        tape_data: Optional[Dict[str, Any]] = None,
        divergences_or_charts: Optional[Any] = None,
        chart_paths: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        """Generates technical analysis report content string."""
        if isinstance(levels_or_df, pd.DataFrame):
            df = levels_or_df
            levels = tape_data if isinstance(tape_data, dict) else {}
            tape = divergences_or_charts if isinstance(divergences_or_charts, dict) else {}
            divs = kwargs.get("divergences", {})
            charts = chart_paths or []
        else:
            levels = levels_or_df if isinstance(levels_or_df, dict) else {}
            tape = tape_data if isinstance(tape_data, dict) else {}
            divs = kwargs.get("divergences", {})
            if isinstance(divergences_or_charts, list):
                charts = divergences_or_charts
            else:
                charts = chart_paths or []

            current_price = float(levels.get("current_price", levels.get("price", 1000.0)))
            df = pd.DataFrame([{
                "open": current_price,
                "high": current_price,
                "low": current_price,
                "close": current_price,
                "volume": 1000000.0,
                "rsi": float(levels.get("rsi", 50.0)),
                "ema20": float(levels.get("ema20", current_price)),
                "ema50": float(levels.get("ema50", current_price)),
                "ema100": float(levels.get("ema100", current_price)),
                "ema200": float(levels.get("ema200", current_price)),
            }])

        return self._build_report_content(
            symbol=symbol,
            df=df,
            levels=levels,
            tape_data=tape,
            divergences=divs,
            chart_paths=charts,
        )

    def run(self, symbol: str, symbol_dir: Union[str, Path]) -> Dict[str, Any]:
        """Executes full technical analysis, produces charts, and saves technical_report.md.

        Args:
            symbol: Persian ticker symbol (e.g. 'زهلال').
            symbol_dir: Directory path for symbol outputs.

        Returns:
            Dictionary containing success status, metrics dictionary, and generated file paths.
        """
        symbol_dir = Path(symbol_dir)
        symbol_dir.mkdir(parents=True, exist_ok=True)
        charts_dir = symbol_dir / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load data
        df = self._load_history(symbol_dir)
        tape_data = self._load_tape_data(symbol_dir)

        # 2. Compute indicators and levels if data available
        chart_paths = []
        if not df.empty and len(df) >= 5:
            df_ind = TechnicalIndicators.calculate_all(df)
            levels = PriceLevels.find_key_levels(df_ind)
            divergences = self._detect_divergences(df_ind)

            # Generate 3 visual charts
            chart_paths = ChartGenerator.generate_all_charts(df_ind, symbol, charts_dir)

            last_row = df_ind.iloc[-1]
            current_price = float(last_row.get("close", 0.0))
            rsi = float(last_row.get("rsi", 50.0)) if pd.notna(last_row.get("rsi")) else 50.0
            ema20 = float(last_row.get("ema20", current_price)) if pd.notna(last_row.get("ema20")) else current_price
            ema50 = float(last_row.get("ema50", current_price)) if pd.notna(last_row.get("ema50")) else current_price
            ema100 = float(last_row.get("ema100", current_price)) if pd.notna(last_row.get("ema100")) else current_price
            ema200 = float(last_row.get("ema200", current_price)) if pd.notna(last_row.get("ema200")) else current_price
            atr = float(last_row.get("atr", 0.0)) if pd.notna(last_row.get("atr")) else 0.0
            macd = float(last_row.get("macd", 0.0)) if pd.notna(last_row.get("macd")) else 0.0
            macd_signal = float(last_row.get("macd_signal", 0.0)) if pd.notna(last_row.get("macd_signal")) else 0.0
            macd_hist = float(last_row.get("macd_hist", 0.0)) if pd.notna(last_row.get("macd_hist")) else 0.0

            buyer_power = float(tape_data.get("buyer_power", 1.0))
            nearest_support = float(levels.get("nearest_support", current_price * 0.95))
            nearest_resistance = float(levels.get("nearest_resistance", current_price * 1.05))
            swing_high = float(levels.get("swing_high", current_price))
            swing_low = float(levels.get("swing_low", current_price))
            fib_levels = levels.get("fibonacci", {})
        else:
            df_ind = df
            levels = {}
            divergences = {}
            current_price = 0.0
            rsi = 50.0
            ema20 = 0.0
            ema50 = 0.0
            ema100 = 0.0
            ema200 = 0.0
            atr = 0.0
            macd = 0.0
            macd_signal = 0.0
            macd_hist = 0.0
            buyer_power = float(tape_data.get("buyer_power", 1.0))
            nearest_support = 0.0
            nearest_resistance = 0.0
            swing_high = 0.0
            swing_low = 0.0
            fib_levels = {}
            chart_paths = ChartGenerator.generate_all_charts(df_ind, symbol, charts_dir)

        # 3. Build and write technical_report.md
        report_text = self._build_report_content(
            symbol=symbol,
            df=df_ind,
            levels=levels,
            tape_data=tape_data,
            divergences=divergences,
            chart_paths=chart_paths,
        )
        report_file = symbol_dir / "technical_report.md"
        report_file.write_text(report_text, encoding="utf-8")

        metrics = {
            "price": current_price,
            "current_price": current_price,
            "rsi": rsi,
            "ema20": ema20,
            "ema50": ema50,
            "ema100": ema100,
            "ema200": ema200,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "atr": atr,
            "buyer_power": buyer_power,
            "fibonacci": fib_levels,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
        }

        return {
            "symbol": symbol,
            "success": True,
            "metrics": metrics,
            "report_file": str(report_file),
            "charts": [str(p) for p in chart_paths],
        }
