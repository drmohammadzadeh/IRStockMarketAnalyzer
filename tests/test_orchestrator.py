import json
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
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])), \
         patch("src.agents.judge.JudgeAgent.audit_symbol", return_value=MagicMock(is_approved=True, score=9.5, critical_defects=[], remedial_actions=[], certificate_markdown="### 🏛️ گواهی داوری")):

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
         patch("src.agents.inspector.QualityInspector.inspect_stage", side_effect=lambda stage, p: inspection_results.pop(0) if stage == "crawler" and inspection_results else MagicMock(is_passed=True, score=9.0, defects=[])), \
         patch("src.agents.judge.JudgeAgent.audit_symbol", return_value=MagicMock(is_approved=True, score=9.5, critical_defects=[], remedial_actions=[], certificate_markdown="### 🏛️ گواهی داوری")):

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
         patch("src.agents.inspector.QualityInspector.inspect_stage", side_effect=mock_inspect), \
         patch("src.agents.judge.JudgeAgent.audit_symbol", return_value=MagicMock(is_approved=True, score=9.5, critical_defects=[], remedial_actions=[], certificate_markdown="### 🏛️ گواهی داوری")):

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
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])), \
         patch("src.agents.judge.JudgeAgent.audit_symbol", return_value=MagicMock(is_approved=True, score=9.5, critical_defects=[], remedial_actions=[], certificate_markdown="### 🏛️ گواهی داوری")):

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


def test_orchestrator_judge_approval_and_certificate_attachment(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "کلید"
    symbol_dir.mkdir(parents=True)

    final_rec_file = symbol_dir / "final_recommendation.md"
    final_rec_file.write_text("# گزارش راهنمای استراتژی\n", encoding="utf-8")

    readme_file = symbol_dir / "README.md"
    readme_file.write_text("# داشبورد نماد کلید\n", encoding="utf-8")

    judge_mock = MagicMock()
    certificate_text = "## 🏛️ گواهی رسمی داوری و ممیزی نهایی نماد کلید\n- **وضعیت:** APPROVED"
    judge_mock.audit_symbol.return_value = MagicMock(
        is_approved=True,
        score=9.6,
        status="APPROVED",
        critical_defects=[],
        remedial_actions=[],
        certificate_markdown=certificate_text,
    )

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir, judge=judge_mock)

    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("کلید", max_retries=2)
        assert success is True
        judge_mock.audit_symbol.assert_called_once_with("کلید", symbol_dir)

        # Check certificate attached to final_recommendation.md and README.md
        final_content = final_rec_file.read_text(encoding="utf-8")
        assert "گواهی رسمی داوری و ممیزی نهایی نماد کلید" in final_content

        readme_content = readme_file.read_text(encoding="utf-8")
        assert "گواهی رسمی داوری و ممیزی نهایی نماد کلید" in readme_content


def test_orchestrator_judge_rejection_triggers_remediation_retry(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "نوری"
    symbol_dir.mkdir(parents=True)

    final_rec_file = symbol_dir / "final_recommendation.md"
    final_rec_file.write_text("# راهبرد\n", encoding="utf-8")

    judge_mock = MagicMock()
    verdict_fail = MagicMock(
        is_approved=False,
        score=7.2,
        status="REJECTED",
        critical_defects=["فایل‌های معیوب در کدال"],
        remedial_actions=["پاکسازی فایل‌های خراب و دانلود مجدد"],
        certificate_markdown="## گواهی رد",
    )
    verdict_pass = MagicMock(
        is_approved=True,
        score=9.2,
        status="APPROVED",
        critical_defects=[],
        remedial_actions=[],
        certificate_markdown="## 🏛️ گواهی رسمی داوری و ممیزی نهایی نماد نوری",
    )
    judge_mock.audit_symbol.side_effect = [verdict_fail, verdict_pass]

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir, judge=judge_mock)

    crawler_mock = MagicMock(return_value={"success": True})
    with patch("src.agents.crawler.CrawlerAgent.run", crawler_mock), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("نوری", max_retries=3)
        assert success is True
        assert judge_mock.audit_symbol.call_count == 2
        assert crawler_mock.call_count == 2
        assert "گواهی رسمی داوری و ممیزی نهایی نماد نوری" in final_rec_file.read_text(encoding="utf-8")


def test_orchestrator_judge_persistent_rejection_fails_pipeline(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "زاگرس"
    symbol_dir.mkdir(parents=True)

    judge_mock = MagicMock()
    verdict_fail = MagicMock(
        is_approved=False,
        score=6.0,
        status="REJECTED",
        critical_defects=["فایل سابقه معاملات خالی است"],
        remedial_actions=["دریافت سابقه معاملات"],
        certificate_markdown="## گواهی رد",
    )
    judge_mock.audit_symbol.return_value = verdict_fail

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir, judge=judge_mock)

    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("زاگرس", max_retries=2)
        assert success is False
        assert judge_mock.audit_symbol.call_count == 2


