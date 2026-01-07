
あなたは自宅PCのAntigravityです。
これから作業を開始するにあたり、まずは以下の手順で開発環境を最新の状態に同期（セットアップ）してください。

### 1. リポジトリの同期とブランチ切り替え
職場PCで作成された「安定復旧版ブランチ」を取得し、作業環境を整えます。

```powershell
# プロジェクトディレクトリへ移動
cd c:\Users\kitahara\Desktop\script\jigyokei-app

# リモートの最新情報を取得
git fetch origin

# 最新の作業ブランチに切り替え
git checkout work/restore-from-1209

# 最新の状態・履歴を確認
git pull origin work/restore-from-1209
git log -n 5 --oneline
```

### 2. 依存関係と仮想環境の確認 (念のため)
```powershell
# 必要なライブラリがインストールされているか確認
pip install -r requirements.txt
```

### 3. 初期動作確認
環境が正しく同期できているか、検証スクリプトを実行して確認してください。
```powershell
# app_hybrid.py のインポートテスト（構文チェック）
python scripts/verify_app_import.py
```
*   `SUCCESS` または `ImportError` 以外のエラー（Mock関連のエラーなど）であれば、環境同期は成功しています。
*   `ModuleNotFoundError` が出る場合はライブラリ不足です。

---
**セットアップが完了しました。**
続いて、具体的な作業内容(タスク)が記載された「引き継ぎ指示プロンプト(HANDOVER_TO_HOME.md)」を実行してください。
