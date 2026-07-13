"""jp-office: 表記ゆれ・用語の候補抽出(機械的な候補のみ。判断は Claude/glossary.md)."""
from __future__ import annotations
import argparse
import re
import sys
import unicodedata
from collections import Counter

from jp_office_common import read_text_auto, run_cli

_TOKEN = re.compile(r"[ァ-ヶ][ァ-ヶー]*|[Ａ-Ｚａ-ｚA-Za-z0-9０-９]+|[一-龠々][一-龠々ぁ-ん]{0,11}")


def _norm_key(s: str) -> str:
    k = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[ぁ-んー・\s]", "", k)


def scan_variants(text: str) -> list[dict]:
    groups: dict[str, Counter] = {}
    for tok in _TOKEN.findall(text):
        key = _norm_key(tok)
        if len(key) < 2:
            continue
        groups.setdefault(key, Counter())[tok] += 1
    out = [{"key": k, "surfaces": dict(c)} for k, c in groups.items() if len(c) >= 2]
    out.sort(key=lambda g: -sum(g["surfaces"].values()))
    return out


def term_candidates(text: str) -> list[dict]:
    kata = Counter(re.findall(r"[ァ-ヶ][ァ-ヶー]{2,}", text))
    acro = Counter(re.findall(r"\b[A-Za-z]{2,6}\b", text))
    kanji = Counter(re.findall(r"[一-龠々]{2,4}", text))
    out = []
    for term, n in kata.items():
        out.append({"term": term, "count": n, "kind": "katakana"})
    for term, n in acro.items():
        out.append({"term": term, "count": n, "kind": "acronym"})
    for term, n in kanji.items():
        out.append({"term": term, "count": n, "kind": "kanji"})
    out.sort(key=lambda c: -c["count"])
    return out


def _read_input(arg: str) -> str:
    if arg == "-":
        return sys.stdin.read()
    return read_text_auto(arg)


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="jp_glossary.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("variants", "terms"):
        p = sub.add_parser(name)
        p.add_argument("input", help="ファイルパス、または - で標準入力")
    args = ap.parse_args(argv[1:])
    text = _read_input(args.input)
    if args.cmd == "variants":
        for g in scan_variants(text):
            surfaces = "、".join(f"{s}({n})" for s, n in g["surfaces"].items())
            print(f"表記ゆれ: {surfaces}")
    else:
        for c in term_candidates(text):
            print(f"{c['term']}\t{c['count']}\t{c['kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main, sys.argv))
