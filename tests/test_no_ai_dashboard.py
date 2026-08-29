from pathlib import Path
import pytest
from src.agents.technical_agent import TechnicalAnalystAgent
from src.reporting.markdown_generator import MarkdownReportGenerator


def test_technical_report_has_no_ai_dashboard_reference():
    agent = TechnicalAnalystAgent()
    content = agent.generate_report("وتجارت", {}, {}, [], [])
    assert "ai_dashboard.png" not in content
    assert "candlestick_overview.png" in content
    assert "indicators_momentum.png" in content
    assert "tape_reading_money_flow.png" in content


def test_markdown_generator_has_no_ai_dashboard_reference():
    gen = MarkdownReportGenerator()
    content = gen.generate_technical_report("وتجارت", {}, {})
    assert "ai_dashboard.png" not in content
    assert "candlestick_overview.png" in content
    assert "indicators_momentum.png" in content
    assert "tape_reading_money_flow.png" in content
