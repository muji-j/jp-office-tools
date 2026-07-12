# 変更履歴 (Changelog)

バージョンは `jp-office/.claude-plugin/plugin.json` の `version` を基準とする（semver）。日付は 2026 年。

## v0.5.0 — 2026-07-13
- **jp-slides スキル新設**: 実際の `.pptx` ファイルを生成するテーマエンジン。内蔵16テーマ(ミニマル3・コーポレート4・モダン ボールド3・ダーク2・ソフト ウォーム3・タイポグラフィ1)、5アーキタイプ(minimal-centered/accent-bar/header-band/sidebar/color-block)、5種のスライド(`cover`/`message`/`table`/`image`/`section`)。
- **カスタマイズ3ノブ**: `--accent`(アクセント色上書き)・`--font`(游ゴシック/BIZ UDPGothic/游明朝/メイリオ)・`--variant light|dark`(明暗コヒーレント反転。専用ダークテーマ「墨」「藍鉄」の使用も推奨)。
- **ブランドテンプレート対応**: `--template <既存pptx>` で社内配布済みの `.pptx` を土台にスライドを追加(自動装飾を無効化しテンプレートを尊重)。
- **`/slides` コマンド**: 自然文の依頼から構成(jp-bizdoc の3パターン)・テーマを推定して生成する軽い経路と、フラグ指定の精密経路の両方に対応。`gallery`(全16テーマ見本一括生成)・`overview`(全テーマ4×4比較の1枚)・`themes`(一覧)コマンドも追加。
- 依存追加: `python-pptx`。

## v0.4.1 — 2026-07-13
- **バグ修正（軽微）**: `jp-mail/references/scheduling.md` の jp-dates 連携表「今月末の営業日ベースで」の例が、条件（月末が休日）と選んだ日付（7/31・実際は金曜=営業日）が矛盾していたため、実際に月末が土曜となる日を用いた例（`addbiz 2026-01-31 -1` → 1月30日(金)）に差し替え。実行検証済み。機能変更なし。

## v0.4.0 — 2026-07-12
- **jp-mail スキル新設**: メールの作成・返信・定型文・日程調整。用件別(依頼/お礼/お詫び/催促/報告/断り)×格式度3段の定型、書き出し・結びを画一化しない複数案、`/mail` コマンド(関係・トーンを確認して自然な文面)。
- **AIっぽさの排除・個性**: `jp-bizdoc/references/anti-ai.md`(AIが書いた痕跡の定型8類型→自然な代替、発信者トーン最優先)を追加。文書・メール共通で参照。
- **文体統一**: `jp-bizdoc/references/style.md`(敬体↔常体の対応・文末変換・混用是正)を追加。
- メール作成/返信は jp-mail に集約(jp-bizdoc は敬語添削 `/keigo` を維持)。

## v0.3.0 — 2026-07-12
- **jp-excel 集計・可視化**: `/xl-pivot`(クロス集計→表+CSV)、`/xl-chart`(折れ線/棒/円を PNG/HTML、matplotlib・日本語フォント対応)、`columns`(列構造の把握)を追加。`clean --format xlsx`(多シート保存 xlsx 出力)と「疑わしい列」警告(郵便番号・電話の先頭0消失等)を追加。
- **利用しやすさ(2段導線)**: 列指定が無くても `columns` で構造を把握し集計軸・グラフ種類を提案する簡単経路と、フラグ指定の精密経路の両方を提供。
- **品質**: 多シート diff `--key` をシート単位で隔離(一部シートにキーが無くても他シートの比較は継続)。
- **バグ修正**: `xl-pivot --agg count` が値列の型に関わらず数値強制変換していたため、テキスト列（例: 商品名）を件数集計すると全件 NaN となり件数が 0 になる不具合を修正（`count` 集計時は数値変換をスキップ）。
- 依存追加: `matplotlib`。自動テスト81件パス・1件スキップ。

## v0.2.1 — 2026-07-12
- 配布運用の整備（機能変更なし）: README に自動更新（`extraKnownMarketplaces` の `autoUpdate`）の案内を追加、`CHANGELOG.md`・`CONTRIBUTING.md` を新設、`tools/check-sensitive.py`（会社固有・機微情報の静的チェック）＋ pre-commit 連携を追加。

## v0.2.0 — 2026-07-12
- **jp-excel 複数シート対応**: `clean` は xlsx の全シートを処理し、シートごとに `<名前>_<シート>_cleaned.csv` を出力（シート名を安全化し、衝突時は連番で一意化）。`diff` はシート名を突き合わせてシート単位で比較。`sheets`（一覧）・`--sheet`（1シート指定）を追加。
- **jp-pdf スキャンPDF対応**: `render`（pypdfium2）でページを PNG 画像に描画し Claude の視覚で読み取る方式を既定に。`extract --ocr`（要 tesseract）でオフライン OCR も選択可。
- 依存追加: `pypdfium2`・`pillow`。tesseract は任意。自動テスト58件パス。

## v0.1.0 — 2026-07-12
- 初版・公開配布。3スキル（`jp-excel` / `jp-bizdoc` / `jp-dates`）、6コマンド（`/xl-clean` `/xl-diff` `/giji` `/ringi` `/keigo` `/jp-office-setup`）、3スクリプト（`jp_excel.py` `jp_dates.py` `jp_pdf.py`）。
- 日本の事務環境向け汎用ツール。Excel/CSV の文字コード・全角半角・和暦正規化・diff、議事録/稟議書/敬語メール等のビジネス文書、祝日/営業日/和暦の計算。原本不変・会社固有情報なし。TDD＋横断レビューで実バグ7類型を修正、自動テスト37件パス。
