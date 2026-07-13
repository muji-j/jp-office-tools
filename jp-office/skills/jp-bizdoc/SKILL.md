---
name: jp-bizdoc
description: 日本のビジネス文書の作成・添削全般 — 議事録, 稟議書, 報告書(月次・出張), メールの敬語添削, スライド(PPT)構成案, ビジネス文書の日韓英翻訳, PDF の読み取り・要約・表抽出, 表記ゆれの検出・用語集作成の際に使用(メールの作成・返信・日程調整は jp-mail スキルに委ねる)。キーワード - 議事録, 稟議, 決裁, 報告書, メール添削, 敬語, 添削, 時候の挨拶, スライド構成, 資料構成, 翻訳, 用語集, PDF要約, PDF表抽出, 表記ゆれ, 表記統一。
---

# jp-bizdoc — 日本型ビジネス文書

## 鉄則

1. 文書テンプレートは [references/templates.md](references/templates.md) の構成に従う。項目の省略は依頼者に確認してから。
2. 敬語・メール添削は [references/keigo.md](references/keigo.md) の NG パターン表に照らして行い、**修正文 + 修正理由の一覧**をセットで示す。
3. 議事録で担当・期限が読み取れない場合は勝手に補完せず**「要確認」**と明記する。期限の計算(◯営業日後 など)は `jp-dates` スキルに委ねる。
4. スライド構成は [references/slides.md](references/slides.md)、翻訳の用語一貫性は [references/translation.md](references/translation.md) を参照。
5. PDF は `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_pdf.py" extract <file> [--pages 1-3]` でテキスト化してから扱う。**スキャンPDF(画像)**でテキスト層が無い場合は、`jp_pdf.py render <file> [--pages]` でページを PNG 画像に描画し、その画像を**視覚(ビジョン)で直接読み取る**(既定・推奨)。オフラインで文字列が必要なら `extract --ocr`(要 tesseract、無ければ案内)。PDF内の表だけを抜き出したい場合は `jp_pdf.py extract-table <file> [--pages] [--format md|csv|xlsx] [--out]` を使う(`/pdf-table` コマンド参照)。
6. 成果物に実在の社名・個人名を例として使わない(架空名: 株式会社サンプル, 山田太郎 等)。
7. 文章の作成・添削では [references/anti-ai.md](references/anti-ai.md) に照らし、AIっぽい定型の乱発を避ける。発信者のトーン指定・例文があればそれを最優先で反映する。
8. 文体(敬体/常体)の統一は [references/style.md](references/style.md) に従う。文書種別の既定文体に合わせ、混用は指摘して統一する(敬語の正確さ=keigo.md とは別の観点)。
9. 表記ゆれの検出・用語集の作成は [references/glossary.md](references/glossary.md) の原則に従う。`python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_glossary.py" variants|terms <file|->` で候補を機械的に抽出できるが、確実に検出できるのはカタカナ長音・全角半角のゆれのみ。漢字の送り仮名のゆれ(例: 取り組み↔取組み)は連続した文章だとスクリプトがほとんど拾えないため、スクリプトに頼らずClaudeが文脈から判断する(`/glossary` コマンド参照)。
