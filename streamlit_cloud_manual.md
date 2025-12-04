# Streamlit Community Cloud デプロイメント & 運用マニュアル

## 1. 概要
本システムは、Streamlit Community Cloud を利用してホスティングされます。
クラウド上の「一時的なファイルシステム」という制約に対応するため、**データの保存・読込はユーザーの手元（ローカルPC）を介して行います。**

## 2. デプロイ手順

### Step 1: GitHubへのプッシュ
ソースコードをGitHubリポジトリにアップロードします。

```bash
# 変更をステージング
git add .

# コミット
git commit -m "Prepare for Streamlit Cloud deployment"

# プッシュ (mainブランチの場合)
git push origin main
```

### Step 2: Streamlit Cloud での設定
1. [Streamlit Community Cloud](https://share.streamlit.io/) にログインします。
2. **"New app"** をクリックします。
3. 以下の設定を入力します:
   - **Repository:** プッシュしたリポジトリを選択
   - **Branch:** `main`
   - **Main file path:** `src/frontend/app_hybrid.py`
4. **"Advanced settings"** をクリックし、**Secrets** 欄に以下を入力します:

```toml
# .streamlit/secrets.toml

# Google Gemini API Key (AI Studioで取得)
GOOGLE_API_KEY = "your-api-key-here"

# アプリケーションの簡易パスワード
APP_PASSWORD = "secret-password-123"
```
5. **"Deploy!"** をクリックします。

## 3. 運用フロー

### A. 事前Webインタビュー (社長)
1. 社長に **アプリのURL** と **パスワード** を伝えます。
2. 社長がアクセスし、パスワードを入力してログインします。
3. チャット形式でインタビューに答えます（途中スキップ可）。
4. 終了時（または中断時）、**「📥 データを保存」** ボタンを押し、`jigyokei_chat_log.json` をダウンロードします。
5. このJSONファイルを、メール等で支援担当者に送付します。

### B. 当日支援 (支援担当者)
1. 支援担当者がアプリを開き、パスワードでログインします。
2. サイドバーで **"Editor Mode"** を選択します。
3. **"📂 Load Previous Session"** に、社長から受け取ったJSONファイルをアップロードします。
4. **"🔄 チャット履歴からデータを抽出・変換"** ボタンを押します。
5. AIが入力済みにしてくれたフォームを見ながら、不足箇所を埋めていきます。
