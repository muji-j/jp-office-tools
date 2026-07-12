#!/usr/bin/env python3
"""公開リポジトリに会社固有・機微情報が混入していないか静的チェックする。

pre-commit フック（`.git/hooks/pre-commit`）から `--staged` で呼ばれ、
ステージされたファイル本文を走査してヒットがあればコミットを止める。
手動実行: `python tools/check-sensitive.py <path ...>` / `--all` で追跡ファイル全走査。

高シグナルな確定マーカーのみを対象にして誤検知を抑える。
注: jp-office の jp-bizdoc スキルは「株式会社サンプル」等の架空社名を教材として
意図的に使うため、汎用の法人格パターン（株式会社 等）は対象にしない。実際に漏えい
リスクのある確定マーカー（開発環境ユーザー名・会社ドメイン・ローカル個人パス・
認証情報・内部IP）のみを検査する。
"""
from __future__ import annotations
import hashlib
import re
import subprocess
import sys

# パターンは断片から組み立てる（この検査スクリプト自身が自明に自己ヒットしないように）。
# それでも tools/ 配下（本スクリプト等）は走査対象から除外する。
PATTERNS = [
    (re.compile(r"ポータルレポジトリ|ポータルリポジトリ"), "内部ポータルリポジトリへの言及"),
    (re.compile(r"010_アプリ|Desktop[\\/]個人"), "開発者ローカルの個人パス"),
    (re.compile(r"(?i)(password|passwd|api[_-]?key|secret|access[_-]?token|client[_-]?secret)\s*[:=]\s*[\"'][^\"'\s]{6,}"),
     "認証情報の代入らしき記述"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?<!0\.0\.0\.0)"), "IP アドレスらしき文字列（内部IPの可能性）"),
]

# 走査から除外するパス接頭辞（本スクリプトはパターン断片を含むため）
SKIP_PREFIXES = ("tools/",)
# バイナリ・非テキストは対象外
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc", ".zip", ".pdf", ".xlsx", ".xlsm")

# 機微トークン(開発環境ユーザー名・会社ドメイン)は原文をソースに置かず、
# sha256 ハッシュのみを保持して照合する(原文の再構成を不可能にする)。
_SENSITIVE_HASHES = {
    "b6f72a21a780cac81a7d37aa78f34c64d49a2de2aa384a0b9390ddc819c1d7c7":
        "開発環境の OS ユーザー名らしき文字列",
    "b0a42971ed8eb10bda3125f8d2a147fb7eb413f07050cdef62bc35d62a567d94":
        "会社ドメインらしき文字列",
}
_HASH_WINDOW_LENS = (12, 14)


def _scan_sensitive_hashes(line: str) -> list[str]:
    norm = re.sub(r"[^a-z0-9]", "", line.lower())
    found = []
    for length in _HASH_WINDOW_LENS:
        for i in range(len(norm) - length + 1):
            h = hashlib.sha256(norm[i:i + length].encode()).hexdigest()
            why = _SENSITIVE_HASHES.get(h)
            if why and why not in found:
                found.append(why)
    return found


def _staged_files() -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    return [f for f in out.splitlines() if f.strip()]


def _tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, encoding="utf-8").stdout
    return [f for f in out.splitlines() if f.strip()]


def _staged_content(path: str) -> str:
    r = subprocess.run(["git", "show", f":{path}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def _worktree_content(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def scan(files: list[str], staged: bool) -> list[tuple[str, int, str, str]]:
    hits: list[tuple[str, int, str, str]] = []
    for path in files:
        p = path.replace("\\", "/")
        if p.startswith(SKIP_PREFIXES) or p.endswith(SKIP_SUFFIXES):
            continue
        text = _staged_content(path) if staged else _worktree_content(path)
        if not text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for rx, why in PATTERNS:
                if rx.search(line):
                    hits.append((p, i, why, line.strip()[:120]))
            for why in _scan_sensitive_hashes(line):
                hits.append((p, i, why, line.strip()[:120]))
    return hits


def main(argv: list[str]) -> int:
    try:  # Windows の cp932 コンソールでも日本語メッセージを読めるように
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--staged" in argv:
        files, staged = _staged_files(), True
    elif "--all" in argv:
        files, staged = _tracked_files(), False
    else:
        files = [a for a in argv if not a.startswith("-")]
        staged = False
        if not files:
            print("usage: check-sensitive.py (--staged | --all | <path ...>)", file=sys.stderr)
            return 2
    hits = scan(files, staged)
    if hits:
        print("✖ 機微情報の疑いを検出しました（コミット中止）:", file=sys.stderr)
        for path, ln, why, snippet in hits:
            print(f"  {path}:{ln}  [{why}]  {snippet}", file=sys.stderr)
        print("  → 公開リポジトリには会社固有情報を含めないでください。誤検知なら tools/check-sensitive.py を調整。",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
