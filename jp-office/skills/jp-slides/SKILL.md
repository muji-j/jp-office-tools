---
name: jp-slides
description: 実際の .pptx ファイル(スライド資料)を生成する際に使用 — 16種のモダンなテーマ(それぞれ固有のデザイン原型)・配色・フォント・ブランドテンプレートを指定したプレゼン資料の作成、KPI・指標を見せる統計(stats)スライド、テーマ一覧・見本ギャラリーの出力。キーワード - スライド作成, pptx, PowerPoint, プレゼン資料, デッキ作成, テーマ, 配色, ブランドテンプレート, ギャラリー, スライドテーマ, モダンデザイン, 統計スライド, KPIスライド, 指標。
---

# jp-slides — スライド(.pptx)生成

## 鉄則

1. スライドの構成(章立て・メッセージの組み立て方)は [jp-bizdoc/references/slides.md](../jp-bizdoc/references/slides.md) の3パターン(結論先行型/経緯報告型/比較検討型)と共通原則に従う: **1スライド1メッセージ**(主張は1枚に1つ)、**メッセージラインは文で書く**(「◯◯の状況」ではなく「◯◯は前月比◯%増加した」のように結論を一文で言い切る)、**根拠のない形容詞を使わない**(「大幅に」「順調に」等は数値・比較対象とセットでなければ使わない)。
2. 成果物に実在の社名・個人名を例として使わない(架空名: 株式会社サンプル, 山田太郎 等)。
3. 日付(表紙の日付・和暦変換・営業日基準の締切日 等)の計算は `jp-dates` スキルに委ねる。
4. テーマ・トーン(コーポレート/モダン/ソフト 等)が依頼から不明瞭な場合は最小限の確認(用途・想定読み手・格式度)をしたうえで初稿を作る。用途が明白な場合(例:「社内向け月次報告」)は確認を省き初稿を作ってから調整を提案してよい。テーマに迷えば `themes` 一覧または `gallery`(見本一括生成)を案内する。
5. Python または `python-pptx` が無い場合は `/jp-office-setup` を案内する(この機能は Python 必須)。

## コンテンツ JSON スキーマ

`build` に渡すコンテンツファイルは以下の形。トップレベルの `theme`/`pattern`/`accent`/`font`/`variant`/`template` は CLI の同名フラグで上書きできる(フラグが優先)。

```json
{
  "meta": { "title": "月次営業報告", "date": "2026年7月13日", "author": "企画部 山田太郎", "audience": "部内向け" },
  "pattern": "conclusion",
  "theme": "藍",
  "slides": [
    { "type": "cover", "title": "月次営業報告", "subtitle": "2026年6月度",
      "date": "2026年7月13日", "author": "企画部 山田太郎", "submitted_to": "◯◯部長" },
    { "type": "section", "title": "結論" },
    { "type": "message", "headline": "6月の売上は前月比12%増加した",
      "body": ["新規契約が8件成立", "解約はゼロ", "主力商品Aが牽引"] },
    { "type": "stats", "headline": "主要指標の伸び", "items": [
      { "value": "182億", "label": "エネルギー事業", "note": "+18%" },
      { "value": "24億", "label": "SaaS事業", "note": "黒字化" },
      { "value": "97億", "label": "海外事業", "note": "+4%" }
    ] },
    { "type": "table", "headline": "案の比較", "columns": ["評価軸", "A案", "B案"],
      "rows": [["コスト", "低", "高"], ["納期", "3週間", "5週間"]] },
    { "type": "image", "headline": "売上推移", "image": "chart.png", "caption": "出典: 社内集計" }
  ]
}
```

