# Minimal, Aesthetic & Responsive Stock Listing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the stock listing page into a minimal, aesthetic, and fully responsive 4-zone card interface across desktop, tablet, and mobile devices (height < 200px on mobile, zero horizontal overflow, unified AI hero score pill, clean sparkline, and quick actions dropdown).

**Architecture:** 
- CSS Tokens & Grid (`browser/styles.css` & `browser/style.css`): Modern OLED dark theme tokens, CSS Grid with responsive breakpoints (3 cols on desktop >= 1024px, 2 cols on tablet 768px-1023px, 1 col on mobile < 768px), hairline subtle borders, smooth micro-interactions.
- JavaScript Component Rendering (`browser/app.js`): Streamlined `renderStockCard` emitting the 4-zone layout, unified Hero AI Pill wired to Explainability Modal, minimalist 14-day micro-sparkline, and a floating quick-actions dropdown.
- Mobile-First Layout & Responsiveness: Header two-tier adaptation, touch targets >= 44px, tabular numeral alignment, zero horizontal overflow.

**Tech Stack:** Vanilla JavaScript (ES6+), CSS Grid/Flexbox, Chart.js / SVG Sparkline, Lucide Icons, Headless Chrome Selenium / DOM testing.

**Spec:** `docs/superpowers/specs/2026-10-11-minimal-responsive-stock-list-design.md`

## Global Constraints

- **Zero Breaking Changes:** All existing modal triggers (`openExplainabilityModal`, `openSummaryModal`, `openLiveReporter`), favorites, search, sort, and filter workflows must remain 100% functional.
- **Twin Stylesheet Parity:** `browser/styles.css` and `browser/style.css` must remain strictly identical.
- **Strict Responsiveness:** Zero horizontal overflow on mobile viewports (tested at 375px); card height on mobile must stay below 200px (down from 750px+).
- **Accessibility & Touch:** All tappable controls must have touch targets >= 44x44px; primary text contrast >= 4.5:1.

---

### Task 1: CSS Minimal Tokens, 4-Zone Card Layout & Dropdown Menus

**Files:**
- Modify: `browser/styles.css`
- Modify: `browser/style.css`
- Test: `tests/test_ui_minimal_tokens.py` (DOM/CSS parsing verification)

**Interfaces:**
- Produces: CSS classes `.stock-card`, `.card-zone-header`, `.card-zone-hero`, `.ai-hero-pill`, `.sparkline-wrap`, `.card-zone-stats`, `.card-zone-actions`, `.quick-actions-dropdown`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ui_minimal_tokens.py`:
```python
# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
from pathlib import Path
import re
import pytest

def test_styles_have_minimal_tokens_and_parity():
    s1 = Path("browser/styles.css").read_text(encoding="utf-8")
    s2 = Path("browser/style.css").read_text(encoding="utf-8")

    # Verify parity
    assert s1 == s2, "styles.css and style.css must be identical"

    # Verify key tokens and classes exist
    required_tokens = [
        "--bg-app",
        "--surface-card",
        "--surface-card-hover",
        "--border-subtle",
        "--color-ai-hero",
    ]
    for token in required_tokens:
        assert token in s1, f"Missing design token: {token}"

    required_classes = [
        ".card-zone-header",
        ".card-zone-hero",
        ".ai-hero-pill",
        ".card-zone-stats",
        ".card-zone-actions",
        ".quick-actions-menu",
    ]
    for cls in required_classes:
        assert cls in s1, f"Missing CSS class: {cls}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui_minimal_tokens.py -v`  
Expected: FAIL (missing CSS classes and tokens)

- [ ] **Step 3: Implement minimal styles in `styles.css` and `style.css`**

Add root tokens and 4-zone card styling:
- Define `:root` tokens: `--bg-app: #020617;`, `--surface-card: #0f172a;`, `--surface-card-hover: #1e293b;`, `--border-subtle: rgba(255, 255, 255, 0.08);`, `--color-ai-hero: #8b5cf6;`, etc.
- Style `.stocks-container` as CSS Grid (`display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.25rem;`).
- Style `.stock-card` with sleek border, border-radius 14px, padding 1rem, subtle hover lift.
- Style `.card-zone-header`: flex row with avatar, symbol, company name, live price, change badge, favorite star.
- Style `.card-zone-hero`: flex row containing `.ai-hero-pill` (score, label, 4 indicator dots) and `.sparkline-wrap`.
- Style `.card-zone-stats`: sleek horizontal flex/grid row with 4 metrics (market cap, volume, P/E, money flow).
- Style `.card-zone-actions`: flex row with `.btn-live-avatar`, `.btn-summary-minimal`, and `.btn-quick-actions` toggle.
- Style `.quick-actions-menu`: absolute positioned sleek glass dropdown with links to TSETMC, Rahavard, Codal, GitHub, and Reanalyze.
- Copy `browser/styles.css` exactly to `browser/style.css`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ui_minimal_tokens.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(ui): add minimal OLED design tokens and 4-zone card layout styles"
```

---

### Task 2: JavaScript 4-Zone Card Template & Micro-Sparkline

**Files:**
- Modify: `browser/app.js`
- Test: `tests/test_ui_app_rendering.py`

**Interfaces:**
- Produces: `renderStockCard(stock)` returning 4-zone minimal article element with interactive listeners.
- Produces: `renderMiniSparkline(canvas, dataPoints, isPositive)` rendering clean minimal trendline.
- Produces: Quick actions menu toggle & click-outside listener.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ui_app_rendering.py`:
```python
# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
from pathlib import Path
import pytest

def test_app_js_contains_4_zone_card_rendering():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    assert "card-zone-header" in app_js
    assert "card-zone-hero" in app_js
    assert "ai-hero-pill" in app_js
    assert "card-zone-stats" in app_js
    assert "card-zone-actions" in app_js
    assert "quick-actions-menu" in app_js
    assert "openExplainabilityModal" in app_js
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui_app_rendering.py -v`  
Expected: FAIL (missing 4-zone elements in app.js)

