---
name: core-protocol
description: すべてのSkillsの基盤となる最上位の開発憲法。TDD、ドキュメント品質、およびプロジェクト理念を規定する。
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
