# コントリビューション / メンテナンス方針

このリポジトリは **日本の事務環境向けの汎用ツール** です。以下を守ってください。

## 1. 公開情報のみ（最重要）
会社固有情報は**一切含めない**: 社名・部署・個人名・顧客/契約・内部URL・認証情報・会社固有の帳票様式・実データ・社内固有の業務手順。
- 含めてよいのは、一般的な事務作業の知識・手順、公開されている祝日データ等のみ。
- ビジネス文書スキル（`jp-bizdoc`）の例示は必ず**架空名**（`株式会社サンプル`・`山田太郎` 等）を用いる。
- **コミット前の自動チェック**: `python tools/check-sensitive.py --staged` が pre-commit フックで走り、会社ドメイン・開発環境ユーザー名・ローカル個人パス・認証情報・内部IP の疑いがあればコミットを止めます。導入は §4。

## 2. バージョン管理
- バージョンは `jp-office/.claude-plugin/plugin.json` の `version` を**基準**とする（semver）。`marketplace.json` の `metadata.version` も同じ値に揃える（単一プラグインのマーケットプレイスのため両者は連動）。
- 変更は `CHANGELOG.md` に記録。利用者側で自動更新を有効にしている場合、`version` を上げて push すると次回起動時に反映されます（README「自動更新」参照）。
- 機能変更はパッチ（x.y.**Z**）以上、後方非互換や大きな機能追加はマイナー（x.**Y**.0）で上げる。

## 3. 情報の鮮度
- 祝日データはライブラリ（`jpholiday`）に依存し、法改正・追加で変わり得る。制度・様式・敬語の作法も改定され得る（本パッケージは 2026-07 時点）。

## 4. pre-commit フックの導入（任意・推奨）
リポジトリ直下で:
```
# Git Bash / macOS / Linux
printf '#!/bin/sh\npython tools/check-sensitive.py --staged\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
以後、`git commit` のたびにステージ内容が自動チェックされます。全ファイルを手動走査するには `python tools/check-sensitive.py --all`。

## 5. テスト
- スクリプトの変更は `jp-office/scripts` で `python -m pytest tests/ -v` を通すこと（ネットワーク不要、ローカル完結）。

## 6. フィードバック
用語・様式・敬語の訂正、機能追加の提案は Issue でお知らせください。
