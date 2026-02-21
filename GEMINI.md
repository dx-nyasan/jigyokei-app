# Antigravity Development Workflow Rules

> これらのルールは全ての開発実装において**必須**です。AIは全てのターンでこのファイルを参照し、遵守します。

---

## 🚨 必須プロトコル（Mandatory Protocols）

### 1. Skill Auto-Dispatch の強制実行

**全ての依頼に対し、AIは以下を実行すること：**

1. `.agent/skill_registry.yaml` を参照し、トリガーキーワードを照合
2. マッチしたSkillの `SKILL.md` を読み込み、指示に従う
3. `auto_chain` に定義されたSkillを順次実行
4. 実行結果を記録

### 2. 常時参照Skill（Always Active）

**以下のSkillは全てのアクションで参照すること：**

| Skill | 参照タイミング | ファイルパス |
| :--- | :--- | :--- |
| `core-protocol` | 全てのアクション | `.agent/skills/core-protocol/SKILL.md` |
| `jigyokei-domain-expert` | ドメイン判断時 | `.agent/skills/jigyokei-domain-expert/SKILL.md` |

### 3. コード変更時の必須チェーン

**コードを追加・修正する際は、以下の順序で必ず実行すること：**

```
task-planner → code-reviewer → ux-storyteller → technical-writer
```

1. **task-planner**: TDDテストを先に作成（Red）
2. **code-reviewer**: TDD・命名・docstringをチェック
3. **ux-storyteller**: UX退行がないか確認
4. **technical-writer**: ドキュメントを同期

### 4. デプロイ時の必須チェーン

**デプロイ・リリース時は、以下を必ず実行すること：**

```
deploy-commander → (全テスト実行) → Git Push
```

- テストが全て通過するまでデプロイしない
- 失敗時は `code-reviewer` へ差し戻し

---

## 🛠️ テスト駆動開発（TDD）

すべての新規実装は以下のサイクルに従うこと:

1. **Red（失敗）**: まず失敗するテストコードを書く
2. **Green（成功）**: テストが通る最小限の実装を行う
3. **Refactor（整理）**: コードを整理し、テストが通ることを確認

```bash
# 実行例
pytest tests/unit/test_xxx.py  # → FAIL (Red)
# 実装追加
pytest tests/unit/test_xxx.py  # → PASS (Green)
# リファクタリング
pytest tests/unit/test_xxx.py  # → PASS (確認)
```

---

## 📝 ドキュメント同時生成

コード生成と同時にドキュメントを作成すること:

- **関数/クラス**: 必ずdocstringを付与（Google Style）
- **新規ファイル**: 先頭にモジュールdocstring
- **複雑なロジック**: インラインコメント
- **API/機能**: user_manual.md に即時反映

---

## 🤖 Model Sovereignty（モデル統治）

- **無料枠の絶対優先**: 無料枠内での運用を絶対正義とする
- **ModelCommander使用**: 直接API呼び出しせず、`src/core/model_commander.py` を経由
- **3段階フォールバック**: gemini-2.5-flash → gemini-2.0-flash → gemini-1.5-flash

---

## 📋 Skill一覧と役割

| Skill | 役割 | トリガー例 |
| :--- | :--- | :--- |
| `core-protocol` | 最上位憲法、TDD・理念遵守 | 常時 |
| `task-planner` | TDDテストケース自動生成 | 「新機能」「実装したい」 |
| `code-reviewer` | TDD・命名・docstringチェック | 「修正」「追加」「実装」 |
| `db-architect` | スキーマ・ER図管理 | 「DB」「テーブル」 |
| `deploy-commander` | テスト駆動デプロイ | 「デプロイ」「リリース」 |
| `jigyokei-domain-expert` | 認定基準ドメイン知識 | 「認定」「審査」「要件」 |
| `model-commander` | Gemini API統治 | 内部API（自動使用） |
| `technical-writer` | マニュアル同期 | 「ドキュメント」「マニュアル」 |
| `ux-storyteller` | ユーザー体験守護 | 「UX」「体験」 |

---

## ⚠️ 違反時の対応

上記ルールに違反した場合:

1. 即座に差し戻し
2. 該当Skillを参照して再実行
3. `task.md` に違反内容を記録

