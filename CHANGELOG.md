# 変更履歴 (Changelog)

バージョンは `jp-office/.claude-plugin/plugin.json` の `version` を基準とする（semver）。日付は 2026 年。

## v0.2.1 — 2026-07-12
- 配布運用の整備（機能変更なし）: README に自動更新（`extraKnownMarketplaces` の `autoUpdate`）の案内を追加、`CHANGELOG.md`・`CONTRIBUTING.md` を新設、`tools/check-sensitive.py`（会社固有・機微情報の静的チェック）＋ pre-commit 連携を追加。

## v0.2.0 — 2026-07-12
- **jp-excel 複数シート対応**: `clean` は xlsx の全シートを処理し、シートごとに `<名前>_<シート>_cleaned.csv` を出力（シート名を安全化し、衝突時は連番で一意化）。`diff` はシート名を突き合わせてシート単位で比較。`sheets`（一覧）・`--sheet`（1シート指定）を追加。
- **jp-pdf スキャンPDF対応**: `render`（pypdfium2）でページを PNG 画像に描画し Claude の視覚で読み取る方式を既定に。`extract --ocr`（要 tesseract）でオフライン OCR も選択可。
- 依存追加: `pypdfium2`・`pillow`。tesseract は任意。自動テスト58件パス。

## v0.1.0 — 2026-07-12
- 初版・公開配布。3スキル（`jp-excel` / `jp-bizdoc` / `jp-dates`）、6コマンド（`/xl-clean` `/xl-diff` `/giji` `/ringi` `/keigo` `/jp-office-setup`）、3スクリプト（`jp_excel.py` `jp_dates.py` `jp_pdf.py`）。
- 日本の事務環境向け汎用ツール。Excel/CSV の文字コード・全角半角・和暦正規化・diff、議事録/稟議書/敬語メール等のビジネス文書、祝日/営業日/和暦の計算。原本不変・会社固有情報なし。TDD＋横断レビューで実バグ7類型を修正、自動テスト37件パス。
