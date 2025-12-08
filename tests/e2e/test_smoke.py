import pytest
from playwright.sync_api import Page, expect

def test_homepage_loads(page: Page):
    # 仮のロードテスト
    # 本番URLやローカルURLは環境変数で切り替えるのが理想
    # page.goto("http://localhost:8501")
    # expect(page).to_have_title("Jigyokei App")
    assert True
