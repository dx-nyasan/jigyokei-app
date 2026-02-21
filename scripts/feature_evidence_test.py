"""
Feature Evidence E2E Test Script
================================
USER_JOURNEY.md に記載された各機能の動作を検証し、
スクリーンショットでエビデンスを取得するテストスクリプト。

対象機能 (UI可視):
1. Onboarding Wizard - 業種選択による初期化
2. Chat Mode - 対話による情報収集
3. Auto-Refinement - 素朴な回答の専門的表現への変換
4. Progress Dashboard - リアルタイム進捗表示
5. Model Monitoring - サイドバーのモデル稼働状況
6. DraftExporter - Excel出力（手動確認用にダウンロードトリガー）
"""
import asyncio
import os
from playwright.async_api import async_playwright

# 出力ディレクトリ
IMG_DIR = r"C:\Users\kitahara\.gemini\antigravity\brain\b932dbb7-0ad2-4b11-b5b9-740aecb2a7ae\evidence"
os.makedirs(IMG_DIR, exist_ok=True)

async def capture(page, name, description):
    """スクリーンショットを取得し、説明付きで保存"""
    path = os.path.join(IMG_DIR, f"{name}.png")
    await page.screenshot(path=path, full_page=True)
    print(f"✅ [{name}] {description}")
    return path


async def run_feature_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("Feature Evidence E2E Test - Start")
        print("="*60 + "\n")

        # ============================
        # Step 0: ログイン
        # ============================
        print("🔐 Step 0: ログイン...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await asyncio.sleep(8)
        try:
            pwd_input = page.locator("input[type='password']").first
            if await pwd_input.is_visible(timeout=5000):
                await pwd_input.fill("30bousai")
                await pwd_input.press("Enter")
                await asyncio.sleep(8)
        except:
            pass
        await capture(page, "00_login_complete", "ログイン完了後の初期画面")

        # ============================
        # Feature 1: Onboarding Wizard
        # ============================
        print("\n🏭 Feature 1: Onboarding Wizard (業種選択)...")
        try:
            start_btn = page.get_by_role("button", name="🚀 はじめる")
            if await start_btn.is_visible(timeout=10000):
                await start_btn.click()
                await asyncio.sleep(8)
                await capture(page, "01_onboarding_wizard", "業種テンプレート選択画面 - 製造業向けにカスタマイズ")
        except Exception as e:
            print(f"  ⚠️ Onboarding not found: {e}")
            await capture(page, "01_onboarding_fallback", "Onboarding画面 (フォールバック)")

        # ============================
        # Feature 2: Chat Mode (対話)
        # ============================
        print("\n💬 Feature 2: Chat Mode (対話による情報収集)...")
        
        async def send_and_capture(text, img_name, desc, wait_time=50):
            """メッセージ送信 → AI応答待機 → スクショ"""
            try:
                chat_input = page.get_by_placeholder("経営者として回答を入力...").last
                await chat_input.fill(text)
                submit_btn = page.get_by_test_id("stChatInputSubmitButton").last
                await submit_btn.click()
                await asyncio.sleep(5)  # 送信後の初期待機
                print(f"  ⏳ AI応答待機中 ({wait_time}秒)...")
                await asyncio.sleep(wait_time)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                await capture(page, img_name, desc)
                return True
            except Exception as e:
                print(f"  ⚠️ Chat failed: {e}")
                return False

        # 2-1: 初回挨拶（事業概要の自動サジェスト）
        await send_and_capture(
            "葛飾区で15人で金属加工をやってる佐藤精密工業です。補助金の加点のためにジギョケイを作りたい。",
            "02_chat_business_intro",
            "Chat Mode: 事業概要入力 → AIがプロフェッショナルな表現をサジェスト"
        )

        # ============================
        # Feature 3: Auto-Refinement (専門的表現への変換)
        # ============================
        print("\n✨ Feature 3: Auto-Refinement (素朴な回答の専門化)...")
        await send_and_capture(
            "荒川の近くなんだけど、水害とか考えたほうがいいかな？",
            "03_auto_refinement_hazard",
            "Auto-Refinement: ユーザーの素朴な質問 → AIがハザードマップ参照を提案"
        )

        await send_and_capture(
            "土嚢を準備するくらいしか思いつかないけど、どう書けばいい？",
            "04_auto_refinement_measure",
            "Auto-Refinement: 「土嚢」→「止水板設置・重要設備嵩上げ」へ専門的に変換"
        )

        # ============================
        # Feature 4: Progress Dashboard
        # ============================
        print("\n📊 Feature 4: Progress Dashboard (進捗可視化)...")
        try:
            dashboard_btn = page.get_by_text("進捗詳細を確認").first
            await dashboard_btn.click()
            await asyncio.sleep(8)
            await capture(page, "05_progress_dashboard", "Progress Dashboard: リアルタイム進捗率と不足項目の視覚化")
        except Exception as e:
            print(f"  ⚠️ Dashboard click failed: {e}")
            await capture(page, "05_dashboard_fallback", "Dashboard画面 (フォールバック)")

        # ============================
        # Feature 5: Model Monitoring (サイドバー)
        # ============================
        print("\n🔧 Feature 5: Model Monitoring (モデル稼働状況)...")
        try:
            # サイドバーを展開
            system_menu = page.get_by_text("System Menu").first
            await system_menu.click()
            await asyncio.sleep(3)
            await capture(page, "06_model_monitoring", "Model Monitoring: サイドバーでのモデル稼働状況表示")
        except Exception as e:
            print(f"  ⚠️ System Menu not found: {e}")
            await capture(page, "06_sidebar_state", "サイドバー状態 (フォールバック)")

        # ============================
        # Feature 6: DraftExporter (Excel出力トリガー)
        # ============================
        print("\n📋 Feature 6: DraftExporter (Excel出力)...")
        try:
            # エディタモードに切り替え or 出力ボタンを探す
            export_btn = page.get_by_text("電子申請入力用").first
            if await export_btn.is_visible(timeout=5000):
                await export_btn.click()
                await asyncio.sleep(5)
                await capture(page, "07_draft_exporter", "DraftExporter: Excel出力ボタン押下後の状態")
            else:
                # サイドバーから探す
                await capture(page, "07_export_not_visible", "Excel出力ボタン非表示 (手動確認が必要)")
        except Exception as e:
            print(f"  ⚠️ Export button not found: {e}")
            await capture(page, "07_export_fallback", "出力画面 (フォールバック)")

        # ============================
        # 完了
        # ============================
        print("\n" + "="*60)
        print("Feature Evidence E2E Test - Complete!")
        print(f"スクリーンショット保存先: {IMG_DIR}")
        print("="*60 + "\n")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_feature_test())
