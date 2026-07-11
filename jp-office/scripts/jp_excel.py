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
    if Path(path).suffix.lower() in (".xlsx", ".xlsm"):
        return "xlsx", "xlsx はバイナリ形式のため文字コード判定は不要(先頭シートを読み込みます)"
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


def _count_lines(path, limit):
    n = 0
    with open(path, "rb") as fh:
        for _ in fh:
            n += 1
            if n > limit:
                break
    return n


def _xlsx_sheet_names(path) -> list[str]:
    return pd.ExcelFile(path).sheet_names


def _read(path: Path) -> tuple[pd.DataFrame, str, str]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        enc, _ = detect_encoding(path)
        names = _xlsx_sheet_names(path)
        df = pd.read_excel(path, sheet_name=names[0], dtype=str)
        note = ""
        if len(names) > 1:
            note = (
                f"⚠️ '{path.name}' には複数シート(合計{len(names)}枚)があります。"
                f"先頭シート「{names[0]}」のみを処理しました。"
            )
        return df, enc, note
    enc, _ = detect_encoding(path)
    return pd.read_csv(path, dtype=str, encoding=enc, encoding_errors="replace"), enc, ""


def clean_file(src, dst=None, *, encoding_out: str = "utf-8-sig") -> CleanReport:
    src = Path(src)
    if src.suffix.lower() not in (".xlsx", ".xlsm") and _count_lines(src, ROW_GUARD + 1) - 1 > ROW_GUARD:
        raise RowGuardError(f"行数がガード{ROW_GUARD}行を超えています。ファイルを分割してから再実行してください。")
    df, enc_in, note = _read(src)
    if len(df) > ROW_GUARD:
        raise RowGuardError(f"{len(df)}行 > ガード{ROW_GUARD}行。ファイルを分割してから再実行してください。")
    dst = Path(dst) if dst else src.with_name(f"{src.stem}_cleaned.csv")
    if dst.resolve() == src.resolve():
        raise ValueError("出力先が入力と同一です(原本は変更しない方針)。--out で別名を指定してください。")
    rep = CleanReport(str(src), str(dst), enc_in, encoding_out,
                      n_rows=len(df), n_cols=len(df.columns))
    if note:
        rep.notes.append(note)

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
        iso = wareki_to_iso(out, full=True)
        if iso and iso != out:
            rep.cells_wareki += 1
            out = iso
        return out

    cleaned = df.map(_clean_cell)
    cleaned.to_csv(dst, index=False, encoding=encoding_out)
    return rep


@dataclass
class DiffReport:
    changed: list = field(default_factory=list)      # (row_label, col, old, new)
    added_rows: list = field(default_factory=list)
    removed_rows: list = field(default_factory=list)
    added_cols: list = field(default_factory=list)
    removed_cols: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    LIMIT: int = 200

    def to_markdown(self) -> str:
        lines = ["## 差分レポート"]
        lines += [f"- {w}" for w in self.warnings]
        lines.append(f"- 変更セル: {len(self.changed)}件 / 追加行: {len(self.added_rows)}件"
                     f" / 削除行: {len(self.removed_rows)}件")
        if self.added_cols:
            lines.append(f"- 追加列: {', '.join(self.added_cols)}")
        if self.removed_cols:
            lines.append(f"- 削除列: {', '.join(self.removed_cols)}")
        if self.changed:
            lines += ["", "| 行 | 列 | 旧 | 新 |", "|---|---|---|---|"]
            lines += [f"| {r} | {c} | {o} | {n} |" for r, c, o, n in self.changed[: self.LIMIT]]
            if len(self.changed) > self.LIMIT:
                lines.append(f"| … | | | ほか {len(self.changed) - self.LIMIT}件 |")
        for title, rows in (("追加行", self.added_rows), ("削除行", self.removed_rows)):
            if rows:
                shown = ", ".join(map(str, rows[: self.LIMIT]))
                extra = f" …ほか{len(rows) - self.LIMIT}件" if len(rows) > self.LIMIT else ""
                lines.append(f"- {title}: {shown}{extra}")
        return "\n".join(lines)


def _fill(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("")


def diff_files(a, b, *, key: str | None = None) -> DiffReport:
    da, _, note_a = _read(Path(a))
    db, _, note_b = _read(Path(b))
    da, db = _fill(da), _fill(db)
    rep = DiffReport()
    rep.warnings = [n for n in (note_a, note_b) if n]
    rep.added_cols = [c for c in db.columns if c not in da.columns]
    rep.removed_cols = [c for c in da.columns if c not in db.columns]
    common_cols = [c for c in da.columns if c in db.columns]
    if key:
        for label, df_ in (("A", da), ("B", db)):
            if key not in df_.columns:
                raise ValueError(f"--key 列 '{key}' がファイル{label}に存在しません。")
            col = df_[key]
            if (col == "").any():
                raise ValueError(
                    f"--key 列 '{key}' に空の値があります(ファイル{label})。"
                    "位置基準の比較を使うか、データを修正してください。")
            dup = col[col.duplicated()].unique()
            if len(dup):
                raise ValueError(
                    f"--key 列 '{key}' に重複があります(ファイル{label}): "
                    f"{', '.join(map(str, dup[:5]))} — 位置基準の比較を使うか、重複を解消してください。")
        ia = da.set_index(key, drop=False)
        ib = db.set_index(key, drop=False)
        rep.added_rows = [k for k in ib.index if k not in ia.index]
        rep.removed_rows = [k for k in ia.index if k not in ib.index]
        for k in ia.index:
            if k not in ib.index:
                continue
            for c in common_cols:
                if c == key:
                    continue
                old, new = str(ia.at[k, c]), str(ib.at[k, c])
                if old != new:
                    rep.changed.append((str(k), c, old, new))
    else:
        n = min(len(da), len(db))
        for i in range(n):
            for c in common_cols:
                old, new = str(da.at[i, c]), str(db.at[i, c])
                if old != new:
                    rep.changed.append((f"行{i + 2}", c, old, new))  # ヘッダーを1行目として行番号を表記
        rep.added_rows = [f"行{i + 2}" for i in range(n, len(db))]
        rep.removed_rows = [f"行{i + 2}" for i in range(n, len(da))]
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
    p_dif = sub.add_parser("diff")
    p_dif.add_argument("file_a")
    p_dif.add_argument("file_b")
    p_dif.add_argument("--key")
    args = ap.parse_args(argv[1:])
    if args.cmd == "detect":
        enc, evidence = detect_encoding(args.file)
        print(f"{enc}\t{evidence}")
    elif args.cmd == "clean":
        print(clean_file(args.file, args.out, encoding_out=args.encoding_out).to_markdown())
    elif args.cmd == "diff":
        print(diff_files(args.file_a, args.file_b, key=args.key).to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
