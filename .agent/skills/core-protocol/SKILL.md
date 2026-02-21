---
name: core-protocol
description: すべてのSkillsの基盤となる最上位の開発憲法。TDD、ドキュメント品質、およびプロジェクト理念を規定する。
version: 1.0.0
---

# core-protocol Skill

このSkillはプロジェクト全体の最上位指針であり、すべてのAIアクションはこのプロトコルに拘束されます。

## 🏛️ プロジェクトの三代理念 (The Three Ideals)

1. **Business Support (経営支援)**: 「寄り添い・引き出し・導く」ことで、経営者の想いを可視化する。
2. **Architecture (建築的誠実さ)**: 「認定駆動・透明性・持続性」を保ち、システムが制度に適合し続ける。
3. **User Journey (ユーザー体験の守護)**: 常に象徴的なユーザー（佐藤さん）の体験を起点に開発し、過去のUX品質を1ミリも下回らないことを誓う。

## 🛠️ 開発プロトコル (Development Protocol)

### 1. テスト駆動開発（TDD）の徹底
いかなる変更も、以下のサイクルを外れてはなりません。
- **Red**: 失敗するテストコード（domain/unit）を作成する。
- **Green**: テストを通過させる最小限の実装を行う。
- **Refactor**: 理念を維持したまま、コードの品質と可読性を向上させる。

### 2. ドキュメントの同時生成と同期
「コードがある場所には常にドメイン・哲学・体験の記録がある」状態を維持します。
- **user_manual.md / walkthrough.md**: 実装と同時にユーザー価値を更新する。
- **docs/DEVELOPMENT_HISTORY.md**: 開発哲学の推移を記録する。
- **docs/USER_JOURNEY.md**: ユーザー体験の進化と整合性を記録する。

### 3. Consistency & Regression Check
- 新機能が既存の理念や過去のユーザージャーニーと矛盾する場合、またはUX品質を低下させる（退行）場合は、実装を差し戻して再設計する。
- `code-reviewer` および `ux-storyteller` はこの退行チェックを厳格に行う。

### 4. Model Sovereignty (モデル統治)
- **無料枠の絶対優先**: プロジェクト継続性のため、無料枠内での運用を絶対正義とする。
- **3段階フォールバック**: `model-commander` を通じ、最新モデルから順に3世代を使い分けることで安定性を確保する。
- **gennai SDK基準**: 常に `google-genai` SDKを使用し、最新の機能（2.5系など）を活用する。

## 🔗 Skill呼び出しチェーン (Skill Call Chain)

変更やデプロイ時に、以下の順序でSkillを連携させます。

### コード変更時
```
code-reviewer → ux-storyteller → technical-writer
```
1. `code-reviewer`: TDD・命名・docstringをチェック
2. `ux-storyteller`: UX退行がないか確認、USER_JOURNEY.md更新
3. `technical-writer`: user_manual.md / walkthrough.md を同期

### デプロイ時
```
deploy-commander → (全テスト実行) → Git Push
```
1. `deploy-commander`: テスト全通過を条件にデプロイ承認
2. 失敗時は `code-reviewer` へ差し戻し

## 🤖 Auto-Dispatch Protocol（自動呼び出し規約）

AIは `.agent/skill_registry.yaml` を参照し、ユーザーの依頼に応じて自動的にSkillを選択・連鎖実行します。

### 自動選択ルール
1. **キーワードマッチング**: ユーザーの依頼文を解析し、`triggers` キーワードとマッチング
2. **自動連鎖**: マッチしたSkillの `auto_chain` に定義されたSkillを順次実行
3. **常時参照**: `always_consult: true` のSkillは常に参照（`jigyokei-domain-expert`）
4. **常時適用**: `always_active: true` のSkillは全アクションに適用（`core-protocol`）
5. **優先度順**: `priority` 値が低いほど優先的に適用

### 実行フロー例
```
ユーザー: 「新しい関数を追加して」
→ トリガー検知: "追加" → code-reviewer
→ 自動連鎖: code-reviewer → ux-storyteller → technical-writer
→ 常時参照: core-protocol (TDD遵守チェック)
→ 常時参照: jigyokei-domain-expert (ドメイン知識)
```

### 内部API
`model-commander` は `internal: true` として定義され、コード内で自動的に使用されます。ユーザーが明示的に呼び出す必要はありません。
