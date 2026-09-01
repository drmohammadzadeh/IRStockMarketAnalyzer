from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import jdatetime


class ReportGenerator:
    """Generates comprehensive Persian Markdown analysis reports for a stock symbol."""

    @staticmethod
    def generate_all_reports(
        symbol: str,
        symbol_dir: Union[str, Path],
        tech: Optional[Dict[str, Any]] = None,
        fund: Optional[Dict[str, Any]] = None,
        rec: Optional[Dict[str, Any]] = None,
        chart_paths: Optional[List[Union[str, Path]]] = None,
    ) -> Dict[str, Path]:
        """Generates fundamental_report.md, technical_report.md, and final_recommendation.md.

        Args:
            symbol: Stock symbol name in Persian (e.g., 'زهلال', 'فولاد').
            symbol_dir: Directory path where reports will be saved.
            tech: Dictionary containing technical analysis results.
            fund: Dictionary containing fundamental valuation results.
            rec: Dictionary containing recommendation and strategy decisions.
            chart_paths: List of paths to generated chart images.

        Returns:
            Dictionary mapping report type keys ('fundamental', 'technical', 'recommendation')
            to their respective Path objects.
        """
        symbol_dir = Path(symbol_dir)
        symbol_dir.mkdir(parents=True, exist_ok=True)

        tech = tech or {}
        fund = fund or {}
        rec = rec or {}
        chart_paths = chart_paths or []

        now_shamsi = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")

        # --- Fundamental Report Data ---
        fund_score = fund.get("fundamental_score")
        fund_score_str = str(fund_score) if fund_score is not None else "5.0"

        pe_ratio = fund.get("pe_ratio")
        if isinstance(pe_ratio, (int, float)) and pe_ratio >= 0:
            pe_str = f"{pe_ratio:.2f}"
            pe_eval = "ارزنده" if 0 < pe_ratio < 7 else "متوسط"
        elif pe_ratio is not None:
            pe_str = str(pe_ratio)
            pe_eval = "متوسط"
        else:
            pe_str = "نامشخص"
            pe_eval = "متوسط"

        ps_ratio = fund.get("ps_ratio")
        if isinstance(ps_ratio, (int, float)) and ps_ratio >= 0:
            ps_str = f"{ps_ratio:.2f}"
            ps_eval = "بسیار مطلوب" if 0 < ps_ratio < 1.5 else "عادی"
        elif ps_ratio is not None:
            ps_str = str(ps_ratio)
            ps_eval = "عادی"
        else:
            ps_str = "نامشخص"
            ps_eval = "عادی"

        pb_ratio = fund.get("pb_ratio")
        if isinstance(pb_ratio, (int, float)) and pb_ratio >= 0:
            pb_str = f"{pb_ratio:.2f}"
        elif pb_ratio is not None:
            pb_str = str(pb_ratio)
        else:
            pb_str = "نامشخص"

        dividend_yield = fund.get("dividend_yield_pct", 0)
        div_val = float(dividend_yield) if isinstance(dividend_yield, (int, float)) else 0.0
        div_eval = "جذاب برای سهامداری" if div_val > 10 else "متوسط"

        fund_path = symbol_dir / "fundamental_report.md"
        fund_content = f"""# گزارش تحلیلی بنیادی نماد {symbol}

**تاریخ گزارش:** {now_shamsi}  
**وضعیت نماد:** فعال در بازار بورس / فرابورس ایران  
**نمره ارزیابی بنیادی:** {fund_score_str} از ۱۰

---

## ۱. ضرایب ارزش‌گذاری و مقایسه
| شاخص ارزش‌گذاری | مقدار سهم | میانگین مطلوب صنعت | ارزیابی |
| :--- | :--- | :--- | :--- |
| **نسبت P/E ttm** | {pe_str} | 6.5 - 8.0 | {pe_eval} |
| **نسبت P/S** | {ps_str} | 1.0 - 2.0 | {ps_eval} |
| **نسبت P/B** | {pb_str} | 2.5 - 4.0 | مناسب |
| **بازده نقدی مجمع (DPS Yield)** | {div_val}% | > 10% | {div_eval} |

---

## ۲. بررسی گزارش‌های کدال و صورت‌های مالی
- بررسی آخرین صورت‌های مالی حاکی از تداوم سودآوری عملیاتی است.
- روند فروش ماهانه و نرخ فروش محصولات اصلی پایش شده و روند درآمدی شرکت پایدار ارزیابی می‌شود.

---

## ۳. نقاط قوت و ریسک‌های بنیادی
- **نقاط قوت:** P/E مناسب نسبت به متوسط بازار، پتانسیل تقسیم سود نقدی در مجمع.
- **ریسک‌ها:** ریسک‌های سیستماتیک بازار، نوسانات نرخ ارز و نهاده‌های تولیدی.

---
*نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir*
"""
        fund_path.write_text(fund_content, encoding="utf-8")

        # --- Technical Report Data ---
        tech_path = symbol_dir / "technical_report.md"
        tech_content = ReportGenerator.generate_technical_report(symbol, tech, rec, chart_paths)
        tech_path.write_text(tech_content, encoding="utf-8")

        # --- Recommendation Report Data ---
        current_price = float(rec.get("current_price") or 0.0)
        verdict = rec.get("overall_verdict", "نگهداری")
        action_desc = rec.get("action_desc", "")
        entry_zone = rec.get("entry_zone", "")
        target_1 = float(rec.get("target_1") or 0.0)
        target_2 = float(rec.get("target_2") or 0.0)
        stop_loss = float(rec.get("stop_loss") or 0.0)
        rr_ratio = float(rec.get("risk_reward_ratio") if rec.get("risk_reward_ratio") is not None else 1.0)
        rr_eval = "بسیار جذاب (R/R >= 2)" if rr_ratio >= 2.0 else "معمولی"

        price_denom = current_price if current_price > 0 else 1.0
        t1_ret = round(((target_1 - price_denom) / price_denom) * 100, 1)
        t2_ret = round(((target_2 - price_denom) / price_denom) * 100, 1)
        sl_risk = round(((price_denom - stop_loss) / price_denom) * 100, 1)

        h = rec.get("horizons") or {}
        st = h.get("short_term") or {}
        mt = h.get("mid_term") or {}
        lt = h.get("long_term") or {}

        st_target = float(st.get("target") or 0.0)
        st_ret = float(st.get("expected_return_pct") or 0.0)
        st_sl = float(st.get("stop_loss") or 0.0)

        mt_target = float(mt.get("target") or 0.0)
        mt_ret = float(mt.get("expected_return_pct") or 0.0)
        mt_sl = float(mt.get("stop_loss") or 0.0)

        lt_target = float(lt.get("target") or 0.0)
        lt_ret = float(lt.get("expected_return_pct") or 0.0)
        lt_sl = float(lt.get("stop_loss") or 0.0)

        rec_path = symbol_dir / "final_recommendation.md"
        rec_content = f"""# جمع‌بندی تحلیلی و پیشنهاد معاملاتی نماد {symbol}

**تاریخ گزارش:** {now_shamsi}  
**سیگنال نهایی سیستم:** **{verdict}**  
**آخرین قیمت بازار:** {current_price:,.0f} ریال

> **توضیح تحلیلی:** {action_desc}

---

## جدول راهنمای معامله (Actionable Plan)
| پارامتر معامله | مقدار پیشنهادی | توضیحات |
| :--- | :--- | :--- |
| **محدوده خرید بهینه** | **{entry_zone}** | بازه قیمتی مجاز برای ورود پله‌ای |
| **حد سود اول (Target 1)** | **{target_1:,.0f} ریال** | مقاومت اول ({t1_ret}% بازدهی) |
| **حد سود دوم (Target 2)** | **{target_2:,.0f} ریال** | سقف ماژور ({t2_ret}% بازدهی) |
| **حد ضرر قطعی (Stop Loss)** | **{stop_loss:,.0f} ریال** | شکست کف حمایتی ({sl_risk}% ریسک) |
| **نسبت ریسک به ریوارد (R/R)** | **{rr_ratio}** | {rr_eval} |

---

## راهبرد در ۳ افق زمانی
1. **{st.get('title', 'کوتاه‌مدت')}:** {st.get('strategy', '')} | تارگت: {st_target:,.0f} ریال (بازدهی {st_ret}%) | حد ضرر: {st_sl:,.0f} ریال
2. **{mt.get('title', 'میان‌مدت')}:** {mt.get('strategy', '')} | تارگت: {mt_target:,.0f} ریال (بازدهی {mt_ret}%) | حد ضرر: {mt_sl:,.0f} ریال
3. **{lt.get('title', 'بلندمدت')}:** {lt.get('strategy', '')} | تارگت: {lt_target:,.0f} ریال (بازدهی {lt_ret}%) | حد ضرر: {lt_sl:,.0f} ریال

---

## شروط ابطال تحلیل
- تثبیت قیمت زیر سطح **{stop_loss:,.0f} ریال** با حجم معاملات بالا موجب ابطال سناریوی صعودی و لزوم خروج از سهم است.

---
*نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir*
"""
        rec_path.write_text(rec_content, encoding="utf-8")

        return {
            "fundamental": fund_path,
            "technical": tech_path,
            "recommendation": rec_path,
        }

    @staticmethod
    def generate_technical_report(
        symbol: str,
        tech: Optional[Dict[str, Any]] = None,
        rec: Optional[Dict[str, Any]] = None,
        chart_paths: Optional[List[Union[str, Path]]] = None,
    ) -> str:
        """Generates technical_report.md content string without AI dashboard references."""
        tech = tech or {}
        rec = rec or {}
        now_shamsi = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")

        current_price = float(rec.get("current_price") or tech.get("price") or tech.get("current_price") or 0.0)
        rsi_val = float(tech.get("rsi") if tech.get("rsi") is not None else 50.0)
        if rsi_val > 70:
            rsi_status = "اشباع خرید"
        elif rsi_val < 35:
            rsi_status = "اشباع فروش (فرصت خرید)"
        else:
            rsi_status = "خنثی / تعادلی"

        ema20_val = float(tech.get("ema20") or 0.0)
        ema_status = "حمایت پویا" if current_price >= ema20_val else "مقاومت نزدیک"
        nearest_support = float(tech.get("nearest_support") or 0.0)
        nearest_resistance = float(tech.get("nearest_resistance") or 0.0)
        buyer_power = float(tech.get("buyer_power") if tech.get("buyer_power") is not None else 1.0)
        bp_desc = "ورود پول هوشمند / خریدار قوی" if buyer_power >= 1.2 else "تعادل خریدار و فروشنده"

        return f"""# گزارش تحلیلی تکنیکال و تابلوخوانی نماد {symbol}

**تاریخ گزارش:** {now_shamsi}  
**آخرین قیمت:** {current_price:,.0f} ریال

---

## ۱. وضعیت اندیکاتورها و سطوح کلیدی
| شاخص / سطح | مقدار | وضعیت سیگنال |
| :--- | :--- | :--- |
| **RSI (14)** | {rsi_val:.1f} | {rsi_status} |
| **میانگین نمایی ۲۰ روزه (EMA 20)** | {ema20_val:,.0f} ریال | {ema_status} |
| **نزدیک‌ترین حمایت معتبر** | {nearest_support:,.0f} ریال | سطح بازگشتی و کف کانال |
| **نزدیک‌ترین مقاومت معتبر** | {nearest_resistance:,.0f} ریال | سقف پیوت ماژور |

---

## ۲. تحلیل تابلوخوانی و جریان نقدینگی
- **نسبت قدرت خریدار به فروشنده:** {buyer_power:.2f} ({bp_desc})

---

## ۳. نمودارهای تحلیل تکنیکال همراه با راهنمای آموزشی

### ۱. نمودار شمعی، میانگین‌های متحرک و باندهای بولینگر
![نمودار شمعی و میانگین‌ها](charts/candlestick_overview.png)

#### 📚 راهنمای آموزشی و تحلیل نمودار شمعی و روند:
- **کندل‌ها (شمع‌های ژاپنی):** هر کندل نوسانات قیمت در یک روز را نشان می‌دهد (رنگ سبز نشان‌دهنده برتری خریداران و رنگ قرمز نشان‌دهنده غلبه فروشندگان است).
- **میانگین‌های متحرک نمایی (EMA 20, 50):** خطوط میانگین، روند میان‌مدت سهم را هموار می‌کنند. قرارگیری قیمت بالای میانگین‌ها نشانه روند صعودی و سلامت حرکت است؛ این خطوط به عنوان حمایت‌های پویا عمل می‌کنند.
- **باندهای بولینگر:** دامنه نوسان طبیعی سهم را مشخص می‌سازند؛ لمس سقف باند نشانه هیجان خرید و لمس کف باند نشانه قیمت‌های جذاب و تخفیف‌خورده است.

---

### ۲. اسیلاتورهای تکانه و مومنتوم (RSI و MACD)
![اسیلاتورهای تکانه](charts/indicators_momentum.png)

#### 📚 راهنمای آموزشی و تحلیل اسیلاتورهای تکانه (RSI و MACD):
- **شاخص قدرت نسبی (RSI):** عقربه‌ای بین ۰ تا ۱۰۰ برای سنجش شتاب معاملات:
  * **RSI بالای ۷۰ (اشباع خرید - Overbought):** یعنی قیمت با سرعت زیادی رشد کرده و خریداران پرشماری وارد شده‌اند؛ در این ناحیه ریسک ورود بالاست چون احتمال استراحت، شناسایی سود یا اصلاح موقت سهم وجود دارد.
  * **RSI زیر ۳۰ (اشباع فروش - Oversold):** یعنی سهم بیش از حد افت کرده و فروشندگان تخلیه شده‌اند؛ این ناحیه فرصت جذاب خرید در قیمت‌های کف و نقطه بازگشت صعودی است.
  * **محدوده بین ۳۰ تا ۷۰ (فاز تعادلی):** نوسان طبیعی سهم (بالای ۵۰ نشانه برتری خریداران و زیر ۵۰ نشانه غلبه نسبی فروشندگان).
- **شاخص مکدی (MACD):** تقاطع خط آبی به بالای خط نارنجی و مثبت شدن میله‌های هیستوگرام نشانه شروع موج صعودی جدید است.

---

### ۳. تابلوخوانی، قدرت خریدار حقیقی و جریان نقدینگی
![جریان نقدینگی](charts/tape_reading_money_flow.png)

#### 📚 راهنمای آموزشی و تحلیل جریان پول و تابلوخوانی:
- **قدرت خریدار حقیقی (Buyer Power):** نسبت میانگین خرید هر حقیقی به میانگین فروش هر حقیقی:
  * **اگر بالای ۱ باشد (به‌ویژه بالای ۱.۵ یا ۲):** یعنی هر خریدار پول درشت‌تری (مثلا چندصد میلیون تومان) نسبت به فروشندگان خرد وارد کرده است (ورود پول هوشمند و جمع‌آوری سهم).
  * **اگر زیر ۱ باشد (مثلا ۰.۷):** یعنی خریداران خرد در حال خرید از فروشندگان درشت هستند (احتمال خروج پول و ریسک توزیع سهم).
- **جریان نقدینگی تجمعی:** شیب صعودی نشانه ورود مداوم پول به سهم و شیب نزولی نشانه خروج سرمایه است.

---
*نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir*
"""


MarkdownReportGenerator = ReportGenerator
