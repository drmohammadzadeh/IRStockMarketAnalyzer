import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.orchestrator import MultiAgentOrchestrator
import main


def test_orchestrator_pipeline_success(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "زهلال"
    symbol_dir.mkdir(parents=True)

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir)
    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("زهلال")
        assert success is True


def test_orchestrator_retries_on_inspection_failure(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "زهلال"
    symbol_dir.mkdir(parents=True)

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir)
    crawler_calls = 0

    def mock_crawler(*args, **kwargs):
        nonlocal crawler_calls
        crawler_calls += 1
        return {"success": True}

    inspection_results = [
        MagicMock(is_passed=False, score=6.0, defects=["Missing file"], feedback="Retry needed"),
        MagicMock(is_passed=True, score=9.0, defects=[], feedback="Passed"),
    ]

    with patch("src.agents.crawler.CrawlerAgent.run", side_effect=mock_crawler), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", side_effect=lambda stage, p: inspection_results.pop(0) if stage == "crawler" and inspection_results else MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("زهلال", max_retries=3)
        assert success is True
        assert crawler_calls == 2


def test_orchestrator_retry_exhaustion_fails(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "فولاد"
    symbol_dir.mkdir(parents=True)

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir)
    summarizer_calls = 0

    def mock_summarizer(*args, **kwargs):
        nonlocal summarizer_calls
        summarizer_calls += 1
        return {"success": True}

    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", side_effect=mock_summarizer), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", side_effect=lambda stage, p: MagicMock(is_passed=False, score=5.0, defects=["Bad summary"], feedback="Fail") if stage == "summarizer" else MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("فولاد", max_retries=3)
        assert success is False
        assert summarizer_calls == 3


def test_orchestrator_analysts_and_strategy_retry(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "شپنا"
    symbol_dir.mkdir(parents=True)

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir)

    analysts_inspection = [
        MagicMock(is_passed=False, score=6.0, defects=["Chart missing"], feedback="Retry chart"),
        MagicMock(is_passed=True, score=9.5, defects=[], feedback="Passed"),
    ]

    strategy_inspection = [
        MagicMock(is_passed=False, score=7.0, defects=["Incomplete plan"], feedback="Retry plan"),
        MagicMock(is_passed=True, score=9.0, defects=[], feedback="Passed"),
    ]

    def mock_inspect(stage, path):
        if stage == "analysts" and analysts_inspection:
            return analysts_inspection.pop(0)
        if stage == "strategy" and strategy_inspection:
            return strategy_inspection.pop(0)
        return MagicMock(is_passed=True, score=10.0, defects=[])

    tech_mock = MagicMock(return_value={"success": True, "metrics": {"current_price": 5000.0}})
    fund_mock = MagicMock(return_value={"success": True, "metrics": {"fundamental_score": 8.5}})
    strat_mock = MagicMock(return_value={"success": True})

    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", tech_mock), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", fund_mock), \
         patch("src.agents.strategy_agent.StrategyAgent.run", strat_mock), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", side_effect=mock_inspect):

        success = orch.run_pipeline("شپنا", max_retries=3)
        assert success is True
        assert tech_mock.call_count == 2
        assert fund_mock.call_count == 2
        assert strat_mock.call_count == 2
        # Check metrics propagation
        strat_mock.assert_called_with(
            "شپنا",
            symbol_dir,
            tech_metrics={"current_price": 5000.0},
            fund_metrics={"fundamental_score": 8.5},
        )


def test_orchestrator_handles_agent_exception(tmp_path):
    stocks_dir = tmp_path / "سهام"
    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir)

    crawler_calls = 0
    def faulty_crawler(*args, **kwargs):
        nonlocal crawler_calls
        crawler_calls += 1
        if crawler_calls == 1:
            raise RuntimeError("Network glitch")
        return {"success": True}

    with patch("src.agents.crawler.CrawlerAgent.run", side_effect=faulty_crawler), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("کگل", max_retries=2)
        assert success is True
        assert crawler_calls == 2


def test_main_analyze_symbol_delegation(tmp_path):
    with patch("main.MultiAgentOrchestrator") as mock_orch_cls:
        mock_orch = MagicMock()
        mock_orch.run_pipeline.return_value = True
        mock_orch_cls.return_value = mock_orch

        result = main.analyze_symbol("زهلال", stocks_dir=tmp_path, max_retries=2)
        assert result is True
        mock_orch_cls.assert_called_once_with(stocks_dir=tmp_path)
        mock_orch.run_pipeline.assert_called_once_with("زهلال", max_retries=2)
