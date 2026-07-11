"""jp-office: PDF テキスト抽出(テキスト層のみ。スキャンPDF/OCRは非対応)."""
import argparse
import sys

import pdfplumber


class NoTextError(Exception):
    """テキスト層が存在しない(スキャンPDFの可能性)。"""


class PageRangeError(Exception):
    """指定されたページ番号が不正、または範囲外。"""


def _parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    try:
        if "-" in spec:
            lo_s, hi_s = spec.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
        else:
            lo = hi = int(spec)
    except ValueError:
        raise PageRangeError(f"ページ指定 '{spec}' を解釈できません(例: 2 または 1-3)。")
    if lo < 1 or lo > hi:
        raise PageRangeError(f"ページ指定 '{spec}' が不正です(1以上、開始<=終了)。")
    if lo > total:
        raise PageRangeError(f"ページ {lo} は総ページ数 {total} を超えています。")
    return list(range(lo, min(hi, total) + 1))


def extract_text(path, pages: str | None = None) -> str:
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        targets = _parse_pages(pages, total)
        selected = []
        any_text_in_doc = False
        for n in range(1, total + 1):
            page_text = pdf.pages[n - 1].extract_text() or ""
            if page_text.strip():
                any_text_in_doc = True
                if n in targets:
                    selected.append(f"--- p.{n} ---\n{page_text}")
    if not any_text_in_doc:
        raise NoTextError(
            "テキスト層が見つかりません。スキャンPDF(画像)の可能性があります — v0.1 は OCR 非対応です。")
    return "\n\n".join(selected)


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="jp_pdf.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_ext = sub.add_parser("extract")
    p_ext.add_argument("file")
    p_ext.add_argument("--pages")
    args = ap.parse_args(argv[1:])
    print(extract_text(args.file, args.pages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