- [ ] **Step 3: Refactor `renderStockCard` in `browser/app.js`**

- In `browser/app.js`:
  - Update `renderStockCard(stock)`:
    - Zone 1: Generate header with avatar, stock symbol, name, price, change chip, and star button.
    - Zone 2: Generate `.ai-hero-pill` (AI score out of 10, recommendation label, 4 pillar indicator dots with tooltips) with `data-action="open-xai"`. Generate canvas element `<canvas class="stock-sparkline-canvas" id="sparkline-${stock.symbol}"></canvas>`.
    - Zone 3: Generate `.card-zone-stats` with 4 formatted values (ارزش بازار, حجم, P/E, ورود/خروج پول).
    - Zone 4: Generate action buttons (`btn-live-avatar-trigger`, `btn-summary-trigger`, and `btn-more-actions` dropdown trigger).
    - Dropdown menu: append `.quick-actions-menu` containing TSETMC, Rahavard, Codal, GitHub links, and Reanalyze button.
  - In `setupCardActions()`:
    - Wire `.ai-hero-pill` click to `openExplainabilityModal(stock, "overview")`.
    - Wire `.btn-more-actions` to toggle `.quick-actions-menu.is-active`.
    - Add global document click listener to close open menus when clicking outside.
  - Implement `renderMiniSparkline(canvas, historyData, isPositive)`:
    - Creates lightweight Chart.js line chart with zero axes (`display: false` on x & y), zero gridlines, tension 0.4, clean gradient fill.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ui_app_rendering.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(ui): implement 4-zone minimal card rendering and sparklines in app.js"
```

---

### Task 3: Responsive Breakpoints & Mobile Polish

**Files:**
- Modify: `browser/styles.css`
- Modify: `browser/style.css`
- Modify: `browser/index.html` (header container layout)
- Test: `tests/test_ui_responsive_rules.py`

**Interfaces:**
- Produces: CSS media queries for `< 768px`, `768px - 1023px`, and `>= 1024px`.
- Enforces: Mobile card height < 200px, touch targets >= 44px, two-tier mobile header.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ui_responsive_rules.py`:
```python
# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
from pathlib import Path
import pytest

def test_responsive_media_queries_exist():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    assert "@media (max-width: 767px)" in css or "@media (max-width: 768px)" in css
    assert "min-height: 44px" in css or "height: 44px" in css or "touch-action" in css
    assert "overflow-x: hidden" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui_responsive_rules.py -v`  
Expected: FAIL (missing responsive rules)

- [ ] **Step 3: Implement responsive media queries**

- In `browser/styles.css` and `browser/style.css`:
  - Add `@media (max-width: 768px)`:
    - Set `.stocks-container` to `grid-template-columns: 1fr; gap: 0.875rem;`.
    - Set `.stock-card` max-height / compact padding (`0.75rem`), with font size adjustments.
    - Set `.app-header` to two-tier layout (row 1: title + badge; row 2: search + filters).
    - Ensure all buttons have touch targets >= 44px.
    - Set `body, .app-wrapper` to `overflow-x: hidden;`.
  - Add `@media (min-width: 769px) and (max-width: 1023px)`:
    - Set `.stocks-container` to `grid-template-columns: repeat(2, 1fr); gap: 1rem;`.
  - Add `@media (min-width: 1024px)`:
    - Set `.stocks-container` to `grid-template-columns: repeat(3, 1fr); gap: 1.25rem;`.
  - Keep `styles.css` and `style.css` 100% synchronized.
- In `browser/index.html`:
  - Ensure header container classes support the responsive flex wrap.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ui_responsive_rules.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(ui): implement responsive media queries and mobile touch optimization"
```

---

### Task 4: Automated Responsive & Functional End-to-End Verification

**Files:**
- Create: `tests/verify_minimal_ui_headless.py`
- Test: Run headless Chrome automated DOM and layout inspection

- [ ] **Step 1: Write verification script**

Create `tests/verify_minimal_ui_headless.py`:
- Spawns local HTTP server for `browser/` on port 8999.
- Launches headless Chrome (via Selenium or python webdriver / CDP).
- Tests 3 viewports:
  - Mobile (375x667): confirms `document.documentElement.scrollWidth <= 375` (no horizontal scroll), card height <= 200px.
  - Tablet (768x1024): confirms 2-column grid.
  - Desktop (1440x900): confirms 3-column grid.
- Simulates click on `.ai-hero-pill`: verifies `#explainabilityModal` gains active class.
- Simulates click on `.btn-more-actions`: verifies `.quick-actions-menu` opens with Codal and Rahavard links.
- Checks `browser.get_log("browser")` for 0 JavaScript errors.

- [ ] **Step 2: Run verification script**

Run: `python tests/verify_minimal_ui_headless.py`  
Expected: All viewport and interaction tests PASS with 0 console errors.

- [ ] **Step 3: Run existing unit & regression tests**

Run: `python -m pytest tests/ -k "test_ui" -v`  
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git commit -am "test(ui): complete automated headless verification of minimal responsive stock listing"
```
