"""jp-office: Excel/CSV ワークベンチ — 診断・クレンジング・diff(原本は変更しない)."""
import argparse
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from jp_dates import wareki_to_iso

ROW_GUARD = 500_000


class RowGuardError(Exception):
    """行数ガード(ROW_GUARD)超過。分割処理を案内する。"""


def detect_encoding(path) -> tuple[str, str]:
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", "UTF-8 BOM を検出"
    for enc in ("utf-8", "cp932", "euc_jp"):
        try:
            raw.decode(enc)
            return enc, f"{enc} で厳密デコード成功"
        except UnicodeDecodeError:
            continue
    return "cp932", "全候補で厳密デコード失敗 — cp932(errors='replace') でフォールバック"


@dataclass
class CleanReport:
    src: str
    dst: str
    encoding_in: str
    encoding_out: str
    cells_nfkc: int = 0
    cells_wareki: int = 0
    cells_stripped: int = 0
    n_rows: int = 0
    n_cols: int = 0
    notes: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "## クレンジング レポート",
            f"- 入力: `{self.src}` ({self.encoding_in})",
            f"- 出力: `{self.dst}` ({self.encoding_out})",
            f"- サイズ: {self.n_rows}行 × {self.n_cols}列",
            f"- NFKC正規化セル: {self.cells_nfkc} / 和暦→ISO変換セル: {self.cells_wareki}"
            f" / 前後空白除去セル: {self.cells_stripped}",
        ]
        lines += [f"- 注記: {n}" for n in self.notes]
        return "\n".join(lines)


def _read(path: Path) -> tuple[pd.DataFrame, str]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        return pd.read_excel(path, dtype=str), "(xlsx)"
    enc, _ = detect_encoding(path)
    return pd.read_csv(path, dtype=str, encoding=enc), enc


def clean_file(src, dst=None, *, encoding_out: str = "utf-8-sig") -> CleanReport:
    src = Path(src)
    df, enc_in = _read(src)
    if len(df) > ROW_GUARD:
        raise RowGuardError(f"{len(df)}行 > ガード{ROW_GUARD}行。ファイルを分割してから再実行してください。")
    dst = Path(dst) if dst else src.with_name(f"{src.stem}_cleaned.csv")
    if dst.resolve() == src.resolve():
        raise ValueError("出力先が入力と同一です(原本は変更しない方針)。--out で別名を指定してください。")
    rep = CleanReport(str(src), str(dst), enc_in, encoding_out,
                      n_rows=len(df), n_cols=len(df.columns))

    def _clean_cell(v):
        if not isinstance(v, str):
            return v
        out = v
        stripped = out.strip()
        if stripped != out:
            rep.cells_stripped += 1
            out = stripped
        nfkc = unicodedata.normalize("NFKC", out)
        if nfkc != out:
            rep.cells_nfkc += 1
            out = nfkc
        iso = wareki_to_iso(out)
        if iso and iso != out:
            rep.cells_wareki += 1
            out = iso
        return out

    cleaned = df.map(_clean_cell)
    cleaned.to_csv(dst, index=False, encoding=encoding_out)
    return rep


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="jp_excel.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_det = sub.add_parser("detect")
    p_det.add_argument("file")
    p_cln = sub.add_parser("clean")
    p_cln.add_argument("file")
    p_cln.add_argument("--out")
    p_cln.add_argument("--encoding-out", default="utf-8-sig", choices=["utf-8-sig", "cp932"])
    args = ap.parse_args(argv[1:])
    if args.cmd == "detect":
        enc, evidence = detect_encoding(args.file)
        print(f"{enc}\t{evidence}")
    elif args.cmd == "clean":
        print(clean_file(args.file, args.out, encoding_out=args.encoding_out).to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
