---
name: technical-writer
description: 実装内容からuser_manual.mdとwalkthrough.mdを自動同期するスキル
version: 1.0.0
---

# technical-writer Skill

コードの変更内容を分析し、ユーザーマニュアル（`user_manual.md`）と実装記録（`walkthrough.md`）を常に最新の状態に保ちます。

## 構成
- 入力: 最近のコード変更（`diff`）、`task.md`
- 出力: 更新された `user_manual.md`, `walkthrough.md`

## 手順
1. **プロトコル遵守の確認**: まず `core-protocol` Skill を参照し、ドキュメントの同期が全フェーズで完了しているかを確認する。
2. **変更の差分分析**: `git diff` や直近の `replace_file_content` 履歴から、どの機能が追加・変更されたかを把握する。
3. **ドキュメントの同時更新 (Rule 2 & 3 Compliance)**:
    - **walkthrough.md**: 実装内容、変更ファイル、およびテスト結果を詳細に記載する。
    - **user_manual.md**: 新機能の使い方やAPIの変更点をエンドユーザー向けに追記する。
    - **docs/DEVELOPMENT_HISTORY.md**: 各フェーズの完了時、その背後にある「開発哲学の進化」やマイルストーンを記録し、理念の推移を損なわないようにする。
    - **docs/USER_JOURNEY.md**: 機能変更がユーザー体験に大きく影響する場合、`ux-storyteller` Skillを呼び出してストーリーを更新する。
    - **task.md**: 完了した項目にチェックを入れ、プロジェクトの進捗を同期する。
4. **品質チェック**: 各ファイルに適切なdocstringやコメントが付与されているか、`core-protocol` の基準に照らして最終確認する。

## 判断基準
- 内部的なリファクタリング（機能変更なし）の場合: `walkthrough.md` のみ更新し、`user_manual.md` は変更しない。
- 大規模な変更の場合: 必要に応じて Mermaid 図面やスクリーンショットのプレースホルダーを追加する。

## 実行例
「Phase 4の実装が終わったから、ドキュメントをまとめて」
→ `technical-writer` が起動
→ `Planner` ノードの追加と12セクション対応を検知
→ 各.mdファイルを自動更新し、レビューを求める
