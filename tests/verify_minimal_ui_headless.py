#!/usr/bin/env python3
# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
"""
Automated Responsive & Functional End-to-End Verification (Task 4)
Uses headless Google Chrome via Selenium to perform DOM and layout inspection:
1. Mobile (375x667): confirms zero horizontal overflow (scrollWidth <= 375) and card height <= 200px.
2. Tablet (768x1024): confirms 2-column grid.
3. Desktop (1440x900): confirms 3-column grid.
4. AI Hero Pill click: confirms #explainabilityModal gains active class and opens.
5. Quick Actions click: confirms .quick-actions-menu opens with Codal and Rahavard links.
6. Verifies 0 JavaScript console errors.
"""

import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
BROWSER_DIR = ROOT_DIR / "browser"
DATA_FILE = BROWSER_DIR / "data" / "stocks.json"

class BrowserHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving browser/ with mocking for API endpoints."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BROWSER_DIR), **kwargs)

    def log_message(self, format, *args):
        # Suppress standard HTTP access log chatter
        pass

    def do_GET(self):
        # Handle php fallback mock
        if self.path.startswith("/api/stocks.php"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            if DATA_FILE.exists():
                with open(DATA_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"[]")
            return

        # Handle favicon request gracefully
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        return super().do_GET()


class HTTPServerManager:
    """Threaded local HTTP server lifecycle manager."""
    def __init__(self, port=8999):
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        # Bind to requested port or fallback to available port
        for attempt_port in [self.port, 8998, 9000, 0]:
            try:
                self.server = socketserver.TCPServer(("127.0.0.1", attempt_port), BrowserHTTPHandler)
                self.port = self.server.server_address[1]
                break
            except OSError:
                continue

        if not self.server:
            raise RuntimeError(f"Could not bind HTTP server to port {self.port} or fallback ports")

        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


def create_headless_chrome_driver():
    """Initializes and configures headless Chrome WebDriver."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    # Bypass Windows proxy artifacts to prevent ERR_NO_SUPPORTED_PROXIES
    opts.add_argument("--no-proxy-server")
    opts.add_argument("--proxy-server=direct://")
    opts.add_argument("--proxy-bypass-list=*")

    driver = webdriver.Chrome(options=opts)
    return driver


def set_viewport(driver, width: int, height: int, mobile: bool = False):
    """Sets exact viewport metrics using Chrome DevTools Protocol."""
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 1,
        "mobile": mobile
    })


def wait_for_stocks_rendered(driver, timeout: float = 6.0):
    """Waits until .stock-card elements are rendered in the DOM."""
    start = time.time()
    while time.time() - start < timeout:
        cards = driver.find_elements("css selector", ".stock-card")
        if len(cards) > 0:
            return cards
        time.sleep(0.2)
    raise TimeoutError("Stock cards were not rendered within timeout")


def run_all_headless_verifications():
    """Executes all headless responsive and functional end-to-end tests."""
    from selenium.webdriver.common.by import By

    print("=" * 70)
    print("STARTING HEADLESS RESPONSIVE & FUNCTIONAL VERIFICATION (Task 4)")
    print("=" * 70)

    server_mgr = HTTPServerManager(port=8999)
    base_url = server_mgr.start()
    app_url = f"{base_url}/index.html"
    print(f"[*] Local HTTP server listening at: {app_url}")

    driver = None
    passed_tests = 0
    total_tests = 6

    try:
        driver = create_headless_chrome_driver()
        print("[*] Chrome Headless WebDriver initialized successfully\n")

        # -------------------------------------------------------------
        # TEST 1: Mobile Viewport (375x667)
        # -------------------------------------------------------------
        print("--- [TEST 1] Mobile Viewport (375x667) ---")
        set_viewport(driver, 375, 667, mobile=True)
        driver.get(app_url)
        cards = wait_for_stocks_rendered(driver)

        metrics = driver.execute_script("""
            const card = document.querySelector('.stock-card');
            const container = document.querySelector('.stocks-container');
            const style = container ? window.getComputedStyle(container) : null;
            return {
                innerWidth: window.innerWidth,
                scrollWidth: document.documentElement.scrollWidth,
                cardHeight: card ? card.getBoundingClientRect().height : 0,
                colCount: style && style.gridTemplateColumns ? style.gridTemplateColumns.trim().split(/\\s+/).length : 0,
                gridCols: style ? style.gridTemplateColumns : null
            };
        """)

        print(f"  -> innerWidth: {metrics['innerWidth']}px")
        print(f"  -> document.scrollWidth: {metrics['scrollWidth']}px (limit <= 375)")
        print(f"  -> stock-card height: {metrics['cardHeight']:.1f}px (limit <= 200)")
        print(f"  -> grid columns: {metrics['colCount']} ({metrics['gridCols']})")

        assert metrics["scrollWidth"] <= 375, (
            f"FAILED: Mobile horizontal overflow detected! scrollWidth={metrics['scrollWidth']} > 375"
        )
        assert metrics["cardHeight"] <= 200, (
            f"FAILED: Mobile card height exceeds limit! height={metrics['cardHeight']} > 200"
        )
        assert metrics["colCount"] == 1, (
            f"FAILED: Mobile grid expected 1 column, got {metrics['colCount']}"
        )
        print("  [PASS] Mobile Viewport (375x667): 0 overflow, card height <= 200px, 1 column.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # TEST 2: Tablet Viewport (768x1024)
        # -------------------------------------------------------------
        print("--- [TEST 2] Tablet Viewport (768x1024) ---")
        set_viewport(driver, 768, 1024, mobile=False)
        time.sleep(0.4)

        tablet_metrics = driver.execute_script("""
            const container = document.querySelector('.stocks-container');
            const style = container ? window.getComputedStyle(container) : null;
            return {
                innerWidth: window.innerWidth,
                colCount: style && style.gridTemplateColumns ? style.gridTemplateColumns.trim().split(/\\s+/).length : 0,
                gridCols: style ? style.gridTemplateColumns : null
            };
        """)

        print(f"  -> innerWidth: {tablet_metrics['innerWidth']}px")
        print(f"  -> grid columns: {tablet_metrics['colCount']} ({tablet_metrics['gridCols']})")

        assert tablet_metrics["colCount"] == 2, (
            f"FAILED: Tablet expected 2 columns, got {tablet_metrics['colCount']} ({tablet_metrics['gridCols']})"
        )
        print("  [PASS] Tablet Viewport (768x1024): 2-column grid confirmed.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # TEST 3: Desktop Viewport (1440x900)
        # -------------------------------------------------------------
        print("--- [TEST 3] Desktop Viewport (1440x900) ---")
        set_viewport(driver, 1440, 900, mobile=False)
        time.sleep(0.4)

        desktop_metrics = driver.execute_script("""
            const container = document.querySelector('.stocks-container');
            const style = container ? window.getComputedStyle(container) : null;
            return {
                innerWidth: window.innerWidth,
                colCount: style && style.gridTemplateColumns ? style.gridTemplateColumns.trim().split(/\\s+/).length : 0,
                gridCols: style ? style.gridTemplateColumns : null
            };
        """)

        print(f"  -> innerWidth: {desktop_metrics['innerWidth']}px")
        print(f"  -> grid columns: {desktop_metrics['colCount']} ({desktop_metrics['gridCols']})")

        assert desktop_metrics["colCount"] == 3, (
            f"FAILED: Desktop expected 3 columns, got {desktop_metrics['colCount']} ({desktop_metrics['gridCols']})"
        )
        print("  [PASS] Desktop Viewport (1440x900): 3-column grid confirmed.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # TEST 4: Explainability Modal Click (.ai-hero-pill)
        # -------------------------------------------------------------
        print("--- [TEST 4] Interaction: Click .ai-hero-pill opens #explainabilityModal ---")
        ai_hero_pill = driver.find_element(By.CSS_SELECTOR, ".ai-hero-pill")
        ai_hero_pill.click()
        time.sleep(0.4)

        modal = driver.find_element(By.ID, "explainabilityModal")
        modal_classes = modal.get_attribute("class") or ""
        modal_display = modal.value_of_css_property("display")

        print(f"  -> modal class list: '{modal_classes}'")
        print(f"  -> modal display style: '{modal_display}'")

        assert "active" in modal_classes, (
            f"FAILED: #explainabilityModal missing 'active' class after .ai-hero-pill click. Classes: {modal_classes}"
        )
        assert modal_display == "flex", (
            f"FAILED: #explainabilityModal expected display: flex, got '{modal_display}'"
        )

        # Close modal to restore clean UI state
        close_btn = driver.find_element(By.ID, "closeXaiModalBtn")
        close_btn.click()
        time.sleep(0.3)
        assert modal.value_of_css_property("display") == "none", (
            "FAILED: #explainabilityModal failed to close properly"
        )
        print("  [PASS] .ai-hero-pill click opens #explainabilityModal with active class & closes properly.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # TEST 5: Quick Actions Dropdown Click (.btn-more-actions)
        # -------------------------------------------------------------
        print("--- [TEST 5] Interaction: Click .btn-more-actions opens .quick-actions-menu ---")
        btn_quick_actions = driver.find_element(By.CSS_SELECTOR, ".btn-quick-actions, .btn-more-actions")
        btn_quick_actions.click()
        time.sleep(0.3)

        menu = driver.find_element(By.CSS_SELECTOR, ".quick-actions-menu")
        menu_classes = menu.get_attribute("class") or ""
        menu_html = menu.get_attribute("innerHTML") or ""

        print(f"  -> quick-actions-menu classes: '{menu_classes}'")
        has_codal = "کدال" in menu_html or "codal" in menu_html.lower()
        has_rahavard = "رهاورد" in menu_html or "rahavard" in menu_html.lower()
        print(f"  -> Codal link present: {has_codal}")
        print(f"  -> Rahavard link present: {has_rahavard}")

        assert "is-active" in menu_classes, (
            f"FAILED: .quick-actions-menu missing 'is-active' class! Classes: {menu_classes}"
        )
        assert has_codal, "FAILED: .quick-actions-menu does not contain Codal link!"
        assert has_rahavard, "FAILED: .quick-actions-menu does not contain Rahavard link!"
        print("  [PASS] .btn-more-actions click opens .quick-actions-menu with Codal & Rahavard.\n")
        passed_tests += 1

        # -------------------------------------------------------------
        # TEST 6: JavaScript Console Errors Verification
        # -------------------------------------------------------------
        print("--- [TEST 6] Zero JavaScript Console Errors ---")
        browser_logs = driver.get_log("browser")
        # Filter genuine severe JavaScript execution errors
        js_errors = [
            l for l in browser_logs
            if l.get("level") == "SEVERE" and "favicon.ico" not in l.get("message", "")
        ]

        if js_errors:
            print("  [!] Detected Console Errors:")
            for err in js_errors:
                print(f"      - {err.get('message')}")
        else:
            print("  -> 0 SEVERE JavaScript errors logged in browser console.")

        assert len(js_errors) == 0, (
            f"FAILED: Found {len(js_errors)} JavaScript error(s) in browser console: {js_errors}"
        )
        print("  [PASS] Clean execution with 0 JavaScript console errors.\n")
        passed_tests += 1

        print("=" * 70)
        print(f"RESULT: ALL {passed_tests}/{total_tests} HEADLESS E2E TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
        return True

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        server_mgr.stop()


# Pytest test function bindings
def test_headless_responsive_and_interactions():
    """Pytest test case executing the complete headless responsive & functional suite."""
    success = run_all_headless_verifications()
    assert success is True


if __name__ == "__main__":
    try:
        run_all_headless_verifications()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[TEST FAILED] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(2)
