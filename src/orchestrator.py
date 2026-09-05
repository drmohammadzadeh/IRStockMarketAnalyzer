# Website: tjb24.ir
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
from src.agents.judge import JudgeAgent, JudgementVerdict
from src.agents.frontend_agent import FrontendAgent


class MultiAgentOrchestrator:
    """Coordinates and executes the multi-agent stock market analysis pipeline

    with autonomous quality inspection gates, Supreme Judge arbitration rubric,
    and self-remedial retry feedback loops.
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
        judge: Optional[JudgeAgent] = None,
        frontend_agent: Optional[FrontendAgent] = None,
    ):
        self.stocks_dir = Path(stocks_dir or STOCKS_DIR)
        self.crawler = crawler or CrawlerAgent()
        self.summarizer = summarizer or SummarizerAgent()
        self.technical_analyst = technical_analyst or TechnicalAnalystAgent()
        self.fundamental_analyst = fundamental_analyst or FundamentalAnalystAgent()
        self.strategy_agent = strategy_agent or StrategyAgent()
        self.inspector = inspector or QualityInspector()
        self.judge = judge or JudgeAgent()
        self.frontend_agent = frontend_agent or FrontendAgent(stocks_dir=self.stocks_dir)

    def _embed_arbitration_certificate(self, symbol_clean: str, symbol_dir: Path, certificate_markdown: str) -> None:
        """Injects the official Persian Arbitration Certificate into final_recommendation.md and README.md."""
        if not certificate_markdown:
            return

        final_rec_file = symbol_dir / "final_recommendation.md"
        if final_rec_file.exists():
            try:
                rec_text = final_rec_file.read_text(encoding="utf-8")
                if "گواهی رسمی داوری و ممیزی نهایی" not in rec_text:
                    marker = "## ⚠️ سلب مسئولیت حقوقی و مالی"
                    if marker in rec_text:
                        parts = rec_text.split(marker, 1)
                        new_text = parts[0].rstrip() + "\n\n---\n\n" + certificate_markdown.strip() + "\n\n---\n\n" + marker + parts[1]
                        final_rec_file.write_text(new_text, encoding="utf-8")
                    else:
                        final_rec_file.write_text(f"{rec_text.rstrip()}\n\n---\n\n{certificate_markdown}\n", encoding="utf-8")
            except Exception as e:
                print(f"  [!] خطا در الصاق گواهی به final_recommendation.md: {e}")

        readme_file = symbol_dir / "README.md"
        try:
            if readme_file.exists():
                readme_text = readme_file.read_text(encoding="utf-8")
                if "گواهی رسمی داوری و ممیزی نهایی" not in readme_text:
                    marker = "## ⚠️ سلب مسئولیت حقوقی و مالی"
                    if marker in readme_text:
                        parts = readme_text.split(marker, 1)
                        new_text = parts[0].rstrip() + "\n\n---\n\n" + certificate_markdown.strip() + "\n\n---\n\n" + marker + parts[1]
                        readme_file.write_text(new_text, encoding="utf-8")
                    else:
                        readme_file.write_text(f"{readme_text.rstrip()}\n\n---\n\n{certificate_markdown}\n", encoding="utf-8")
            else:
                readme_file.write_text(f"# نماد {symbol_clean}\n\n{certificate_markdown}\n", encoding="utf-8")
        except Exception as e:
            print(f"  [!] خطا در الصاق گواهی به README.md: {e}")

    def run_pipeline(self, symbol: str, max_retries: int = 3) -> bool:
        """Executes the complete multi-stage analysis pipeline for a given symbol:

        1. Crawler stage (Codal, news, social sentiment, market history) -> inspect_stage("crawler")
        2. Summarizer stage (Codal & news/sentiment summarization) -> inspect_stage("summarizer")
        3. Analysts stage (Technical & Fundamental) -> inspect_stage("analysts")
        4. Strategy stage (Multi-horizon synthesis & recommendation) -> inspect_stage("strategy")
        5. Supreme Arbitration stage (5-Pillar Rubric & Remediation) -> judge.audit_symbol

        Returns:
            bool: True if all stages completed and approved by Supreme Judge, False otherwise.
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

        for arbitration_attempt in range(1, max_retries + 1):
            if arbitration_attempt > 1:
                print(f"\n=======================================================")
                print(f"  🔄 اجرای مجدد پایپ‌لاین بر اساس بازخورد داور (تلاش {arbitration_attempt} از {max_retries})")
                print(f"=======================================================")

            # Stage 1: Crawler
            print(f"\n[۱/۵] اجرای عامل خزش و دریافت داده‌ها (Crawler Agent)...")
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
            print(f"\n[۲/۵] اجرای عامل تلخیص و پردازش گزارش‌ها (Summarizer Agent)...")
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
            print(f"\n[۳/۵] اجرای عامل‌های تحلیل تکنیکال و بنیادی (Analysts Agents)...")
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
            print(f"\n[۴/۵] اجرای عامل تدوین استراتژی و تصمیم‌گیری (Strategy Agent)...")
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

            # Stage 5: Supreme Arbitration (Judge Agent)
            print(f"\n[۵/۵] ممیزی عالی و داوری پنج‌گانه ارکان گزارش (Supreme Judge Agent)...")
            try:
                verdict = self.judge.audit_symbol(symbol_clean, symbol_dir)
                status_fa = "تأیید نهایی (APPROVED)" if verdict.is_approved else "مردود و نیازمند اصلاح (REJECTED)"
                print(f"  ◀ کارنامه داوری: نمره مکتسبه {verdict.score}/10.0 | وضعیت: {status_fa}")

                if verdict.is_approved:
                    self._embed_arbitration_certificate(symbol_clean, symbol_dir, verdict.certificate_markdown)

                    # Realtime watchlist sync
                    try:
                        self.frontend_agent.update_single_stock(symbol_clean)
                        print(f"  ⚡ داده‌های نماد {symbol_clean} در پایگاه داده واچ‌لیست (stocks.json و stocks.js) بروزرسانی شد.")
                    except Exception as e:
                        print(f"  [!] هشدار در بروزرسانی خودکار واچ‌لیست نماد {symbol_clean}: {e}")

                    print(f"\n=======================================================")
                    print(f"  🛡️ پایپ‌لاین تحلیل نماد {symbol_clean} با احراز نمره {verdict.score}/10 مورد تأیید رسمی داور قرار گرفت.")
                    print(f"  گزارش‌ها و گواهی داوری در مسیرهای زیر ذخیره گردیدند:")
                    print(f"    - گزارش تکنیکال: {symbol_dir / 'technical_report.md'}")
                    print(f"    - گزارش بنیادی: {symbol_dir / 'fundamental_report.md'}")
                    print(f"    - راهنمای استراتژی و گواهی داوری: {symbol_dir / 'final_recommendation.md'}")
                    print(f"    - داشبورد سهم: {symbol_dir / 'README.md'}")
                    print(f"    - نمودارها: {symbol_dir / 'charts'}")
                    print(f"=======================================================\n")
                    return True
                else:
                    if verdict.critical_defects:
                        print(f"  🚨 نقص‌های بحرانی داوری:")
                        for d in verdict.critical_defects:
                            print(f"    - {d}")
                    if verdict.remedial_actions:
                        print(f"  🛠️ اقدامات اصلاحی تجویزی داور:")
                        for idx, a in enumerate(verdict.remedial_actions, 1):
                            print(f"    {idx}. {a}")

                    if arbitration_attempt < max_retries:
                        print(f"  🔄 آغاز چرخه خودترمیمی و اجرای مجدد...")
            except Exception as e:
                print(f"  [!] خطای غیرمنتظره در اجرای Judge Agent: {e}")

        print(f"\n=======================================================")
        print(f"  [✗] پایپ‌لاین تحلیل نماد {symbol_clean} پس از {max_retries} تلاش موفق به جلب تأیید داور نشد.")
        print(f"=======================================================\n")
        return False
