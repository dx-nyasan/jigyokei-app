
あなたは自宅PCのAntigravityです。
Cycle 1（初期検証）が完了し、環境が安定していることが確認されました。以下のタスクを引き続き実行してください。

### 【現状のコンテキスト (Cycle 1 完了時点)】
*   **現在地:** `work/restore-from-1209` ブランチ (推奨)
*   **検証ステータス:**
    *   `scripts/verify_app_import.py`: **SUCCESS** (インポートテスト合格)
    *   **レポート:** `docs/CYCLE1_VERIFICATION_REPORT.md` を参照してください。技術的な詳細が記載されています。

---

### 【あなたのミッション: 機能の段階的再導入 (Cycle 2〜)】

#### Step 0: 環境確認
まず、セットアップ後に以下のコマンドで現状の健全性を再確認してください。
```powershell
python scripts/verify_app_import.py
```

#### Step 1: 複数災害対応 (Multi-Disaster Support) の導入
1.  以下のコマンドで機能を取り込みます。
    ```powershell
    # feat(core): implement multi-disaster support via context injection (12/10)
    git cherry-pick a0f844a
    ```
2.  **検証:**
    *   コンフリクトが発生した場合は解消してください。
    *   **重要:** cherry-pick後、再度 `python scripts/verify_app_import.py` を実行し、インポートエラーが発生しないか確認してください。
    *   可能であれば `streamlit run src/frontend/app_hybrid.py` を起動し、ダッシュボードやチャットが落ちないか確認してください。

#### Step 2: コンテキスト対応ダッシュボード (Context-aware Dashboard)
*   **注意:** この機能はロジックが複雑なため、Step 1が安定してから検討してください。
*   対象: `git cherry-pick 207ea31` (12/11)

### 完了条件
作業が完了したら、変更を `git push` し、翌日の職場PCへの引き継ぎプロンプトを作成して終了してください。
