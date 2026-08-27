import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import jdatetime


class StrategyAgent:
    """Strategy & Risk Recommender Agent synthesizing technical, fundamental,

    orderbook tape reading, and news sentiment into actionable trading recommendations.
    """

    def __init__(self):
        pass

    def _load_news_summary(self, symbol_dir: Path) -> str:
        """Reads news summary text if present."""
        news_file = symbol_dir / "news" / "news_summary.md"
        if news_file.exists():
            try:
                return news_file.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    def _load_codal_summary(self, symbol_dir: Path) -> str:
        """Reads codal summary text if present."""
        codal_file = symbol_dir / "codal_reports" / "codal_summaries.md"
        if codal_file.exists():
            try:
                return codal_file.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    def _calculate_recommendation_plan(
        self,
        tech: Dict[str, Any],
        fund: Dict[str, Any],
        news_text: str,
        codal_text: str,
    ) -> Dict[str, Any]:
        """Calculates quantitative entry, targets, dynamic stop-loss,

        risk/reward ratio, multi-horizon breakdowns, and portfolio sizing.
        """
        # 1. Price extraction
        current_price_raw = tech.get("current_price") or tech.get("price") or fund.get("current_price")
        current_price = float(current_price_raw) if current_price_raw and float(current_price_raw) > 0 else 1000.0

        # 2. Extract technical parameters
        atr = float(tech.get("atr") or 0.0)
        rsi = float(tech.get("rsi") or 50.0)
        buyer_power = float(tech.get("buyer_power") or 1.0)

        nearest_support_raw = tech.get("nearest_support")
        nearest_support = float(nearest_support_raw) if nearest_support_raw is not None else current_price * 0.93

        nearest_resistance_raw = tech.get("nearest_resistance")
        nearest_resistance = float(nearest_resistance_raw) if nearest_resistance_raw is not None else current_price * 1.15

        swing_high_raw = tech.get("swing_high")
        swing_high = float(swing_high_raw) if swing_high_raw is not None else current_price * 1.30

        swing_low_raw = tech.get("swing_low")
        swing_low = float(swing_low_raw) if swing_low_raw is not None else current_price * 0.85

        # 3. Extract fundamental parameters
        fund_score = float(fund.get("fundamental_score") or 5.0)
        pe_ratio = float(fund.get("pe_ratio") or 0.0)
        dividend_yield = float(fund.get("dividend_yield_pct") or 0.0)

        # 4. Stop loss calculation (Dynamic ATR + Support)
        if atr > 0:
            stop_loss = max(nearest_support - (0.5 * atr), current_price * 0.90)
        else:
            stop_loss = max(nearest_support, current_price * 0.93)

        # Safety boundary: stop loss must be strictly below current price
        if stop_loss >= current_price or nearest_support >= current_price:
            stop_loss = current_price * 0.95

        stop_loss = round(stop_loss, 2)
        risk_per_share = current_price - stop_loss
        if risk_per_share <= 0:
            risk_per_share = current_price * 0.05
            stop_loss = round(current_price * 0.95, 2)

        sl_risk_pct = round((risk_per_share / current_price) * 100, 1)

        # 5. Targets & Rewards
        target_1 = nearest_resistance
        if target_1 <= current_price:
            target_1 = round(current_price * 1.12, 2)
        else:
            target_1 = round(target_1, 2)

        target_2 = round(max(swing_high, target_1 * 1.10), 2)
        reward_1 = target_1 - current_price
        t1_ret_pct = round((reward_1 / current_price) * 100, 1)
        t2_ret_pct = round(((target_2 - current_price) / current_price) * 100, 1)

        # 6. Risk / Reward ratio
        rr_ratio = round(reward_1 / risk_per_share, 2) if risk_per_share > 0 else 1.0

        # 7. Convergence Matrix Scoring
        score = 0

        # Tape / Buyer power
        if buyer_power >= 1.3:
            score += 2
        elif buyer_power <= 0.8:
            score -= 2

        # Fundamentals
        if fund_score >= 7.0:
            score += 2
        elif fund_score < 4.0:
            score -= 2

        # RSI Momentum
        if 35 <= rsi <= 55:
            score += 1
        elif rsi > 75:
            score -= 2
        elif rsi < 30:
            score += 1

        # R/R attractiveness
        if rr_ratio >= 2.0:
            score += 2
        elif rr_ratio < 1.0:
            score -= 2

        # News & Codal sentiment adjustments
        combined_text = (news_text + " " + codal_text).lower()
        if any(w in combined_text for w in ["مثبت", "رشد", "افزایش", "صادرات", "سودآوری", "تقاضا"]):
            score += 1
        if any(w in combined_text for w in ["ریسک", "کاهش", "ضرر", "افت", "توقف", "منفی"]):
            score -= 1

        # 8. Final Verdict Determination
        if score >= 4:
            verdict = "خرید قوی (Strong Buy)"
            action_desc = "سهم در موقعیت بسیار جذاب تکنیکال و ارزندگی بالای بنیادی قرار دارد. ورود در محدوده فعلی با رعایت حد ضرر پویا اکیداً توصیه می‌شود."
            portfolio_allocation_pct = 15.0
            sizing_strategy = "ورود در ۳ پله: ۴۰٪ در محدوده فعلی، ۳۰٪ در پولبک به حمایت، ۳۰٪ پس از تثبیت بالای مقاومت اول."
        elif 1 <= score < 4:
            verdict = "خرید پله‌ای (Accumulate)"
            action_desc = "سهم دارای ارزندگی مناسب و شرایط معاملاتی مساعد است؛ ورود مرحله‌ای و پله‌ای در محدوده مشخص‌شده با رعایت اصول مدیریت ریسک توصیه می‌شود."
            portfolio_allocation_pct = 10.0
            sizing_strategy = "ورود در ۳ پله متوالی با فواصل قیمتی ۲ الی ۳ درصدی برای میانگین‌سازی کنترل‌شده."
        elif -2 <= score < 1:
            verdict = "نگهداری با رعایت حد ضرر (Hold)"
            action_desc = "حفظ موقعیت سهامداری با پایبندی دقیق به حد ضرر تعیین‌شده تا شفاف‌تر شدن جهت شکست حمایت یا مقاومت توصیه می‌شود."
            portfolio_allocation_pct = 5.0
            sizing_strategy = "عدم افزایش حجم و سرمایه جدید در قیمت‌های جاری؛ حفظ پوزیشن‌های قبلی با تریلینگ استاپ."
        else:
            verdict = "سیو سود / خروج (Sell / Exit)"
            action_desc = "سهم در محدوده اشباع خرید، تضعیف تقاضا یا ارزیابی بالای ارزش ذاتی قرار گرفته است. شناسایی سود یا خروج پله‌ای با فعال‌سازی حد ضرر توصیه می‌شود."
            portfolio_allocation_pct = 0.0
            sizing_strategy = "عدم تخصیص نقدینگی جدید؛ اقدام فوری به سیو سود، کاهش حجم و خروج در مثبت‌های بازار."

        entry_min = round(current_price * 0.98, 2)
        entry_max = round(current_price * 1.02, 2)
        entry_zone = f"{entry_min:,.0f} تا {entry_max:,.0f} ریال"

        # 9. Multi-Horizon Plans
        horizons = {
            "short_term": {
                "title": "کوتاه‌مدت (۱ تا ۴ هفته)",
                "strategy": "نوسان‌گیری با تکیه بر تابلوی معاملات، ورود پول هوشمند و شکست مقاومت اول",
                "target": target_1,
                "expected_return_pct": t1_ret_pct,
                "stop_loss": stop_loss,
                "risk_pct": sl_risk_pct,
            },
            "mid_term": {
                "title": "میان‌مدت (۱ تا ۳ ماه)",
                "strategy": "بهره‌گیری از شکست الگوهای ماژور و گزارش‌های فعالیت ماهانه کدال",
                "target": target_2,
                "expected_return_pct": t2_ret_pct,
                "stop_loss": round(stop_loss * 0.97, 2),
                "risk_pct": round(((current_price - (stop_loss * 0.97)) / current_price) * 100, 1),
            },
            "long_term": {
                "title": "بلندمدت (۶ تا ۱۲ ماه)",
                "strategy": "دید بنیادی و سرمایه‌گذاری بر پایه ارزش ذاتی، P/E رو به جلو و سود تقسیمی مجمع (DPS)",
                "target": round(target_2 * 1.25, 2),
                "expected_return_pct": round(((target_2 * 1.25 - current_price) / current_price) * 100, 1),
                "stop_loss": round(nearest_support * 0.92, 2),
                "risk_pct": round(((current_price - (nearest_support * 0.92)) / current_price) * 100, 1),
            },
        }

        # 10. Invalidation triggers
        invalidation_triggers = [
            f"تثبیت کندل روزانه زیر قیمت {stop_loss:,.0f} ریال با حجم معاملات فراتر از میانگین ماهانه.",
            f"خروج سنگین نقدینگی حقیقی و نزول نسبت قدرت خریدار به زیر ۰.۷۵ در دو روز متوالی.",
            f"افت محسوس در درآمد یا نرخ‌های فروش ماهانه در سامانه کدال (بیش از ۱۵ درصد نسبت به دوره قبل).",
            f"شکست قطعی کف سوئینگ ماژور در محدوده {swing_low:,.0f} ریال.",
        ]

        return {
            "overall_verdict": verdict,
            "action_desc": action_desc,
            "current_price": current_price,
            "entry_zone": entry_zone,
            "entry_min": entry_min,
            "entry_max": entry_max,
            "target_1": target_1,
            "target_2": target_2,
            "stop_loss": stop_loss,
            "risk_reward_ratio": rr_ratio,
            "score": score,
            "horizons": horizons,
            "portfolio_allocation_pct": portfolio_allocation_pct,
            "sizing_strategy": sizing_strategy,
            "invalidation_triggers": invalidation_triggers,
            "buyer_power": buyer_power,
            "fund_score": fund_score,
            "rsi": rsi,
            "atr": atr,
            "pe_ratio": pe_ratio,
            "dividend_yield": dividend_yield,
        }

    def _build_final_recommendation_report(
        self,
        symbol: str,
        plan: Dict[str, Any],
        news_text: str,
        codal_text: str,
    ) -> str:
        """Generates rich Persian Markdown recommendation report."""
        try:
            now_shamsi = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")
        except Exception:
            now_shamsi = "نامشخص"

        verdict = plan["overall_verdict"]
        current_price = plan["current_price"]
        entry_zone = plan["entry_zone"]
        target_1 = plan["target_1"]
        target_2 = plan["target_2"]
        stop_loss = plan["stop_loss"]
        rr_ratio = plan["risk_reward_ratio"]
        action_desc = plan["action_desc"]

        st = plan["horizons"]["short_term"]
        mt = plan["horizons"]["mid_term"]
        lt = plan["horizons"]["long_term"]

        rr_badge = "🟢 جذاب (R/R >= 2)" if rr_ratio >= 2.0 else ("🟡 قابل قبول (R/R >= 1.5)" if rr_ratio >= 1.5 else "🔴 نامناسب (R/R < 1.5)")

        lines = [
            f"# جمع‌بندی تحلیلی و پیشنهاد معاملاتی نماد {symbol}",
            "",
            f"**تاریخ تدوین استراتژی:** {now_shamsi}  ",
            f"**سیگنال و وضعیت نهایی:** **{verdict}**  ",
            f"**آخرین قیمت معاملاتی:** {current_price:,.0f} ریال  ",
            f"**کیفیت ریسک به ریوارد (R/R):** {rr_badge}  ",
            "",
            f"> **خلاصه اجرایی و چشم‌انداز:** {action_desc}",
            "",
            "---",
            "",
            "## جدول راهنمای معامله (Actionable Plan)",
            "| پارامتر معاملاتی | مقدار پیشنهادی | درصد بازدهی / ریسک | توضیحات و منطق تحلیلی |",
            "| :--- | :--- | :--- | :--- |",
            f"| **محدوده خرید بهینه (Entry Zone)** | **{entry_zone}** | — | بازه ورود مجاز و منطقی برای ورود پله‌ای |",
            f"| **حد سود اول (Target 1)** | **{target_1:,.0f} ریال** | **+{st['expected_return_pct']}%** | مقاومت اول و هدف نوسان‌گیری کوتاه‌مدت |",
            f"| **حد سود دوم (Target 2)** | **{target_2:,.0f} ریال** | **+{mt['expected_return_pct']}%** | سقف کانال ماژور و مقاومت کلیدی میان‌مدت |",
            f"| **حد ضرر پویا (Dynamic Stop Loss)** | **{stop_loss:,.0f} ریال** | **-{st['risk_pct']}%** | سطح شکست حمایت پیوت با ضریب نوسان ATR |",
            f"| **نسبت سود به ریسک (R/R)** | **{rr_ratio}** | — | {rr_badge} |",
            "",
            "---",
            "",
            "## راهبرد در ۳ افق زمانی",
            f"### ۱. {st['title']}",
            f"- **استراتژی اجرایی:** {st['strategy']}",
            f"- **تارگت هدف:** {st['target']:,.0f} ریال (بازدهی مورد انتظار: {st['expected_return_pct']}%)",
            f"- **حد ضرر:** {st['stop_loss']:,.0f} ریال (حداکثر ریسک: {st['risk_pct']}%)",
            "",
            f"### ۲. {mt['title']}",
            f"- **استراتژی اجرایی:** {mt['strategy']}",
            f"- **تارگت هدف:** {mt['target']:,.0f} ریال (بازدهی مورد انتظار: {mt['expected_return_pct']}%)",
            f"- **حد ضرر:** {mt['stop_loss']:,.0f} ریال (ریسک: {mt['risk_pct']}%)",
            "",
            f"### ۳. {lt['title']}",
            f"- **استراتژی اجرایی:** {lt['strategy']}",
            f"- **تارگت هدف:** {lt['target']:,.0f} ریال (بازدهی مورد انتظار: {lt['expected_return_pct']}%)",
            f"- **حد ضرر:** {lt['stop_loss']:,.0f} ریال (ریسک: {lt['risk_pct']}%)",
            "",
            "---",
            "",
            "## ماتریس همگرایی تحلیلی (Convergence Matrix)",
            "| رکن تحلیلی | وضعیت و داده‌های کلیدی | سیگنال منتج |",
            "| :--- | :--- | :--- |",
            f"| **تحلیل تکنیکال** | شاخص RSI: {plan['rsi']:.1f} - ATR: {plan['atr']:,.0f} ریال | {'مساعد برای صعود' if plan['rsi'] <= 60 else 'اشباع خرید / خنثی'} |",
            f"| **تابلوخوانی و جریان پول** | سرانه قدرت خریدار به فروشنده: {plan['buyer_power']:.2f} | {'ورود پول هوشمند و تقاضای قوی' if plan['buyer_power'] >= 1.2 else 'تعادل یا برتری عرضه'} |",
            f"| **تحلیل بنیادی و صورت‌های مالی** | نمره ارزیابی: {plan['fund_score']}/۱۰ - نسبت P/E: {plan['pe_ratio']:.1f} | {'ارزندگی بالا و حاشیه سود پایدار' if plan['fund_score'] >= 7 else 'ارزندگی متوسط'} |",
            f"| **اخبار و رویدادهای کدال** | اطلاعیه‌های ماهانه و سنتیمنت رسانه‌ای | {'محرک‌های مثبت خبری و رشد درآمد' if any(w in news_text + codal_text for w in ['رشد', 'صادرات', 'مثبت']) else 'پوشش خبری باثبات'} |",
            "",
            "---",
            "",
            "## مدیریت ریسک و اندازه موقعیت در سبد سرمایه‌گذاری (Risk & Portfolio Sizing)",
            f"- **حداکثر سهم پیشنهادی از کل پورتفو:** **{plan['portfolio_allocation_pct']}%**",
            f"- **روش چینش و ورود:** {plan['sizing_strategy']}",
            "- **مدیریت حد ضرر متحرک (Trailing Stop):** پس از دستیابی قیمت به ۵۰٪ فاصله تا تارگت اول، حد ضرر را به نقطه سربه‌سر (قیمت ورود میانگین) منتقل نمایید.",
            "- **قانون حفظ سرمایه:** در هیچ شرایطی اجازه ندهید ریسک این تک‌سهم بیش از ۲ درصد کل ارزش سبد دارایی شما را تحت تأثیر قرار دهد.",
            "",
            "---",
            "",
            "## شروط ابطال تحلیل",
        ]

        for trigger in plan["invalidation_triggers"]:
            lines.append(f"- {trigger}")

        lines.extend([
            "",
            "---",
            "*سلب مسئولیت: این گزارش بر مبنای پردازش الگوریتمی متغیرهای بازار سرمایه تهیه شده و مسئولیت تصمیم‌گیری نهایی بر عهده معامله‌گر است.*",
        ])

        return "\n".join(lines)

    def run(
        self,
        symbol: str,
        symbol_dir: Union[str, Path],
        tech_metrics: Optional[Dict[str, Any]] = None,
        fund_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes the strategy synthesis workflow, builds recommendation plan,

        and creates final_recommendation.md and strategy_recommendation.json.
        """
        symbol_dir = Path(symbol_dir)
        symbol_dir.mkdir(parents=True, exist_ok=True)

        tech = tech_metrics or {}
        fund = fund_metrics or {}

        news_text = self._load_news_summary(symbol_dir)
        codal_text = self._load_codal_summary(symbol_dir)

        plan = self._calculate_recommendation_plan(
            tech=tech,
            fund=fund,
            news_text=news_text,
            codal_text=codal_text,
        )

        verdict = plan["overall_verdict"]

        # Write final_recommendation.md
        report_content = self._build_final_recommendation_report(
            symbol=symbol,
            plan=plan,
            news_text=news_text,
            codal_text=codal_text,
        )
        report_file = symbol_dir / "final_recommendation.md"
        report_file.write_text(report_content, encoding="utf-8")

        # Write strategy_recommendation.json
        json_file = symbol_dir / "strategy_recommendation.json"
        json_file.write_text(
            json.dumps(
                {
                    "symbol": symbol,
                    "verdict": verdict,
                    "plan": plan,
                    "entry_zone": plan["entry_zone"],
                    "target_1": plan["target_1"],
                    "target_2": plan["target_2"],
                    "stop_loss": plan["stop_loss"],
                    "risk_reward_ratio": plan["risk_reward_ratio"],
                    "portfolio_allocation_pct": plan["portfolio_allocation_pct"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return {
            "symbol": symbol,
            "success": True,
            "verdict": verdict,
            "plan": plan,
            "report_file": str(report_file),
            "json_file": str(json_file),
        }
