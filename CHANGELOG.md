# 変更履歴 (Changelog)

バージョンは `jp-office/.claude-plugin/plugin.json` の `version` を基準とする（semver）。日付は 2026 年。

## v0.3.0 — 2026-07-12
- **jp-excel 集計・可視化**: `/xl-pivot`(クロス集計→表+CSV)、`/xl-chart`(折れ線/棒/円を PNG/HTML、matplotlib・日本語フォント対応)、`columns`(列構造の把握)を追加。`clean --format xlsx`(多シート保存 xlsx 出力)と「疑わしい列」警告(郵便番号・電話の先頭0消失等)を追加。
- **利用しやすさ(2段導線)**: 列指定が無くても `columns` で構造を把握し集計軸・グラフ種類を提案する簡単経路と、フラグ指定の精密経路の両方を提供。
- **品質**: 多シート diff `--key` をシート単位で隔離(一部シートにキーが無くても他シートの比較は継続)。
- 依存追加: `matplotlib`。自動テスト77件パス。

## v0.2.1 — 2026-07-12
- 配布運用の整備（機能変更なし）: README に自動更新（`extraKnownMarketplaces` の `autoUpdate`）の案内を追加、`CHANGELOG.md`・`CONTRIBUTING.md` を新設、`tools/check-sensitive.py`（会社固有・機微情報の静的チェック）＋ pre-commit 連携を追加。

## v0.2.0 — 2026-07-12
- **jp-excel 複数シート対応**: `clean` は xlsx の全シートを処理し、シートごとに `<名前>_<シート>_cleaned.csv` を出力（シート名を安全化し、衝突時は連番で一意化）。`diff` はシート名を突き合わせてシート単位で比較。`sheets`（一覧）・`--sheet`（1シート指定）を追加。
- **jp-pdf スキャンPDF対応**: `render`（pypdfium2）でページを PNG 画像に描画し Claude の視覚で読み取る方式を既定に。`extract --ocr`（要 tesseract）でオフライン OCR も選択可。
- 依存追加: `pypdfium2`・`pillow`。tesseract は任意。自動テスト58件パス。

## v0.1.0 — 2026-07-12
- 初版・公開配布。3スキル（`jp-excel` / `jp-bizdoc` / `jp-dates`）、6コマンド（`/xl-clean` `/xl-diff` `/giji` `/ringi` `/keigo` `/jp-office-setup`）、3スクリプト（`jp_excel.py` `jp_dates.py` `jp_pdf.py`）。
- 日本の事務環境向け汎用ツール。Excel/CSV の文字コード・全角半角・和暦正規化・diff、議事録/稟議書/敬語メール等のビジネス文書、祝日/営業日/和暦の計算。原本不変・会社固有情報なし。TDD＋横断レビューで実バグ7類型を修正、自動テスト37件パス。
