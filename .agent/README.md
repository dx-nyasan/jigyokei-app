# .agent ディレクトリ - Skill-Driven Development System

このディレクトリはプロジェクトのAI開発支援システム（Skill制度）を管理します。

## 🚀 クイックスタート

**ユーザーはSkillを個別に把握・呼び出しする必要はありません。**
AIが `skill_registry.yaml` を参照し、依頼内容に応じて適切なSkillを自動選択・連鎖実行します。

## 📁 構成

```
.agent/
├── README.md              # このファイル
├── skill_registry.yaml    # Skill自動選択ルール
└── skills/                # Skill定義
    ├── core-protocol/     # 最上位憲法（常時適用）
    ├── code-reviewer/     # TDD・命名・docstringチェック
    ├── task-planner/      # TDDテストケース自動生成
    ├── db-architect/      # スキーマ・ER図管理
    ├── deploy-commander/  # テスト駆動デプロイ
    ├── jigyokei-domain-expert/  # 認定基準ドメイン知識
    ├── model-commander/   # Gemini API統治（内部API）
    ├── technical-writer/  # マニュアル同期
    └── ux-storyteller/    # ユーザー体験守護
```

## 🤖 Auto-Dispatch（自動呼び出し）

AIは以下のルールに従い、自動的にSkillを選択します：

1. **キーワードマッチング**: 依頼文と `triggers` キーワードをマッチング
2. **自動連鎖**: `auto_chain` に定義されたSkillを順次実行
3. **常時参照**: `jigyokei-domain-expert`（ドメイン知識）
4. **常時適用**: `core-protocol`（TDD・理念遵守）

### 例
```
ユーザー: 「新しい関数を追加して」
→ code-reviewer → ux-storyteller → technical-writer
```

## 📖 詳細

- 各Skillの詳細は `skills/[skill-name]/SKILL.md` を参照
- 自動選択ルールの詳細は `skill_registry.yaml` を参照
- プロジェクト理念は `skills/core-protocol/SKILL.md` を参照
