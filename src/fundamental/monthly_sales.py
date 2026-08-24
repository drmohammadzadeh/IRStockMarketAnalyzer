from typing import Dict, Any, List

class MonthlySalesAnalyzer:
    @staticmethod
    def analyze_sales_trend(monthly_sales_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not monthly_sales_records:
            return {"status": "No monthly data available", "trend": "نامشخص", "growth_mom_pct": 0.0}
        
        amounts = [r.get("amount", 0) for r in monthly_sales_records if "amount" in r]
        if len(amounts) >= 2:
            latest = amounts[-1]
            prev = amounts[-2]
            growth = round(((latest - prev) / prev) * 100, 2) if prev > 0 else 0.0
            trend = "صعودی (رشد فروش)" if growth > 5 else ("نزولی (کاهش فروش)" if growth < -5 else "باثبات")
            return {
                "latest_month_amount": latest,
                "growth_mom_pct": growth,
                "trend": trend
            }
        return {"status": "Single month record", "trend": "باثبات", "growth_mom_pct": 0.0}
