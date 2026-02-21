import asyncio
import os
import json
from playwright.async_api import async_playwright

# Directories
STRICT_DIR = r"C:\Users\kitahara\.gemini\antigravity\brain\b932dbb7-0ad2-4b11-b5b9-740aecb2a7ae\strict_evidence"
os.makedirs(STRICT_DIR, exist_ok=True)

ASSET_PATH = r"c:\Users\kitahara\Desktop\script\jigyokei-app\tests\assets\sato_info.txt"

async def ux_strict_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1400, 'height': 1200})
        page = await context.new_page()

        async def capture(name):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            await page.screenshot(path=os.path.join(STRICT_DIR, f"{name}.png"), full_page=False)

        print("--- Scene 0: Authentication ---")
        await page.goto("http://localhost:8501")
        await asyncio.sleep(12)
        try:
            pwds = await page.locator("input[type='password']").all()
            if pwds:
                await pwds[0].fill("30bousai")
                await pwds[0].press("Enter")
                await asyncio.sleep(12)
        except: pass
        await capture("scene0_auth")

        print("--- Scene 1: Onboarding ---")
        try:
            if await page.get_by_text("事業継続力強化計画 策定支援システムへようこそ").is_visible():
                await page.get_by_text("経営者（事業主）").first.click()
                await asyncio.sleep(2)
                await page.get_by_role("button", name="🚀 はじめる").click()
                await asyncio.sleep(12)
        except: pass
        await capture("scene1_onboarding")

        print("--- Scene 2: Document Upload (Direct Context Injection) ---")
        try:
            # Open upload expander
            await page.get_by_text("資料の追加アップロード").first.click()
            await asyncio.sleep(2)
            
            # Use set_input_files on the hidden input
            async with page.expect_file_chooser() as fc_info:
                await page.get_by_text("Browse files").first.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(ASSET_PATH)
            await asyncio.sleep(5)
            
            # Click Process Files
            await page.get_by_role("button", name="🚀 資料を読み込む (Process Files)").click()
            print("  Processing file (100s for AI reasoning)...")
            await asyncio.sleep(100) # Wait for AI Agent Working status
        except Exception as e:
            print(f"Upload failed: {e}")
        await capture("scene2_upload")

        print("--- Scene 3: Dashboard Verification ---")
        try:
            await page.get_by_role("button", name="📊 進捗詳細を確認 (Dashboard)").click()
            await asyncio.sleep(60)
            try:
                prog = await page.locator("div[data-testid='stMetricValue']").first.inner_text()
                print(f"  Dashboard Progress: {prog}")
            except: pass
        except: pass
        await capture("scene3_dashboard")

        print("--- Scene 4: Excel Export ---")
        try:
            await page.get_by_role("button", name="📋 電子申請入力用 (Excel)").click()
            await asyncio.sleep(5)
            async with page.expect_download(timeout=90000) as download_info:
                await page.get_by_text("⬇️ ダウンロード (入力用)").click()
            download = await download_info.value
            excel_path = os.path.join(STRICT_DIR, "sato_strict_draft.xlsx")
            await download.save_as(excel_path)
            print(f"Excel Export SUCCESS: {excel_path}")
        except Exception as e:
            print(f"Excel Export FAILED: {e}")
            await capture("error_excel_export")

        await browser.close()
        print("Final Strict E2E Test Completed.")

if __name__ == "__main__":
    asyncio.run(ux_strict_test())
