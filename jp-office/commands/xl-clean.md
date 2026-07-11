---
description: Excel/CSV をクレンジング(エンコーディング判別→全角半角・和暦・空白の正規化)し、コピーに出力してレポートを表示
argument-hint: "<ファイルパス> [--encoding-out utf-8-sig|cp932]"
---

`jp-excel` スキルの方針に従い、指定ファイルをクレンジングする。

## 手順

1. 引数のファイルパスを確認。無ければ「どのファイルを整形しますか」と尋ねる。
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" detect <file>` で判別結果(エンコーディング+根拠)を先に示す。
3. `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" clean <file> [--encoding-out ...]` を実行し、レポート(markdown)をそのまま表示する。
4. 原本は変更されないこと、出力先(`_cleaned`)のパスを明示する。
5. Python/ライブラリ不足のエラーが出たら `/jp-office-setup` を案内する。
