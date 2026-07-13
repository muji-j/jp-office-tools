"""jp-office: PDF テキスト抽出(テキスト層)+ スキャンPDF対応(レンダー/OCR)."""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import pdfplumber
import pypdfium2


class NoTextError(Exception):
    """テキスト層が存在しない(スキャンPDFの可能性)。"""


class PageRangeError(Exception):
    """指定されたページ番号が不正、または範囲外。"""


class OcrUnavailableError(Exception):
    """tesseract が利用できない(未インストール)場合に送出。"""


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
            "テキスト層がありません(スキャンPDFの可能性)。"
            "`render` で画像化して読み取るか、`extract --ocr`(要tesseract)を使ってください。")
    return "\n\n".join(selected)


def _normalize_rows(rows):
    """表セルの None を "" に正規化し、文字列化して前後空白を除去する。"""
    return [["" if c is None else str(c).strip() for c in row] for row in rows]


def extract_tables(path, pages: str | None = None) -> list[dict]:
    """PDF の対象ページから表を抽出する。各要素は {"page","index","rows"}。表が無ければ []。"""
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        targets = _parse_pages(pages, total)
        results = []
        for n in targets:
            for i, tbl in enumerate(pdf.pages[n - 1].extract_tables(), 1):
                rows = _normalize_rows(tbl)
                if any(any(c for c in row) for row in rows):
                    results.append({"page": n, "index": i, "rows": rows})
    return results


def _rows_to_markdown(rows) -> str:
    """表の行リストをマークダウン表(パイプエスケープ・列数パディング済み)に変換する。"""
    def esc(c):
        return c.replace("|", "\\|").replace("\n", " ")

    ncol = max((len(r) for r in rows), default=0)
    if ncol == 0:
        return ""

    def pad(r):
        return r + [""] * (ncol - len(r))

    lines = ["| " + " | ".join(esc(c) for c in pad(rows[0])) + " |",
             "| " + " | ".join(["---"] * ncol) + " |"]
    for r in rows[1:]:
        lines.append("| " + " | ".join(esc(c) for c in pad(r)) + " |")
    return "\n".join(lines)


def tables_to_markdown(tables) -> str:
    """抽出済みの表リストをマークダウンに変換する。表が無ければ案内文を返す。"""
    if not tables:
        return "(表が見つかりませんでした)"
    return "\n\n".join(f"### p.{t['page']} 表{t['index']}\n\n{_rows_to_markdown(t['rows'])}"
                        for t in tables)


def tables_to_files(tables, out, fmt: str):
    """抽出済みの表を csv/xlsx ファイルへ書き出す(後続タスクで実装)。"""
    raise NotImplementedError("csv/xlsx は後続タスクで実装します。")


def render_pages(path, out_dir=None, pages: str | None = None, scale: float = 2.0) -> list[str]:
    """PDF の対象ページを PNG に描画して保存し、保存先パスのリストを返す(原本は変更しない)。"""
    path = Path(path)
    out_dir = Path(out_dir) if out_dir is not None else path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = pypdfium2.PdfDocument(str(path))
    try:
        total = len(pdf)
        targets = _parse_pages(pages, total)
        saved = []
        for n in targets:
            bitmap = pdf[n - 1].render(scale=scale)
            pil_image = bitmap.to_pil()
            out_path = out_dir / f"{path.stem}_p{n}.png"
            pil_image.save(out_path)
            saved.append(str(out_path))
        return saved
    finally:
        pdf.close()


def ocr_available() -> bool:
    """tesseract 実行ファイルと pytesseract の両方が利用可能かを判定する。"""
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return True


def ocr_text(path, pages: str | None = None, lang: str = "jpn+eng") -> str:
    """tesseract で対象ページを OCR し、ページ区切り付きのテキストを返す。"""
    if not ocr_available():
        raise OcrUnavailableError(
            "tesseract 未インストールです。`/jp-office-setup` を実行するか、"
            "render で画像化して Claude の視覚(ビジョン)で読み取ってください。")
    import pytesseract
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmp_dir:
        img_paths = render_pages(path, out_dir=tmp_dir, pages=pages)
        parts = []
        for img_path in img_paths:
            n = int(Path(img_path).stem.rsplit("_p", 1)[1])
            with Image.open(img_path) as img:
                text = pytesseract.image_to_string(img, lang=lang)
            parts.append(f"--- p.{n} (OCR) ---\n{text}")
        return "\n\n".join(parts)


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="jp_pdf.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_ext = sub.add_parser("extract")
    p_ext.add_argument("file")
    p_ext.add_argument("--pages")
    p_ext.add_argument("--ocr", action="store_true")
    p_ren = sub.add_parser("render")
    p_ren.add_argument("file")
    p_ren.add_argument("--pages")
    p_ren.add_argument("--out-dir")
    p_ren.add_argument("--scale", type=float, default=2.0)
    p_tbl = sub.add_parser("extract-table")
    p_tbl.add_argument("file")
    p_tbl.add_argument("--pages")
    p_tbl.add_argument("--format", default="md", choices=["md", "csv", "xlsx"])
    p_tbl.add_argument("--out")
    args = ap.parse_args(argv[1:])
    try:
        if args.cmd == "extract":
            if args.ocr:
                print(ocr_text(args.file, pages=args.pages))
            else:
                print(extract_text(args.file, args.pages))
        elif args.cmd == "render":
            for saved_path in render_pages(
                    args.file, out_dir=args.out_dir, pages=args.pages, scale=args.scale):
                print(saved_path)
        elif args.cmd == "extract-table":
            tables = extract_tables(args.file, pages=args.pages)
            if args.format == "md":
                print(tables_to_markdown(tables))
            else:
                for p in tables_to_files(tables, args.out, args.format):
                    print(p)
        return 0
    except OcrUnavailableError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
