---
name: technical-writer
description: 実装内容からuser_manual.mdとwalkthrough.mdを自動同期するスキル
---

# technical-writer Skill

コードの変更内容を分析し、ユーザーマニュアル（`user_manual.md`）と実装記録（`walkthrough.md`）を常に最新の状態に保ちます。

## 構成
- 入力: 最近のコード変更（`diff`）、`task.md`
- 出力: 更新された `user_manual.md`, `walkthrough.md`

## 手順
1. **プロトコル遵守の確認**: まず `core-protocol` Skill を参照し、ドキュメントの同期が全フェーズで完了しているかを確認する。
2. **変更の差分分析**: `git diff` や直近の `replace_file_content` 履歴から、どの機能が追加・変更されたかを把握する。
2. **walkthrough.md の更新**:
    - 実装したファイル、関数のリストを更新する。
    - 実行されたテストの結果を記載する。
3. **user_manual.md の更新**:
    - 新しい機能の使い道をエンドユーザー向けに追記する。
    - 既存機能の挙動変更があれば反映する。
4. **task.md との整合性**: `task.md` で完了マークがついた項目が、各ドキュメントに正しく反映されているか確認する。

## 判断基準
- 内部的なリファクタリング（機能変更なし）の場合: `walkthrough.md` のみ更新し、`user_manual.md` は変更しない。
- 大規模な変更の場合: 必要に応じて Mermaid 図面やスクリーンショットのプレースホルダーを追加する。

## 実行例
「Phase 4の実装が終わったから、ドキュメントをまとめて」
→ `technical-writer` が起動
→ `Planner` ノードの追加と12セクション対応を検知
→ 各.mdファイルを自動更新し、レビューを求める
