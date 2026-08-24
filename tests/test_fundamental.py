import pytest
from src.fundamental.valuation import ValuationAnalyzer
from src.fundamental.financial_statements import FinancialStatementsAnalyzer
from src.fundamental.monthly_sales import MonthlySalesAnalyzer

def test_valuation_multiples():
    result = ValuationAnalyzer.calculate_ratios(
        market_cap=5000_000_000_000,
        annual_revenue=8000_000_000_000,
        net_profit=1000_000_000_000,
        book_value=3000_000_000_000,
        last_dps=150,
        current_price=1200
    )
    assert result["pe_ratio"] == 5.0
    assert result["ps_ratio"] == 0.625
    assert result["pb_ratio"] == round(5000/3000, 3)
    assert result["dividend_yield_pct"] == 12.5
    assert result["fundamental_score"] > 5.0

def test_financial_margins():
    margins = FinancialStatementsAnalyzer.calculate_margins(
        revenue=1000,
        cogs=600,
        operating_profit=300,
        net_profit=250
    )
    assert margins["gross_margin_pct"] == 40.0
    assert margins["operating_margin_pct"] == 30.0
    assert margins["net_margin_pct"] == 25.0

def test_monthly_sales_trend():
    records = [{"amount": 100}, {"amount": 120}]
    trend = MonthlySalesAnalyzer.analyze_sales_trend(records)
    assert trend["growth_mom_pct"] == 20.0
    assert "صعودی" in trend["trend"]

def test_monthly_sales_trend_downtrend_and_empty():
    records_down = [{"amount": 100}, {"amount": 80}]
    trend_down = MonthlySalesAnalyzer.analyze_sales_trend(records_down)
    assert trend_down["growth_mom_pct"] == -20.0
    assert "نزولی" in trend_down["trend"]

    empty_trend = MonthlySalesAnalyzer.analyze_sales_trend([])
    assert empty_trend["growth_mom_pct"] == 0.0
    assert empty_trend["trend"] == "نامشخص"

    single_trend = MonthlySalesAnalyzer.analyze_sales_trend([{"amount": 100}])
    assert single_trend["growth_mom_pct"] == 0.0
    assert single_trend["trend"] == "باثبات"

def test_valuation_edge_cases():
    result = ValuationAnalyzer.calculate_ratios(
        market_cap=5000_000,
        annual_revenue=0,
        net_profit=-100,
        book_value=0,
        last_dps=0,
        current_price=0
    )
    assert result["pe_ratio"] == -1.0
    assert result["ps_ratio"] == -1.0
    assert result["pb_ratio"] == -1.0
    assert result["dividend_yield_pct"] == 0.0
