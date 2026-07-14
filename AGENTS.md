# AGENTS.md — jp-office-tools

日本の業務環境向けの公開・汎用 Office ツールプラグインリポジトリ。Excel/CSV/PDF/Word/PPTX と日本語業務文書を扱うが、特定企業のデータや様式は含めない。

## Repository Rules

- 回帰: `cd jp-office/scripts; py -3 -m pytest tests/ -v`。
- 機微情報ゲート: `py -3 tools/check-sensitive.py --all`。
- DOCX、PDF、PPTX、XLSX の変更は構造検査だけで終えず、インストール済みのレンダリングスキルで実際の表示を確認する。
- 日本語エンコーディング、フォント置換、表・グラフの切れ、数式・シート・データ保持、テンポラリファイルの整理を確認する。
- 機能変更時は README、CHANGELOG、marketplace/plugin version、サンプル、ギャラリーの同期要否を確認する。
- 公開リポジトリに会社名、内部 URL、実際の契約・顧客情報、社内様式を含めない。

## Codex Agent Routing

- `.codex/agents/*.toml` は JP シリーズ共通の Codex エージェント群であり、`common`、`jp-power-tools` とバイト単位で同一に保つ。Claude エージェントとプラグインファイルは別資産として扱う。
- 探索=`scout`、設計=`plan-architect`、Python=`script-engineer`、文書=`content-author`、HTML/ギャラリー=`dashboard-engineer`。
- Office レンダリング=`office-artifact-auditor`、機微情報=`sensitivity-auditor`、仕様=`spec-reviewer`、テスト=`test-runner`、最終監査=`deep-reviewer`、出荷=`release-engineer`。電力事実確認エージェントは電力関連作業にだけ使用する。
- root を含めて最大 4 threads、depth 1。実装担当と read-only reviewer を分離する。
- ユーザーへの説明・報告はユーザーが使用した言語に合わせ、判別できない場合は日本語を使用する。コマンド、パス、識別子、公式名称は翻訳しない。
- リモート push と release はユーザー承認後にのみ実行する。
- Codex の変更はワークスペースルートの `../CODEX_HANDOFF.md` に記録する。単独 checkout で利用できない場合は、その旨を報告する。
