# سیستم امتیازدهی سه‌گانه توصیه خرید/فروش و به‌روزرسانی جامع سبد سهام Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Three-Tier 1-5 Buy/Sell Recommendation Scoring System ($S_1$ Multi-Factor Weighted, $S_2$ Decision Tree & Veto Rules, $S_3$ Multi-Horizon & Risk/Reward) across the analytics engine, embed scoring tables in all individual stock READMEs, generate a comprehensive comparative portfolio table in `سهام/README.md`, and refresh all analyzed stocks.

**Architecture:** 
- `StrategyAgent` in `src/agents/strategy_agent.py` computes $S_1, S_2, S_3, S_{\text{Final}}$ from fundamental, technical, tape reading, and news metrics.
- Reports generator embeds individual scoring tables in `final_recommendation.md` and `README.md` for each stock.
- Orchestrator updates `strategy_recommendation.json` and compiles the portfolio-wide ranking table in `سهام/README.md`.

**Tech Stack:** Python 3.13, Pandas, NumPy, Pytest, Matplotlib, JDateTime.

## Global Constraints
- All financial metrics scale in Million Rials (مبالغ به واحد میلیون ریال).
- Strict 1 to 5 scoring scale with star ratings (★★★★★).
- Educational, clear Persian explanations under all scoring tables and charts.
- Author attribution invariant: `نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir`.
- 100% pytest pass rate.

---

### Task 1: Three-Tier Scoring Engine in `src/agents/strategy_agent.py`

**Files:**
- Modify: `src/agents/strategy_agent.py`
- Test: `tests/test_strategy_agent.py`

**Interfaces:**
- Consumes: `tech_metrics: Dict[str, Any]`, `fund_metrics: Dict[str, Any]`, `news_summary: str`, `risk_reward: float`
- Produces: `calculate_three_tier_scores(...) -> Dict[str, Any]` containing `score_weighted`, `score_rules`, `score_horizon`, `score_final`, `stars`, `rationale`, `table_markdown`.

- [ ] **Step 1: Write failing unit test for three-tier scoring in `tests/test_strategy_agent.py`**
- [ ] **Step 2: Run pytest to verify failure**
- [ ] **Step 3: Implement `calculate_three_tier_scores` and integrate into `StrategyAgent.run` & `generate_recommendation_report`**
- [ ] **Step 4: Run `python -m pytest tests/test_strategy_agent.py` and verify PASS**
- [ ] **Step 5: Commit changes to git**

---

### Task 2: Portfolio-Wide Ranking Generator and Stock `README.md` Integration

**Files:**
- Modify: `src/reporting/markdown_generator.py`
- Modify: `src/orchestrator.py`
- Test: `tests/test_reporting.py`

**Interfaces:**
- Produces: `generate_portfolio_summary_table(stocks_data: List[Dict]) -> str`
- Updates: `سهام/README.md` with the unified comparative table of all analyzed stocks.

- [ ] **Step 1: Write failing test in `tests/test_reporting.py` for portfolio ranking table generator**
- [ ] **Step 2: Run pytest to verify failure**
- [ ] **Step 3: Implement `generate_portfolio_summary_table` and embed per-stock scoring table in `README.md`**
- [ ] **Step 4: Run `python -m pytest tests/test_reporting.py` and verify PASS**
- [ ] **Step 5: Commit changes to git**

---

### Task 3: Comprehensive Re-Analysis and Execution Across All Stocks

**Files:**
- Execute pipeline for: `تابان`, `کلید`, `وتجارت`, `تلیسه`, `خودرو`, `زهلال`, `فسازان`, `بانیان`
- Update: `سهام/<symbol>/README.md`, `سهام/<symbol>/final_recommendation.md`, `سهام/<symbol>/strategy_recommendation.json`
- Generate: `سهام/README.md` (Master Portfolio Dashboard)

- [ ] **Step 1: Run analysis / scoring on each stock and verify 10.0/10 quality scores**
- [ ] **Step 2: Verify scoring tables in each `سهام/<symbol>/README.md` and `final_recommendation.md`**
- [ ] **Step 3: Build master `سهام/README.md` with complete comparative ranking table**
- [ ] **Step 4: Verify all links and clickable paths**
- [ ] **Step 5: Commit updated stock reports to git**

---

### Task 4: Full Suite Testing, Self-Review, and GitHub Push

- [ ] **Step 1: Run full test suite `python -m pytest`**
- [ ] **Step 2: Check git diff and verify cleanliness**
- [ ] **Step 3: Push all commits to `origin/main`**
- [ ] **Step 4: Present results to user**
