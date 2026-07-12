---
description: Excel/CSV からグラフ(折れ線/棒/円)を PNG または HTML で生成。列指定が無ければ列構造を見て提案
argument-hint: "<ファイル> [--kind line|bar|pie --x 列 --y 列 --format png|html]"
---

`jp-excel` スキルの方針でグラフを生成する。簡単に使える経路を優先する。

## 手順

1. ファイルを受け取る。--x/--y が無い、または自然文の依頼(例:「月別の売上を折れ線で」)の場合:
   - `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" columns <file> [--sheet シート]` で列構造を把握。
   - x 軸(日付/カテゴリ列)、y 軸(数値列)、種類(時系列→line、カテゴリ比較→bar、構成比→pie)を推定し確認。明白なら実行。
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" chart <file> --kind line|bar|pie --x 列 --y 列 [--format png|html] [--title ...] [--sheet シート]` を実行。
3. 生成された画像/HTML のパスを示し、画像なら内容を利用者に見せる。日本語フォントが無い環境では文字化けの可能性を伝える。
4. Python/ライブラリ不足は `/jp-office-setup` を案内(matplotlib が必要)。