- `meta`: `title`/`date`/`author`/`audience`(いずれも任意。表紙・ファイル名の既定に使う)
- `pattern`: `conclusion`(結論先行型) / `incident`(経緯報告型) / `comparison`(比較検討型)。構成の目安であり、`slides` は自由に組んでよい。
- `theme`: 内蔵テーマ名(下記16種、それぞれ固有のモダンデザイン原型)。既定は「藍」。
- `template`: 既存の会社ブランド `.pptx`(社内テンプレート)を土台にする場合のパス。指定時は背景色・装飾の自動描画を行わず、テンプレートのレイアウト・配色をそのまま活かす。
- `accent`/`font`/`variant`: テーマの部分上書き(下記「カスタマイズ」参照)。
- `slides[].type`: `cover`(title/subtitle/date/author/submitted_to/audience/stat{value,label}) / `message`(headline/body[]) / `stats`(headline/items[]。items は `value`(必須)/`label`(必須)/`note`(任意)を持つオブジェクトの配列。KPI・指標を数字で見せたい場合に使う) / `table`(headline/columns[]/rows[][]) / `image`(headline/image/caption) / `section`(title)。stats の詳細・レイアウト(テーマごとの並べ方)は [references/themes.md](references/themes.md) を参照。

## 使い方

| 目的 | コマンド |
|---|---|
| テーマ一覧(16種) | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" themes` |
| スライド生成 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" build <content.json> [--pattern conclusion\|incident\|comparison] [--theme <テーマ名>] [--template <既存pptx>] [--accent #RRGGBB] [--font yu-gothic\|biz-ud\|yu-mincho\|meiryo] [--variant light\|dark] [--out <出力pptx>]` |
| 全16テーマの見本一括生成 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" gallery [--out-dir <ディレクトリ>]` |
| 全テーマ比較の1枚もの | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" overview [--out <出力pptx>]` |

CLI のフラグはコンテンツ JSON の同名項目を上書きする(例: JSON で `"theme": "藍"` でも `--theme 朱` を渡せば朱になる)。

### カスタマイズ

- `--accent #RRGGBB`: テーマのアクセント色だけを差し替える(配色の基調はテーマのまま)。
- `--font`: `yu-gothic`(游ゴシック) / `biz-ud`(BIZ UDPGothic) / `yu-mincho`(游明朝、見出しのみ) / `meiryo`(メイリオ) の4種のみ指定可。未導入環境では PowerPoint 側でフォールバック表示になる。
- `--variant light|dark`: ライト/ダークの配色をコヒーレントに反転する簡易切替。**ダーク品質を優先する場合は反転より専用ダークテーマ(墨・藍鉄)を選ぶ方が仕上がりが良い。**
- テーマ・ノブの詳細(パレット・アーキタイプ・用途別の選び方)は [references/themes.md](references/themes.md) を参照。

### ブランドテンプレート(社内フォーマットの活用)

`--template <既存pptx>` を指定すると、そのテンプレートの `Presentation` を土台にスライドを追加する(自動の背景塗り・装飾バーは描画しない)。社内配布済みのブランド `.pptx` を土台にしたい場合はこちらを使う。

### 見本の確認(gallery / overview)

テーマ選びに迷ったら `gallery` で16テーマ全部を同一サンプル内容で一括生成し、見比べる(`overview.pptx` は全テーマを4×4の1枚にまとめた比較シート)。`/slides` の精密経路からは `gallery`/`overview` サブコマンドの実行として案内できる。

## 2段導線

- 軽い経路: 「◯◯についての報告スライドを作って」のような自然文の依頼を受け付け、内容をヒアリング(または貼付資料から抽出)しながら上記コンテンツ JSON を組み立て、`pattern`・`theme` を用途から推定して `build` する。テーマ・トーンが不明瞭な場合のみ最小限確認する。
- 精密経路: コンテンツ JSON を用意済み、またはテーマ・アクセント・フォント・テンプレートを明示指定したい場合はフラグを直接指定する。テーマを見比べたい場合は `themes`/`gallery`/`overview` サブコマンドを案内する。

いずれも `/slides` コマンドから利用できる([commands/slides.md](../../commands/slides.md))。
