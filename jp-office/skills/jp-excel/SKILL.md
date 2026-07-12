---
name: jp-excel
description: Excel/CSVファイルの取り扱い全般 — 文字化け・エンコーディング変換(Shift-JIS/CP932/UTF-8)、全角半角・和暦日付の正規化、ファイル比較(diff、xlsxは全シート対応)、集計・グラフ作成の際に使用。キーワード - 文字化け, Shift-JIS, CP932, BOM, 全角, 半角, CSV, Excel, xlsx, シート, セル結合, 突合, 差分比較, ピボット, クロス集計。
---

# jp-excel — Excel/CSV ワークベンチ(日本の事務環境向け)

## 鉄則

1. **原本は絶対に上書きしない。** 変換・整形は必ず別名コピー(`_cleaned` 等)に出力する。スクリプトもこの方針で実装されている。
2. エンコーディングを推測で断定しない。まず `detect` で判別根拠ごと確認する。
3. 集計・比較の前にクレンジング(全角数字・空白・和暦の正規化)を通す — 「同じに見えて別の値」が日本のデータ品質問題の大半。
4. 落とし穴の類型は [references/pitfalls.md](references/pitfalls.md)、定型作業の手順は [references/recipes.md](references/recipes.md) を参照。
5. 和暦・営業日の計算は `jp-dates` スキルのスクリプトに委ねる。

## スクリプト(要 Python — 無ければ /jp-office-setup)

| 目的 | コマンド |
|---|---|
| エンコーディング判別 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" detect <file>` |
| シート一覧(xlsx) | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" sheets <file>` |
| クレンジング(コピーに出力) | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" clean <file> [--out X] [--encoding-out utf-8-sig\|cp932] [--sheet シート名]` |
| 差分比較 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" diff <A> <B> [--key 列名] [--sheet シート名]` |

出力エンコーディングの既定は `utf-8-sig`(Excel がそのまま開ける)。行数ガードはシートごとに 50万行。

**xlsx の複数シート**: `clean` は全シートを処理し、シートごとに `<名前>_<シート名>_cleaned.csv` を出力する(レポートにシート別の一覧)。`diff` はシート名を突き合わせてシート単位で比較する。特定の1シートだけを扱うときは `--sheet シート名` を付ける。
