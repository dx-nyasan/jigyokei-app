import asyncio
from playwright.async_api import async_playwright

async def debug_dom():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8501")
        await asyncio.sleep(10)
        
        # Login
        await page.locator("input[type='password']").fill("30bousai")
        await page.keyboard.press("Enter")
        await asyncio.sleep(10)
        
        # Start
        await page.get_by_role("button", name="🚀 はじめる").click()
        await asyncio.sleep(10)
        
        # Print all buttons and textareas
        print("--- Textareas ---")
        textareas = await page.locator("textarea").all()
        for i, ta in enumerate(textareas):
            print(f"{i}: {await ta.get_attribute('aria-label')} | {await ta.get_attribute('placeholder')}")
            
        print("--- Buttons ---")
        buttons = await page.locator("button").all()
        for i, btn in enumerate(buttons):
            print(f"{i}: {await btn.inner_text()} | {await btn.get_attribute('data-testid')}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dom())
