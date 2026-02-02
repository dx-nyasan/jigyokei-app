---
name: deploy-commander
description: テスト全通過を条件としたデプロイフローの自律制御を行うスキル
---

# deploy-commander Skill

ローカルおよびクラウド環境へのデプロイを安全に実行します。デプロイ前後の健全性チェックをオートメーション化します。

## 構成
- 入力: デプロイ対象のブランチ/コミット、環境（staging/prod）
- 出力: デプロイ実行、ステータス報告

## 手順
1. **プロトコル遵守の確認**: まず `core-protocol` Skill を参照し、テストがTDD原則に従って全件通過しているかを確認する。## 🚢 デプロイ手順と環境構成

### 1. 手順 (Step-by-Step)
- **GitHub同期**: `git push origin main` でソースを最新化。
- **Streamlit Cloud設定**: 
  - Main file path: `src/frontend/app_hybrid.py`
  - Python version: 3.11以上を推奨。

### 2. シークレット管理 (Advanced Settings > Secrets)
以下の項目を必ず `secrets.toml` 形式で定義してください。
```toml
# Google Gemini API Key
GOOGLE_API_KEY = "取得したAPIキー"

# アプリケーション認証パスワード
APP_PASSWORD = "30bousai" (デフォルト)
```

### 3. 運用・保守
- **一時ファイルシステムの制約**: サーバー上のファイル保存は再起動で消失するため、ユーザーデータの保存（JSONダウンロード）を適切に案内する。
- **ヘルスチェック**: デプロイ直後に「経営者インタビュー」画面が正常にロードされるかを確認する。

## 判断基準
- テスト未実施でのデプロイは原則禁止する。（`pytest` 全件パスが必須条件）
- `APP_PASSWORD` が変更された場合は、`user_manual.md` に即時反映する。

## 実行例
「準備ができたらデプロイして」
→ `deploy-commander` が起動
→ `git push` 後、Streamlit Secrets の設定状況とテスト結果を報告
