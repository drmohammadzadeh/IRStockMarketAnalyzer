from typing import Dict, Any

class FinancialStatementsAnalyzer:
    @staticmethod
    def calculate_margins(
        revenue: float,
        cogs: float,
        operating_profit: float,
        net_profit: float
    ) -> Dict[str, float]:
        gross_profit = revenue - cogs
        return {
            "gross_margin_pct": round((gross_profit / revenue) * 100, 2) if revenue > 0 else 0.0,
            "operating_margin_pct": round((operating_profit / revenue) * 100, 2) if revenue > 0 else 0.0,
            "net_margin_pct": round((net_profit / revenue) * 100, 2) if revenue > 0 else 0.0
        }
