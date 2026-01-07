# Jigyokei-App (事業継続力強化計画 電子申請支援システム)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://jigyokei-app-eructgjkiaybbvnqhddnfg.streamlit.app)

中小企業の「事業継続力強化計画（Jigyokei）」認定申請を支援するAIシステムです。

## 🎯 主な機能

### 1. AIインタビュー
- 対話形式で申請書作成に必要な情報を収集
- 業種別の記載例を自動提案
- 一問一答でわかりやすいガイダンス

### 2. ダッシュボード
- 申請書の完成度をリアルタイムで可視化
- 認定要件との差分を自動検出
- **J-SHIS検証機能**: 災害想定の記載要件チェック

### 3. 自動改善（Auto-Refinement）
- **ManualRAG統合**: 認定マニュアルから動的に記載例を取得
- ワンクリックで認定レベルの文章に改善
- 信頼度スコアと改善点を表示

### 4. 下書きシート出力
- Excel形式で下書きシートを出力
- 電子申請システムへのコピペに対応

## 🚀 クイックスタート

```bash
# 依存関係のインストール
pip install -r requirements.txt

# ローカル起動
streamlit run src/frontend/app_hybrid.py
```

## 🏗️ アーキテクチャ

```
src/
├── core/
│   ├── jigyokei_core.py    # AIインタビューエンジン
│   ├── auto_refinement.py  # 自動改善 + ManualRAG統合
│   ├── jshis_helper.py     # J-SHIS検証モジュール
│   ├── manual_rag.py       # ベクター検索エンジン
│   └── audit_agent.py      # 監査エージェント
├── data/
│   └── vector_store.db     # 認定マニュアルのベクターDB
└── frontend/
    └── app_hybrid.py       # Streamlit UI
```

## ✅ 検証済み機能

| 機能 | 状態 |
|:---|:---:|
| J-SHIS検証 | ✅ 100%検出率 |
| ManualRAG統合 | ✅ 動作確認済 |
| PDCA必須チェック | ✅ 12/17対応済 |
| 事業概要200文字チェック | ✅ |

## 📋 テスト

```bash
# ユニットテスト実行
python -m pytest tests/unit/test_jshis_integration.py -v
```

## 📝 ライセンス

Private - 和歌山県商工会連合会