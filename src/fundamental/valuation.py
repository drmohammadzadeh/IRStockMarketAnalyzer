from typing import Dict, Any

class ValuationAnalyzer:
    @staticmethod
    def calculate_ratios(
        market_cap: float,
        annual_revenue: float,
        net_profit: float,
        book_value: float,
        last_dps: float,
        current_price: float
    ) -> Dict[str, Any]:
        pe = round(market_cap / net_profit, 2) if net_profit > 0 else -1.0
        ps = round(market_cap / annual_revenue, 3) if annual_revenue > 0 else -1.0
        pb = round(market_cap / book_value, 3) if book_value > 0 else -1.0
        div_yield = round((last_dps / current_price) * 100, 2) if current_price > 0 else 0.0
        
        # Rating 1-10
        score = 5.0
        if 0 < pe < 6.0:
            score += 2.0
        elif 6.0 <= pe <= 8.5:
            score += 1.0
        elif pe > 15:
            score -= 1.5
            
        if 0 < ps < 1.5:
            score += 1.5
        if div_yield >= 10.0:
            score += 1.5

        score = max(1.0, min(10.0, score))

        return {
            "pe_ratio": pe,
            "ps_ratio": ps,
            "pb_ratio": pb,
            "dividend_yield_pct": div_yield,
            "fundamental_score": round(score, 1)
        }
