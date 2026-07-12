---
description: スライド(.pptx)を生成。用途・内容が自然文でもテーマ・構成を推定して作成、フラグ指定で精密に制御も可
argument-hint: "(作りたい資料の内容、または content.json [--theme --pattern --template --accent --font --variant])"
---

`jp-slides` スキルの方針でスライド(.pptx)を生成する。軽い経路(自然文からの組み立て)と精密経路(コンテンツ JSON・フラグ指定)の両方に対応する。

## 手順

1. 入力を受け取る。「◯◯についての月次報告スライドを作って」のような自然文の依頼、貼り付けられた会議メモ・報告内容、または完成済みのコンテンツ JSON のいずれも受け付ける。
2. **軽い経路(既定)**: 自然文・貼付内容から構成パターン([jp-bizdoc/references/slides.md](../skills/jp-bizdoc/references/slides.md) の結論先行型/経緯報告型/比較検討型)を推定し、[jp-slides/SKILL.md](../skills/jp-slides/SKILL.md) のコンテンツ JSON スキーマに沿って内容を組み立てる。テーマは用途(社内向け/対外提案/夜間投影 等)から妥当なものを推定する。用途・想定読み手・テーマの方向性が不明瞭な場合のみ最小限確認し、明白なら確認を省いて初稿を作ってから調整を提案する。
3. 組み立てたコンテンツ JSON を一時ファイルに保存し、`python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" build <content.json> [--out <出力先>]` で生成する。
4. **精密経路**: 利用者がテーマ・アクセント色・フォント・ブランドテンプレート・ライト/ダークを明示指定した場合は、対応するフラグ(`--theme` `--accent` `--font` `--template` `--variant`)を `build` に渡す。テーマを見比べたい場合は `gallery`(または `overview`)サブコマンドの実行として案内し、`python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_slides.py" gallery [--out-dir <dir>]`(16テーマ見本一括生成 + `overview.pptx`)を実行して選んでもらう。`themes` コマンドで一覧だけ確認することもできる。
5. 生成後、パスと使用テーマ・パターンを報告する。テーマ変更・トーン調整の希望があれば `--theme`/`--accent`/`--variant` を変えて再生成できる旨を伝える。
6. Python または `python-pptx` が無い場合のエラーは `/jp-office-setup` を案内する。
