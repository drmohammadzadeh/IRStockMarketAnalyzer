# -*- coding: utf-8 -*-
"""
End-to-End Headless Verification Test for Multi-Criteria Filtering System
"""
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def run_headless_tests():
    print("=" * 60, flush=True)
    print("Starting Headless Selenium UI & Filter Verification...", flush=True)
    print("=" * 60, flush=True)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-proxy-server")
    options.add_argument("--window-size=1400,900")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    print("Initializing Chrome webdriver...", flush=True)
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. Load Page
        print("Navigating to http://127.0.0.1:8080/ ...", flush=True)
        driver.get("http://127.0.0.1:8080/")
        wait.until(EC.presence_of_element_located((By.ID, "stocksContainer")))
        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        total_badge = driver.find_element(By.ID, "totalStocksBadge").text
        print(f"[OK] Page loaded. Total Stocks Badge: {total_badge}, Rendered Cards: {len(cards)}", flush=True)
        assert len(cards) > 0, "No stock cards rendered!"

        # Check Quick Filter Chips toolbar
        quick_chips = driver.find_elements(By.CSS_SELECTOR, "#quickFilterChips .filter-chip")
        print(f"[OK] Found {len(quick_chips)} Quick Filter Chips.", flush=True)
        assert len(quick_chips) >= 10, f"Expected at least 10 quick filter chips, found {len(quick_chips)}"

        # 2. Test Quick Filter: Golden Opportunity (خرید قوی)
        chip_golden = driver.find_element(By.CSS_SELECTOR, ".filter-chip[data-quick-filter='golden']")
        chip_golden.click()
        time.sleep(0.5)
        cards_golden = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] Golden Opportunity Filter applied. Matching Cards: {len(cards_golden)}", flush=True)
        assert len(cards_golden) > 0, "Golden filter returned 0 cards!"

        # Check Active Tag Bar
        tags_bar = driver.find_element(By.ID, "activeFilterTagsBar")
        assert tags_bar.is_displayed(), "Active filter tags bar should be visible!"
        tag_chips = driver.find_elements(By.CSS_SELECTOR, ".filter-tag-chip")
        print(f"[OK] Active tags rendered: {len(tag_chips)} tag chip(s).", flush=True)
        assert len(tag_chips) >= 1, "Expected active tag chip for quick filter!"

        # Test Dismissing Quick Filter Tag via 'x'
        tag_remove_btn = driver.find_element(By.CSS_SELECTOR, ".tag-remove-btn")
        tag_remove_btn.click()
        time.sleep(0.5)
        cards_after_remove = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] Tag dismissed via 'x'. Cards count restored: {len(cards_after_remove)}", flush=True)
        assert len(cards_after_remove) == len(cards), "Card count not restored after tag dismissal!"

        # 3. Test Quick Filter: Smart Money (ورود پول هوشمند)
        chip_smart = driver.find_element(By.CSS_SELECTOR, ".filter-chip[data-quick-filter='smart_money']")
        chip_smart.click()
        time.sleep(0.5)
        cards_smart = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] Smart Money Filter applied. Matching Cards: {len(cards_smart)}", flush=True)
        assert len(cards_smart) > 0, "Smart money filter returned 0 cards!"

        # 4. Test Quick Filter: In Entry Zone (در محدوده خرید)
        chip_ez = driver.find_element(By.CSS_SELECTOR, ".filter-chip[data-quick-filter='entry_zone']")
        chip_ez.click()
        time.sleep(0.5)
        cards_ez = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] In Entry Zone Filter applied. Matching Cards: {len(cards_ez)}", flush=True)
        assert len(cards_ez) > 0, "Entry zone filter returned 0 cards!"

        # 5. Test Quick Filter: High R/R (R/R >= 2.0)
        chip_rr = driver.find_element(By.CSS_SELECTOR, ".filter-chip[data-quick-filter='rr_high']")
        chip_rr.click()
        time.sleep(0.5)
        cards_rr = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] High R/R Filter applied. Matching Cards: {len(cards_rr)}", flush=True)
        assert len(cards_rr) > 0, "High R/R filter returned 0 cards!"

        # 6. Reset with 'All' chip
        chip_all = driver.find_element(By.CSS_SELECTOR, ".filter-chip[data-quick-filter='all']")
        chip_all.click()
        time.sleep(0.5)
        cards_all = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] Reset to 'All'. Cards count: {len(cards_all)}", flush=True)
        assert len(cards_all) == len(cards), "Card count mismatch after reset to All!"

        # 7. Test Advanced Filter Drawer
        open_btn = driver.find_element(By.ID, "openFilterDrawerBtn")
        drawer_panel = driver.find_element(By.ID, "filterDrawerPanel")
        backdrop = driver.find_element(By.ID, "filterDrawerBackdrop")

        open_btn.click()
        time.sleep(0.5)
        assert "show" in drawer_panel.get_attribute("class"), "Drawer panel does not have 'show' class!"
        assert "show" in backdrop.get_attribute("class"), "Drawer backdrop does not have 'show' class!"
        print("[OK] Advanced Filter Drawer opened successfully.", flush=True)

        # Test AI Score Slider in Drawer
        ai_slider = driver.find_element(By.ID, "filterAiScoreSlider")
        driver.execute_script("arguments[0].value = 8.5; arguments[0].dispatchEvent(new Event('input'));", ai_slider)
        time.sleep(0.5)
        matching_count_el = driver.find_element(By.ID, "drawerMatchingCount")
        print(f"[OK] AI Score Slider set to 8.5. Live Matching Count Pill: {matching_count_el.text}", flush=True)

        # Check Active Filter Badge in Header
        badge = driver.find_element(By.ID, "activeFiltersBadge")
        assert badge.is_displayed(), "Active filters badge in header should be displayed!"
        print(f"[OK] Header Active Filters Badge: {badge.text}", flush=True)

        # Test Apply Button in Drawer
        apply_btn = driver.find_element(By.ID, "drawerApplyBtn")
        apply_btn.click()
        time.sleep(0.5)
        assert "show" not in drawer_panel.get_attribute("class"), "Drawer panel still has 'show' class after Apply!"
        print("[OK] Apply button clicked; drawer closed and filtered results shown.", flush=True)

        cards_filtered = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] Filtered Cards Count on Main View: {len(cards_filtered)}", flush=True)
        assert len(cards_filtered) <= len(cards), "Filtered card count invalid!"

        # Test Clear All Filters Button
        clear_all_btn = driver.find_element(By.ID, "clearAllFiltersBtn")
        clear_all_btn.click()
        time.sleep(0.5)
        cards_after_clear = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        print(f"[OK] 'Clear All Filters' executed. Cards count restored: {len(cards_after_clear)}", flush=True)
        assert len(cards_after_clear) == len(cards), "Card count not restored after clear all!"

        # 8. Check Browser Console Logs for JavaScript Errors
        logs = driver.get_log("browser")
        # Ignore 404 for missing favicon.ico
        severe_errors = [l for l in logs if l["level"] == "SEVERE" and "favicon.ico" not in l.get("message", "")]
        print(f"[OK] Browser Console Logs: {len(logs)} messages, {len(severe_errors)} SEVERE script errors.", flush=True)
        for err in severe_errors:
            print("  SEVERE:", err["message"], flush=True)
        assert len(severe_errors) == 0, f"Found {len(severe_errors)} SEVERE JavaScript console errors!"

        print("=" * 60, flush=True)
        print("ALL HEADLESS E2E TESTS PASSED WITH 100% SUCCESS!", flush=True)
        print("=" * 60, flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    run_headless_tests()
