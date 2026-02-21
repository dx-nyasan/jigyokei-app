import asyncio
from playwright.async_api import async_playwright
import os

async def run_scenario():
    async with async_playwright() as p:
        # Create artifacts dir if not exists
        img_dir = r"C:\Users\kitahara\.gemini\antigravity\brain\b932dbb7-0ad2-4b11-b5b9-740aecb2a7ae\images"
        os.makedirs(img_dir, exist_ok=True)
        
        browser = await p.chromium.launch(headless=True)
        # Explicitly set viewport
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print("Opening app...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await asyncio.sleep(10)
        
        # Step 0: Login
        print("Performing login...")
        try:
            password_input = page.locator("input[type='password']").first
            if await password_input.is_visible(timeout=5000):
                await password_input.fill("30bousai")
                await password_input.press("Enter")
                print("Password entered.")
                await asyncio.sleep(10)
        except:
            pass

        # Step 0.1: Onboarding Wizard
        print("Navigating onboarding...")
        try:
            start_button = page.get_by_role("button", name="🚀 はじめる")
            if await start_button.is_visible(timeout=10000):
                await start_button.click()
                print("Start button clicked.")
                await asyncio.sleep(10)
        except:
            pass

        # Helper to send message and wait for response
        async def send_chat(text, img_name):
            print(f"Sending: {text[:20]}...")
            try:
                # Find input by placeholder/aria-label
                chat_input = page.get_by_placeholder("経営者として回答を入力...").last
                await chat_input.fill(text)
                
                # Click the verified submit button
                submit_btn = page.get_by_test_id("stChatInputSubmitButton").last
                await submit_btn.click()
                
                # Wait for the "spinner" or response to start
                await asyncio.sleep(5)
                # Wait for response to finish
                print("Waiting for response...")
                await asyncio.sleep(45) # Long wait for LLM response + suggestions
                
                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                await page.screenshot(path=os.path.join(img_dir, img_name), full_page=True)
                return True
            except Exception as e:
                print(f"Chat failed: {e}")
                return False

        # Step 1: Initial Greeting
        await send_chat("葛飾区で15人で金属加工をやってる佐藤精密工業です。補助金の加点のためにジギョケイを作りたい。", "01_business_suggestion.png")
        
        # Step 2: Flood Risk
        await send_chat("荒川の近くなんだけど、水害とか考えたほうがいいかな？", "02_hazard_suggestion.png")
        
        # Step 3: Countermeasures
        await send_chat("土嚢を準備するくらいしか思いつかないけど、どう書けばいい？", "03_measure_suggestion.png")
        
        # Step 4: Dashboard
        print("Viewing Dashboard...")
        try:
            # Click dashboard from sidebar or main UI
            await page.get_by_text("進捗詳細を確認").first.click()
            await asyncio.sleep(10)
            await page.screenshot(path=os.path.join(img_dir, "04_dashboard_view.png"), full_page=True)
        except:
            await page.screenshot(path=os.path.join(img_dir, "04_dashboard_fallback.png"), full_page=True)
        
        await browser.close()
        print("Test complete.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
