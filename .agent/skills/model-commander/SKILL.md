---
name: model-commander
description: Google gennai SDKを活用し、無料枠（Free Tier）を最大限に活用するための3段階フォールバック制御を行うスキル。
version: 1.0.0
---

# model-commander Skill

このSkillは、APIクォータ制限をインテリジェントに回避し、システムの持続可能性を保証します。

## 📊 調査結果（2026年2月時点）

### 利用可能なモデルと無料枠クォータ

| モデル名 | 世代 | 無料枠 RPD | 無料枠 RPM | 特徴 |
| :--- | :--- | :--- | :--- | :--- |
| `gemini-2.5-pro` | 第1世代 | 25 | 5 | 最高推論力、クォータ極小 |
| `gemini-2.5-flash` | 第1世代 | 500 | 15 | バランス型、主力モデル |
| `gemini-2.0-flash` | 第2世代 | 1,500 | 15 | 大容量、2026/3/31 廃止予定 |
| `gemini-1.5-flash` | 第3世代 | 1,500 | 15 | 枯れた安定版 |
| `gemini-embedding-001` | 最新統合 | - | 5-15 | Embedding専用、100+言語対応 |

---

## 🛠️ タスク別・3段階導入モデル

| タスク分類 | ティア1 (優先) | ティア2 (予備1) | ティア3 (セーフティ) |
| :--- | :--- | :--- | :--- |
| **Reasoning** (監査、プラン) | `gemini-2.5-flash` | `gemini-2.0-flash` | `gemini-1.5-flash` |
| **Draft** (執筆、要約) | `gemini-2.5-flash` | `gemini-2.0-flash` | `gemini-1.5-flash` |
| **Extraction** (解析、変換) | `gemini-2.5-flash` | `gemini-2.0-flash` | `gemini-1.5-flash` |
| **Embedding** (ベクトル生成) | `gemini-embedding-001` | `text-embedding-004` | N/A |

> [!NOTE]
> `gemini-2.5-pro` は無料枠が25 RPDと極小のため、本プロジェクトでは使用しません。

---

## 🔄 フォールバック & Shift-Up プロトコル

1. **Latest-First 原則**: ティア1には常に「最新の安定版（Stable）」を配置。これにより、廃止リスクを最小化し、APIの寿命を最大化する。
2. **gennai SDKの使用**: `google-genai` パッケージを使用。
3. **429エラー検知**: クォータ超過時は自動的に次ティアへスイッチ。
4. **Shift-Up（押し上げ演算）**: ティア3のモデルが廃止された場合、ティア1/2を維持しつつ、新しい最新モデルをティア1へ挿入し、全体を一つずつ押し下げる。
5. **フライトログ記録**: `docs/MODEL_FLIGHT_LOG.md` に稼働モデルを記録。

---

## 📝 実装コード

```python
from google import genai

MODEL_TIERS = {
    "reasoning": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
    "draft": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
    "extraction": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
    "embedding": ["gemini-embedding-001", "text-embedding-004"]
}

def generate_with_fallback(client, task_type, prompt):
    for model in MODEL_TIERS[task_type]:
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                continue
            raise
```
