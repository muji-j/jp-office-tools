---
description: PDF内の表を抽出し、マークダウン表で表示。CSV/Excel(xlsx)への保存にも対応
argument-hint: "<PDFファイル> [--pages 1-3] [--format md|csv|xlsx] [--out 出力パス]"
---

`jp-bizdoc` スキルの方針(SKILL.md 鉄則5)に従い、PDF から表を抽出する。

## 手順

1. 対象PDFのパスを確認する。ページ範囲の指定が無ければ全ページを対象にする。
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_pdf.py" extract-table <file> [--pages 1-3]` を実行する(既定 `--format md`)。マークダウン表がそのまま出力されるので、整形せずに提示する。
3. 「(表が見つかりませんでした)」と出た場合は、スキャンPDF(画像でテキスト層・罫線情報を持たない)の可能性を伝える。`jp_pdf.py render <file> [--pages]` でページをPNG画像に描画し、その画像を**Claudeの視覚(ビジョン)で直接読み取る**(既定・推奨)。
4. 表をファイルに保存したい依頼、または表の件数・列数が多く目視確認より保存が適切な場合は、次のいずれかを提案・実行する。
   - `--format csv`: 表ごとに別ファイル(`<出力名>_p<ページ>_t<番号>.csv`)で保存。
   - `--format xlsx --out <パス>`: 1つのxlsxファイルに、表ごとのシート(シート名 `p<ページ>_t<番号>`)としてまとめて保存。
5. Python/ライブラリ不足のエラーが出たら `/jp-office-setup` を案内する。
