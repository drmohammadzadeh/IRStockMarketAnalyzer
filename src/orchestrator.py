import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union

from src.config import STOCKS_DIR
from src.agents.crawler import CrawlerAgent
from src.agents.summarizer import SummarizerAgent
from src.agents.technical_agent import TechnicalAnalystAgent
from src.agents.fundamental_agent import FundamentalAnalystAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.inspector import QualityInspector


class MultiAgentOrchestrator:
    """Coordinates and executes the multi-agent stock market analysis pipeline

    with autonomous quality inspection gates and retry feedback loops.
    """

    def __init__(
        self,
        stocks_dir: Optional[Union[str, Path]] = None,
        crawler: Optional[CrawlerAgent] = None,
        summarizer: Optional[SummarizerAgent] = None,
        technical_analyst: Optional[TechnicalAnalystAgent] = None,
        fundamental_analyst: Optional[FundamentalAnalystAgent] = None,
        strategy_agent: Optional[StrategyAgent] = None,
        inspector: Optional[QualityInspector] = None,
    ):
        self.stocks_dir = Path(stocks_dir or STOCKS_DIR)
        self.crawler = crawler or CrawlerAgent()
        self.summarizer = summarizer or SummarizerAgent()
        self.technical_analyst = technical_analyst or TechnicalAnalystAgent()
        self.fundamental_analyst = fundamental_analyst or FundamentalAnalystAgent()
        self.strategy_agent = strategy_agent or StrategyAgent()
        self.inspector = inspector or QualityInspector()

    def run_pipeline(self, symbol: str, max_retries: int = 3) -> bool:
        """Executes the complete multi-stage analysis pipeline for a given symbol:

        1. Crawler stage (Codal, news, market history) -> inspect_stage("crawler")
        2. Summarizer stage (Codal & news summarization) -> inspect_stage("summarizer")
        3. Analysts stage (Technical & Fundamental) -> inspect_stage("analysts")
        4. Strategy stage (Multi-horizon synthesis & recommendation) -> inspect_stage("strategy")

        Returns:
            bool: True if all stages completed and passed quality inspection, False otherwise.
        """
        symbol_clean = str(symbol).strip()
        if not symbol_clean:
            print("[!] نام نماد معتبر نیست.")
            return False

        symbol_dir = self.stocks_dir / symbol_clean
        symbol_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n=======================================================")
        print(f"  شروع پایپ‌لاین تحلیل چندعاملی (Multi-Agent) برای نماد: {symbol_clean}")
        print(f"=======================================================")

        # Stage 1: Crawler
        print(f"\n[۱/۴] اجرای عامل خزش و دریافت داده‌ها (Crawler Agent)...")
        crawler_passed = False
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  ◀ تلاش {attempt} از {max_retries} برای دریافت اطلاعات...")
                self.crawler.run(symbol_clean, symbol_dir)
                inspection = self.inspector.inspect_stage("crawler", symbol_dir)
                print(f"  ◀ بازرسی کیفیت: امتیاز {inspection.score}/10 | وضعیت: {'تأیید' if inspection.is_passed else 'رد'}")
                if inspection.is_passed:
                    crawler_passed = True
                    break
                else:
                    if inspection.defects:
                        print(f"  [!] نواقص شناسایی‌شده: {', '.join(inspection.defects)}")
            except Exception as e:
                print(f"  [!] خطای غیرمنتظره در اجرای Crawler: {e}")

        if not crawler_passed:
            print(f"  [✗] مرحله خزش و دریافت داده‌ها پس از {max_retries} تلاش ناموفق بود.")
            return False

        # Stage 2: Summarizer
        print(f"\n[۲/۴] اجرای عامل تلخیص و پردازش گزارش‌ها (Summarizer Agent)...")
        summarizer_passed = False
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  ◀ تلاش {attempt} از {max_retries} برای خلاصه‌سازی...")
                self.summarizer.run(symbol_clean, symbol_dir)
                inspection = self.inspector.inspect_stage("summarizer", symbol_dir)
                print(f"  ◀ بازرسی کیفیت: امتیاز {inspection.score}/10 | وضعیت: {'تأیید' if inspection.is_passed else 'رد'}")
                if inspection.is_passed:
                    summarizer_passed = True
                    break
                else:
                    if inspection.defects:
                        print(f"  [!] نواقص شناسایی‌شده: {', '.join(inspection.defects)}")
            except Exception as e:
                print(f"  [!] خطای غیرمنتظره در اجرای Summarizer: {e}")

        if not summarizer_passed:
            print(f"  [✗] مرحله خلاصه‌سازی و پردازش گزارش‌ها پس از {max_retries} تلاش ناموفق بود.")
            return False

        # Stage 3: Analysts (Technical + Fundamental)
        print(f"\n[۳/۴] اجرای عامل‌های تحلیل تکنیکال و بنیادی (Analysts Agents)...")
        analysts_passed = False
        tech_metrics: Dict[str, Any] = {}
        fund_metrics: Dict[str, Any] = {}
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  ◀ تلاش {attempt} از {max_retries} برای تحلیل تکنیکال و بنیادی...")
                tech_res = self.technical_analyst.run(symbol_clean, symbol_dir)
                tech_metrics = tech_res.get("metrics", {}) if isinstance(tech_res, dict) else {}
                current_price = float(tech_metrics.get("current_price", 0.0))

                fund_res = self.fundamental_analyst.run(symbol_clean, symbol_dir, current_price=current_price)
                fund_metrics = fund_res.get("metrics", {}) if isinstance(fund_res, dict) else {}

                inspection = self.inspector.inspect_stage("analysts", symbol_dir)
                print(f"  ◀ بازرسی کیفیت: امتیاز {inspection.score}/10 | وضعیت: {'تأیید' if inspection.is_passed else 'رد'}")
                if inspection.is_passed:
                    analysts_passed = True
                    break
                else:
                    if inspection.defects:
                        print(f"  [!] نواقص شناسایی‌شده: {', '.join(inspection.defects)}")
            except Exception as e:
                print(f"  [!] خطای غیرمنتظره در اجرای Analysts: {e}")

        if not analysts_passed:
            print(f"  [✗] مرحله تحلیل تکنیکال و بنیادی پس از {max_retries} تلاش ناموفق بود.")
            return False

        # Stage 4: Strategy
        print(f"\n[۴/۴] اجرای عامل تدوین استراتژی و تصمیم‌گیری (Strategy Agent)...")
        strategy_passed = False
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  ◀ تلاش {attempt} از {max_retries} برای تدوین استراتژی...")
                self.strategy_agent.run(
                    symbol_clean,
                    symbol_dir,
                    tech_metrics=tech_metrics,
                    fund_metrics=fund_metrics,
                )
                inspection = self.inspector.inspect_stage("strategy", symbol_dir)
                print(f"  ◀ بازرسی کیفیت: امتیاز {inspection.score}/10 | وضعیت: {'تأیید' if inspection.is_passed else 'رد'}")
                if inspection.is_passed:
                    strategy_passed = True
                    break
                else:
                    if inspection.defects:
                        print(f"  [!] نواقص شناسایی‌شده: {', '.join(inspection.defects)}")
            except Exception as e:
                print(f"  [!] خطای غیرمنتظره در اجرای Strategy: {e}")

        if not strategy_passed:
            print(f"  [✗] مرحله تدوین استراتژی پس از {max_retries} تلاش ناموفق بود.")
            return False

        print(f"\n=======================================================")
        print(f"  [✓] پایپ‌لاین تحلیل چندعاملی نماد {symbol_clean} با موفقیت کامل انجام شد.")
        print(f"  گزارش‌ها و خروجی‌ها در مسیر زیر ذخیره شدند:")
        print(f"    - گزارش تکنیکال: {symbol_dir / 'technical_report.md'}")
        print(f"    - گزارش بنیادی: {symbol_dir / 'fundamental_report.md'}")
        print(f"    - راهنمای استراتژی: {symbol_dir / 'final_recommendation.md'}")
        print(f"    - نمودارها: {symbol_dir / 'charts'}")
        print(f"=======================================================\n")

        return True
