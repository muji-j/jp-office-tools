---
description: jp-office のスクリプト実行環境(Python・ライブラリ)を点検し、無ければ確認のうえ導入
argument-hint: "(なし)"
---

`jp-office` のスクリプト(Excel クレンジング/diff・PDF 抽出・スライド生成・日付計算)を動かす環境を点検し、
不足があればユーザーに確認してから導入する。

## 手順

### 1. Python の点検
- `python --version`(無ければ `python3 --version` / `py --version`)を実行しバージョン確認(3.10+ が必要)。
- 見つからない場合は**勝手に入れず、必ずユーザーに確認**する。
  - Windows: `winget install -e --id Python.Python.3.12` を**提案**し、同意を得たら実行。失敗時は https://www.python.org/downloads/ を案内。
  - macOS: `brew install python` を提案。Linux: ディストリのパッケージ(apt/dnf 等)を案内。

### 2. ライブラリの点検
`python -c "import <mod>"` の成否で判定:
- **Excel/CSV 系**: `pandas`, `openpyxl`, `matplotlib`(グラフ生成)
- **PDF 系**: `pdfplumber`(テキスト抽出)、`pypdfium2`・`PIL`(スキャンPDFの画像レンダー)
- **スライド系**: `python-pptx`(.pptx 生成、jp-slides)
- **日付系**: `jpholiday`

### 3. 不足があれば確認して導入
- 不足パッケージを一覧で示し、導入可否を**ユーザーに確認**(AskUserQuestion 可)。
- 同意後: `python -m pip install -r "${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt"`

### 3'. (任意)スキャンPDF の OCR
- スキャンPDF(画像)を**オフラインでテキスト化**したい場合のみ、`tesseract` 本体(＋日本語データ `jpn`)と `pytesseract` が必要。
  - Windows: `winget install -e --id UB-Mannheim.TesseractOCR` を提案(日本語データ同梱版)。macOS: `brew install tesseract tesseract-lang`。Linux: `apt install tesseract-ocr tesseract-ocr-jpn` 等。
  - `python -m pip install pytesseract`。
- **不要な場合が多い**: スキャンPDF は `jp_pdf.py render` で画像化し、**Claude の視覚(ビジョン)で直接読み取る**のが既定。tesseract は headless/一括処理向けの任意機能。

### 4. 動作確認
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_dates.py" holiday 2026-01-01` が `元日` を返すか。
- (任意)`python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" themes` がテーマ一覧を返すか(jp-slides 用)。
- Python が無い/導入しない場合も、文書系スキル(jp-bizdoc)は全機能動作する旨を伝える。
