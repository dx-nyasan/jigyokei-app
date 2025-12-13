import pytest
from playwright.sync_api import sync_playwright, expect
import time
import os

# Use existing app URL or launch new
APP_URL = "http://localhost:8501"

def test_mobile_menu_button_logic():
    """
    Simulates a mobile device and verifies that the 'Menu' button 
    (customized stSidebarCollapsedControl) is visible and styled correctly.
    """
    with sync_playwright() as p:
        # iPhone 12 Emulation
        iphone_12 = p.devices['iPhone 12']
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone_12)
        page = context.new_page()
        
        try:
            print(f"Navigating to {APP_URL}...")
            page.goto(APP_URL, timeout=30000)
            
            # Wait for Streamlit to finish "Running" state
            print("Waiting for app to load...")
            page.wait_for_selector('[data-testid="stStatusWidgetRunningIcon"]', state='detached', timeout=30000)
            
            page.wait_for_load_state("networkidle")
            
            # Allow CSS to inject
            time.sleep(3)
            
            # Select the button
            # Note: On mobile, Streamlit might render it in header
            # Strategy: Look for the collapsed control button
            
            # 1. Check if ANY collapsed control is present
            btn = page.locator('[data-testid="stSidebarCollapsedControl"]').first
            if not btn.is_visible():
                # Maybe it's buried in header?
                btn = page.locator('button[data-testid="stSidebarCollapsedControl"]').first
            
            assert btn.is_visible(), "Menu button should be visible on mobile"
            
            # 2. Verify pseudo-element content using JS evaluation
            # Streamlit CSS injection converts ::after content to visible text visually,
            # but programmatically we check if the CSS rule is applied.
            
            # Check dimensions (Should be > 44px wide if 'Menu' text is there)
            box = btn.bounding_box()
            print(f"Button Box: {box}")
            
            # Custom CSS forces min-height 44px and width auto
            # If text "メニュー" is present via CSS content, width should be reasonable (>50px usually)
            # Standard icon is ~44px. Custom one with text is wider.
            
            # Capture Screenshot
            screenshot_path = os.path.abspath("mobile_menu_verification.png")
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
            
            # Verify CSS property on Mobile
            # check if background is #ffeaea (pinkish)
            bg_color = btn.evaluate("el => window.getComputedStyle(el).backgroundColor")
            print(f"Background Color: {bg_color}")
            
            assert "rgb(255, 234, 234)" in bg_color or "#ffeaea" in bg_color, \
                f"Expected pink background #ffeaea, got {bg_color}"
            
        except Exception as e:
            # Take error screenshot
            page.screenshot(path="mobile_test_error.png")
            
            # Dump DOM to find the button
            debug_dom = page.content()
            with open("debug_dom.html", "w", encoding="utf-8") as f:
                f.write(debug_dom)
            print("Dumped DOM to debug_dom.html")
            
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    test_mobile_menu_button_logic()
