"""jp-office: PDF テキスト抽出(テキスト層のみ。スキャンPDF/OCRは非対応)."""
import argparse
import sys

import pdfplumber


class NoTextError(Exception):
    """テキスト層が存在しない(スキャンPDFの可能性)。"""


def _parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return list(range(int(lo), min(int(hi), total) + 1))
    return [int(spec)]


def extract_text(path, pages: str | None = None) -> str:
    chunks = []
    with pdfplumber.open(path) as pdf:
        targets = _parse_pages(pages, len(pdf.pages))
        for n in targets:
            page_text = pdf.pages[n - 1].extract_text() or ""
            if page_text.strip():
                chunks.append(f"--- p.{n} ---\n{page_text}")
    if not chunks:
        raise NoTextError(
            "テキスト層が見つかりません。スキャンPDF(画像)の可能性があります — v0.1 は OCR 非対応です。")
    return "\n\n".join(chunks)


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
