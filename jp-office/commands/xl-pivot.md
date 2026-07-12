---
description: Excel/CSV をクロス集計(ピボット)し、表を表示して CSV に保存。列指定が無ければ列構造を見て提案
argument-hint: "<ファイル> [--index 列 --values 列 --agg sum|count|mean|max|min]"
---

`jp-excel` スキルの方針で Excel/CSV をクロス集計する。簡単に使える経路を優先する。

## 手順

1. ファイルを受け取る。--index/--values が指定されていない、または自然文の依頼(例:「店舗別・月別の売上合計」)の場合:
   - まず `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" columns <file> [--sheet シート]` で列構造(型・サンプル)を把握する。
   - 集計軸(index)・集計値(values)・集計方法(agg)を推定して利用者に確認する(既定: 文字列/カテゴリ列を index、数値列を values、agg=sum)。明白なら確認を省いて実行してよい。
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" pivot <file> --index 列 --values 列 [--agg ...] [--columns 列] [--sheet シート]` を実行し、マークダウン表と保存先(`_pivot.csv`)を示す。
3. 集計値が文字列化していると合計が 0 になることがある — 事前に `/xl-clean` を案内してもよい。
4. Python/ライブラリ不足のエラーは `/jp-office-setup` を案内。