def test_crawler_agent_integrates_social_sentiment_crawler(tmp_path):
    symbol_dir = tmp_path / "سهام" / "کلید"
    symbol_dir.mkdir(parents=True)

    from src.agents.crawler import CrawlerAgent
    crawler = CrawlerAgent()
    mock_social = MagicMock()
    mock_social.crawl_and_save.return_value = {"success": True, "data": {"composite_sentiment_score": 8.0}}
    crawler.social_crawler = mock_social

    with patch.object(crawler, "_fetch_codal_letters", return_value=[]), \
         patch.object(crawler, "_fetch_news", return_value=[]), \
         patch.object(crawler, "_fetch_market_data", return_value=(MagicMock(empty=True), {})):

        res = crawler.run("کلید", symbol_dir)
        assert res["success"] is True
        mock_social.crawl_and_save.assert_called_once_with("کلید", symbol_dir)


def test_summarizer_agent_includes_social_sentiment_section(tmp_path):
    symbol_dir = tmp_path / "سهام" / "کلید"
    news_dir = symbol_dir / "news"
    news_dir.mkdir(parents=True)

    sentiment_payload = {
        "symbol": "کلید",
        "composite_sentiment_score": 8.5,
        "sentiment_verdict": "خوش‌بینی بالا در میان سهامداران خرد",
        "sahamyab": {"total_posts": 12, "bullish_count": 9, "bearish_count": 1, "neutral_count": 2, "sample_comments": ["صف خرید سنگین"]},
        "rahavard365": {"total_posts": 8, "bullish_count": 6, "bearish_count": 1, "neutral_count": 1, "sample_comments": ["تارگت اول تاچ شد"]},
    }
    (news_dir / "social_sentiment.json").write_text(json.dumps(sentiment_payload, ensure_ascii=False), encoding="utf-8")

    from src.agents.summarizer import SummarizerAgent
    summarizer = SummarizerAgent()
    res = summarizer.run("کلید", symbol_dir)

    assert res["success"] is True
    news_summary = (news_dir / "news_summary.md").read_text(encoding="utf-8")
    assert "تحلیل جو روانی و دیدگاه‌های سهامداران در شبکه‌های اجتماعی (سهام‌یاب و ره‌آورد ۳۶۰)" in news_summary
    assert "8.5" in news_summary or "۸.۵" in news_summary
    assert "خوش‌بینی بالا" in news_summary


def test_strategy_agent_incorporates_social_sentiment(tmp_path):
    symbol_dir = tmp_path / "سهام" / "کلید"
    news_dir = symbol_dir / "news"
    news_dir.mkdir(parents=True)

    sentiment_payload = {
        "symbol": "کلید",
        "composite_sentiment_score": 9.0,
        "sentiment_verdict": "خوش‌بینی بالا",
    }
    (news_dir / "social_sentiment.json").write_text(json.dumps(sentiment_payload, ensure_ascii=False), encoding="utf-8")

    from src.agents.strategy_agent import StrategyAgent
    agent = StrategyAgent()
    res = agent.run(
        "کلید",
        symbol_dir,
        tech_metrics={"current_price": 2000.0, "ema20": 1900.0, "ema50": 1800.0, "rsi": 50.0, "buyer_power": 1.5},
        fund_metrics={"fundamental_score": 8.0, "pe_ratio": 6.0, "dividend_yield_pct": 12.0},
    )
    assert res["success"] is True
    plan = res["plan"]
    assert plan["scoring"]["sub_metrics"]["s_news"] >= 7.0


def test_orchestrator_updates_watchlist_on_approval(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "کلید"
    symbol_dir.mkdir(parents=True)

    judge_mock = MagicMock()
    judge_mock.audit_symbol.return_value = MagicMock(
        is_approved=True,
        score=9.5,
        critical_defects=[],
        remedial_actions=[],
        certificate_markdown="## 🏛️ گواهی داوری",
    )
    frontend_mock = MagicMock()

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir, judge=judge_mock, frontend_agent=frontend_mock)

    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("کلید", max_retries=1)
        assert success is True
        frontend_mock.update_single_stock.assert_called_once_with("کلید")


def test_orchestrator_non_blocking_on_watchlist_error(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "کلید"
    symbol_dir.mkdir(parents=True)

    judge_mock = MagicMock()
    judge_mock.audit_symbol.return_value = MagicMock(
        is_approved=True,
        score=9.5,
        critical_defects=[],
        remedial_actions=[],
        certificate_markdown="## 🏛️ گواهی داوری",
    )
    frontend_mock = MagicMock()
    frontend_mock.update_single_stock.side_effect = RuntimeError("Simulated write error")

    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir, judge=judge_mock, frontend_agent=frontend_mock)

    with patch("src.agents.crawler.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.agents.summarizer.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.agents.technical_agent.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.agents.fundamental_agent.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.agents.strategy_agent.StrategyAgent.run", return_value={"success": True}), \
         patch("src.agents.inspector.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):

        success = orch.run_pipeline("کلید", max_retries=1)
        assert success is True
        frontend_mock.update_single_stock.assert_called_once_with("کلید")

