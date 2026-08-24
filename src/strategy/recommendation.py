from typing import Dict, Any, Optional


class StrategyEngine:
    @staticmethod
    def generate_recommendation(
        tech: Optional[Dict[str, Any]] = None,
        fund: Optional[Dict[str, Any]] = None,
        current_price: float = 0.0,
        atr: float = 0.0
    ) -> Dict[str, Any]:
        """
        Synthesizes technical indicators, support/resistance levels, buyer power,
        and fundamental valuation into concrete recommendations across 3 time horizons
        (short, mid, long term) with entry prices, stop-loss, targets, and risk/reward.
        """
        tech = tech or {}
        fund = fund or {}

        current_price = float(current_price) if current_price and current_price > 0 else 1.0
        atr = float(atr) if atr is not None and atr > 0 else 0.0

        nearest_support_val = tech.get("nearest_support")
        nearest_support = float(nearest_support_val) if nearest_support_val is not None else current_price * 0.93

        nearest_resistance_val = tech.get("nearest_resistance")
        nearest_resistance = float(nearest_resistance_val) if nearest_resistance_val is not None else current_price * 1.15

        swing_high_val = tech.get("swing_high")
        swing_high = float(swing_high_val) if swing_high_val is not None else current_price * 1.3

        buyer_power_val = tech.get("buyer_power")
        buyer_power = float(buyer_power_val) if buyer_power_val is not None else 1.0

        fund_score_val = fund.get("fundamental_score")
        fund_score = float(fund_score_val) if fund_score_val is not None else 5.0

        rsi_val = tech.get("rsi")
        rsi = float(rsi_val) if rsi_val is not None else 50.0

        # Stop loss calculation (support - 0.5*ATR or 5-7% below current price)
        stop_loss = round(max(nearest_support - (0.5 * atr if atr > 0 else 0), current_price * 0.93), 2)
        risk_per_share = current_price - stop_loss
        if risk_per_share <= 0:
            risk_per_share = current_price * 0.05
            stop_loss = round(current_price * 0.95, 2)

        target_1 = round(nearest_resistance, 2)
        reward_1 = target_1 - current_price
        target_2 = round(max(swing_high, target_1 * 1.1), 2)

        rr_ratio = round(reward_1 / risk_per_share, 2) if risk_per_share > 0 else 1.0

        # Decision Matrix
        score = 0
        if buyer_power >= 1.3:
            score += 2
        elif buyer_power <= 0.8:
            score -= 2

        if fund_score >= 7.0:
            score += 2
        elif fund_score < 4.0:
            score -= 2

        if 35 <= rsi <= 55:
            score += 1
        elif rsi > 75:
            score -= 2

        if rr_ratio >= 2.0:
            score += 2
        elif rr_ratio < 1.0:
            score -= 2

        if score >= 4:
            verdict = "خرید قوی (Strong Buy)"
            action_desc = "سهم در موقعیت بسیار جذاب تکنیکال و بنیادی قرار دارد. خرید در محدوده فعلی با رعایت حد ضرر توصیه می‌شود."
        elif 1 <= score < 4:
            verdict = "خرید پله‌ای (Accumulate)"
            action_desc = "سهم ارزندگی مناسب دارد؛ ورود پله‌ای در محدوده مجاز با کنترل اندازه موقعیت توصیه می‌شود."
        elif -2 <= score < 1:
            verdict = "نگهداری با رعایت حد ضرر (Hold)"
            action_desc = "حفظ سهامداری با پایبندی به حد ضرر تا مشخص شدن شفاف‌تر جهت شکست مقاومت/حمایت."
        else:
            verdict = "سیو سود / خروج (Sell / Exit)"
            action_desc = "سهم در اشباع خرید یا محدوده پرریسک است. کاهش حجم یا خروج توصیه می‌شود."

        entry_min = round(current_price * 0.98, 2)
        entry_max = round(current_price * 1.02, 2)

        horizons = {
            "short_term": {
                "title": "کوتاه‌مدت (۱ تا ۴ هفته)",
                "strategy": "نوسان‌گیری با تکیه بر تابلوی معاملات و پول هوشمند",
                "target": target_1,
                "expected_return_pct": round(((target_1 - current_price) / current_price) * 100, 1),
                "stop_loss": stop_loss,
                "risk_pct": round(((current_price - stop_loss) / current_price) * 100, 1),
            },
            "mid_term": {
                "title": "میان‌مدت (۱ تا ۳ ماه)",
                "strategy": "بهره‌گیری از شکست الگوها و گزارش‌های ماهانه کدال",
                "target": target_2,
                "expected_return_pct": round(((target_2 - current_price) / current_price) * 100, 1),
                "stop_loss": round(stop_loss * 0.97, 2),
                "risk_pct": round(((current_price - (stop_loss * 0.97)) / current_price) * 100, 1),
            },
            "long_term": {
                "title": "بلندمدت (۶ تا ۱۲ ماه)",
                "strategy": "دید بنیادی، ارزش ذاتی و سود تقسیمی مجمع (DPS)",
                "target": round(target_2 * 1.25, 2),
                "expected_return_pct": round(((target_2 * 1.25 - current_price) / current_price) * 100, 1),
                "stop_loss": round(nearest_support * 0.92, 2),
                "risk_pct": round(((current_price - (nearest_support * 0.92)) / current_price) * 100, 1),
            },
        }

        return {
            "overall_verdict": verdict,
            "action_desc": action_desc,
            "current_price": current_price,
            "entry_zone": f"{entry_min:,.0f} تا {entry_max:,.0f} ریال",
            "target_1": target_1,
            "target_2": target_2,
            "stop_loss": stop_loss,
            "risk_reward_ratio": rr_ratio,
            "horizons": horizons,
        }
