"""jp-office: Excel/CSV ワークベンチ — 診断・クレンジング・diff(原本は変更しない)."""
import argparse
import json
import re
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
        return "xlsx", "xlsx はバイナリ形式のため文字コード判定は不要"
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
    sheet_outputs: list = field(default_factory=list)  # (sheet_name, output_path, rows, cols)
    column_warnings: list = field(default_factory=list)

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
        if self.sheet_outputs:
            lines.append("")
            lines.append("## シート別出力")
            lines.append("| シート | 出力ファイル | 行 | 列 |")
            lines.append("|---|---|---|---|")
            for name, path, rows, cols in self.sheet_outputs:
                lines.append(f"| {name} | `{Path(path).name}` | {rows} | {cols} |")
        if self.column_warnings:
            lines.append("")
            lines.append("## ⚠️ 疑わしい列")
            lines += [f"- {w}" for w in self.column_warnings]
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


def list_sheets(path) -> list[str]:
    """xlsx/xlsm はシート名一覧、CSV は空リストを返す。"""
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        return _xlsx_sheet_names(path)
    return []


_UNSAFE_FILENAME_CHARS = '/\\:*?"<>|'


def _safe_sheet_name(name: str) -> str:
    """シート名をファイル名として安全な文字列に変換(不可文字は '_' に置換)。"""
    out = name
    for ch in _UNSAFE_FILENAME_CHARS:
        out = out.replace(ch, "_")
    return out


def _read(path: Path, sheet: str | None = None) -> tuple[pd.DataFrame, str, str]:
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        enc, _ = detect_encoding(path)
        names = _xlsx_sheet_names(path)
        if sheet is not None:
            if sheet not in names:
                raise ValueError(f"シート「{sheet}」が見つかりません。利用可能なシート: {', '.join(names)}")
            df = pd.read_excel(path, sheet_name=sheet, dtype=str)
            return df, enc, ""
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


_NUM_RE = re.compile(r"^-?[\d,]+(\.\d+)?$")
_DATE_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^(令和|平成|昭和|R\d|H\d|S\d)")


def _infer_column_type(series) -> str:
    vals = [v for v in series if isinstance(v, str) and v.strip() != ""]
    if not vals:
        return "text"
    num = sum(1 for v in vals if _NUM_RE.match(v.strip()))
    dat = sum(1 for v in vals if _DATE_RE.match(v.strip()))
    if num / len(vals) >= 0.8:
        return "numeric"
    if dat / len(vals) >= 0.8:
        return "date"
    return "text"


def column_summary(path, sheet: str | None = None) -> list[dict]:
    """各列の名前・推定型・非空数・ユニーク数・サンプル3件を返す(読み取り専用)。"""
    df, _, _ = _read(Path(path), sheet=sheet)
    out = []
    for col in df.columns:
        s = df[col]
        non_null = [v for v in s if isinstance(v, str) and v.strip() != ""]
        samples = list(dict.fromkeys(non_null))[:3]
        out.append({
            "name": str(col),
            "type": _infer_column_type(s),
            "non_null": len(non_null),
            "n_unique": int(s.nunique(dropna=True)),
            "samples": samples,
        })
    return out


_POSTAL_COL_RE = re.compile(r"郵便|〒|zip|postal", re.I)
_PHONE_COL_RE = re.compile(r"電話|TEL|phone", re.I)


def detect_column_issues(df) -> list[str]:
    issues = []
    for col in df.columns:
        name = str(col)
        vals = [v for v in df[col] if isinstance(v, str) and v.strip() != ""]
        if not vals:
            continue
        if _POSTAL_COL_RE.search(name):
            digits = [re.sub(r"\D", "", v) for v in vals]
            if any(0 < len(d) < 7 for d in digits):
                issues.append(f"「{name}」: 郵便番号で桁数が不足する値があります(先頭0の消失の可能性)。")
        if _PHONE_COL_RE.search(name):
            if any(re.sub(r"\D", "", v) and
                   not unicodedata.normalize("NFKC", v.lstrip()).startswith("0")
                   for v in vals):
                issues.append(f"「{name}」: 電話番号で先頭0が無い値があります(先頭0の消失の可能性)。")
        nums = sum(1 for v in vals if _NUM_RE.match(v.strip()))
        non_num = len(vals) - nums
        if nums / len(vals) >= 0.8 and 0 < non_num <= len(vals) * 0.2:
            issues.append(f"「{name}」: 数値列に見えますが一部に非数値が混在しています(集計時に注意)。")
    return issues


def columns_to_markdown(cols: list[dict]) -> str:
    lines = ["## 列サマリ", "| 列 | 型 | 非空 | ユニーク | サンプル |", "|---|---|---|---|---|"]
    for c in cols:
        samp = ", ".join(c["samples"])
        lines.append(f"| {c['name']} | {c['type']} | {c['non_null']} | {c['n_unique']} | {samp} |")
    return "\n".join(lines)


def _clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    counts = {"nfkc": 0, "wareki": 0, "stripped": 0}

    def _clean_cell(v):
        if not isinstance(v, str):
            return v
        out = v
        stripped = out.strip()
        if stripped != out:
            counts["stripped"] += 1
            out = stripped
        nfkc = unicodedata.normalize("NFKC", out)
        if nfkc != out:
            counts["nfkc"] += 1
            out = nfkc
        iso = wareki_to_iso(out, full=True)
        if iso and iso != out:
            counts["wareki"] += 1
            out = iso
        return out

    cleaned = df.map(_clean_cell)
    return cleaned, counts


def _check_row_guard(df: pd.DataFrame, sheet_label: str = "") -> None:
    if len(df) > ROW_GUARD:
        prefix = f"シート「{sheet_label}」: " if sheet_label else ""
        raise RowGuardError(
            f"{prefix}{len(df)}行 > ガード{ROW_GUARD}行。ファイルを分割してから再実行してください。")


def _clean_xlsx_all_sheets(src: Path, dst, encoding_out: str, names: list[str]) -> CleanReport:
    enc_in, _ = detect_encoding(src)
    totals = {"nfkc": 0, "wareki": 0, "stripped": 0}
    sheet_outputs = []
    first_dst = first_rows = first_cols = None
    used = set()  # Track output paths to detect collisions
    all_issues = []
    for name in names:
        df = pd.read_excel(src, sheet_name=name, dtype=str)
        _check_row_guard(df, sheet_label=name)
        cleaned, counts = _clean_dataframe(df)
        all_issues += detect_column_issues(df)
        for k in totals:
            totals[k] += counts[k]
        out_path = src.with_name(f"{src.stem}_{_safe_sheet_name(name)}_cleaned.csv")
        # Collision detection: ensure unique output path
        final = out_path
        i = 2
        while str(final) in used:
            final = out_path.with_name(f"{out_path.stem}_{i}{out_path.suffix}")
            i += 1
        used.add(str(final))
        cleaned.to_csv(final, index=False, encoding=encoding_out)
        sheet_outputs.append((name, str(final), len(df), len(df.columns)))
        if first_dst is None:
            first_dst, first_rows, first_cols = final, len(df), len(df.columns)
    rep = CleanReport(
        str(src), str(first_dst), enc_in, encoding_out,
        cells_nfkc=totals["nfkc"], cells_wareki=totals["wareki"], cells_stripped=totals["stripped"],
        n_rows=first_rows, n_cols=first_cols, sheet_outputs=sheet_outputs,
    )
    rep.column_warnings = list(dict.fromkeys(all_issues))
    if dst is not None:
        rep.notes.append(
            f"複数シートのため --out(『{dst}』) は無視し、シートごとに自動命名で出力しました。")
    return rep


def _clean_to_xlsx(src: Path, dst, sheet: str | None) -> CleanReport:
    src = Path(src)
    is_xlsx = src.suffix.lower() in (".xlsx", ".xlsm")
    enc_in, _ = detect_encoding(src)
    dst = Path(dst) if dst else src.with_name(f"{src.stem}_cleaned.xlsx")
    if dst.resolve() == src.resolve():
        raise ValueError("出力先が入力と同一です(原本は変更しない方針)。")
    if is_xlsx and sheet is None:
        names = _xlsx_sheet_names(src)
    elif is_xlsx:
        names = [sheet]
    else:
        names = [None]
    totals = {"nfkc": 0, "wareki": 0, "stripped": 0}
    sheet_outputs = []
    first_rows = first_cols = 0
    used_labels = set()
    all_issues = []
    with pd.ExcelWriter(dst, engine="openpyxl") as writer:
        for name in names:
            df, _, _ = _read(src, sheet=name)
            _check_row_guard(df, sheet_label=name or "")
            cleaned, counts = _clean_dataframe(df)
            all_issues += detect_column_issues(df)
            for k in totals:
                totals[k] += counts[k]
            label = _safe_sheet_name(name)[:31] if name else "Sheet1"
            base = label
            i = 2
            while label in used_labels:
                label = f"{base[:28]}_{i}"
                i += 1
            used_labels.add(label)
            cleaned.to_excel(writer, sheet_name=label, index=False)
            sheet_outputs.append((name or "(CSV)", str(dst), len(df), len(df.columns)))
            if not first_cols:
                first_rows, first_cols = len(df), len(df.columns)
    rep = CleanReport(str(src), str(dst), enc_in, "xlsx",
                      cells_nfkc=totals["nfkc"], cells_wareki=totals["wareki"],
                      cells_stripped=totals["stripped"], n_rows=first_rows, n_cols=first_cols)
    rep.column_warnings = list(dict.fromkeys(all_issues))
    if len(sheet_outputs) > 1:
        rep.sheet_outputs = sheet_outputs
    return rep


def clean_file(src, dst=None, *, encoding_out: str = "utf-8-sig",
               sheet: str | None = None, out_format: str = "csv") -> CleanReport:
    src = Path(src)
    if out_format == "xlsx":
        return _clean_to_xlsx(src, dst, sheet)
    is_xlsx = src.suffix.lower() in (".xlsx", ".xlsm")
    if not is_xlsx and _count_lines(src, ROW_GUARD + 1) - 1 > ROW_GUARD:
        raise RowGuardError(f"行数がガード{ROW_GUARD}行を超えています。ファイルを分割してから再実行してください。")

    if is_xlsx and sheet is None:
        names = _xlsx_sheet_names(src)
        if len(names) > 1:
            return _clean_xlsx_all_sheets(src, dst, encoding_out, names)

    df, enc_in, note = _read(src, sheet=sheet)
    _check_row_guard(df)
    if dst:
        dst = Path(dst)
    elif is_xlsx and sheet is not None:
        dst = src.with_name(f"{src.stem}_{_safe_sheet_name(sheet)}_cleaned.csv")
    else:
        dst = src.with_name(f"{src.stem}_cleaned.csv")
    if dst.resolve() == src.resolve():
        raise ValueError("出力先が入力と同一です(原本は変更しない方針)。--out で別名を指定してください。")
    rep = CleanReport(str(src), str(dst), enc_in, encoding_out,
                      n_rows=len(df), n_cols=len(df.columns))
    if note:
        rep.notes.append(note)

    cleaned, counts = _clean_dataframe(df)
    rep.cells_nfkc, rep.cells_wareki, rep.cells_stripped = counts["nfkc"], counts["wareki"], counts["stripped"]
    cleaned.to_csv(dst, index=False, encoding=encoding_out)
    rep.column_warnings = detect_column_issues(df)
    return rep


def _df_to_markdown(df: pd.DataFrame, limit: int = 200) -> str:
    d = df.reset_index()
    cols = ["/".join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in d.head(limit).iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    if len(d) > limit:
        lines.append(f"| …ほか {len(d) - limit} 行 |" + " |" * (len(cols) - 1))
    return "\n".join(lines)


def _to_numeric(series):
    return pd.to_numeric(
        series.map(lambda v: unicodedata.normalize("NFKC", v).replace(",", "")
                   if isinstance(v, str) else v),
        errors="coerce")


@dataclass
class PivotReport:
    src: str
    dst: str
    table_md: str
    n_rows: int
    n_cols: int

    def to_markdown(self) -> str:
        return (f"## ピボット集計\n- 入力: `{self.src}`\n"
                f"- 出力: `{self.dst}` ({self.n_rows}行 × {self.n_cols}列)\n\n{self.table_md}")


def pivot_report(path, index, values, *, agg: str = "sum", columns=None,
                 sheet: str | None = None, out=None) -> PivotReport:
    src = Path(path)
    df, _, _ = _read(src, sheet=sheet)
    _check_row_guard(df)
    idx = [c.strip() for c in index.split(",")]
    vals = [c.strip() for c in values.split(",")]
    cols = [c.strip() for c in columns.split(",")] if columns else None
    for c in idx + vals + (cols or []):
        if c not in df.columns:
            raise ValueError(
                f"列 '{c}' が見つかりません。利用可能: {', '.join(map(str, df.columns))}")
    work = df.copy()
    for v in vals:
        work[v] = _to_numeric(work[v])
    table = pd.pivot_table(work, index=idx, columns=cols, values=vals,
                           aggfunc=agg, margins=True, margins_name="合計")
    dst = Path(out) if out else src.with_name(f"{src.stem}_pivot.csv")
    if dst.resolve() == src.resolve():
        raise ValueError("出力先が入力と同一です(原本は変更しない方針)。")
    table.to_csv(dst, encoding="utf-8-sig")
    return PivotReport(str(src), str(dst), _df_to_markdown(table),
                       len(table), len(table.columns))


def _set_jp_font():
    from matplotlib import font_manager
    import matplotlib.pyplot as plt
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Meiryo", "Yu Gothic", "MS Gothic", "IPAexGothic", "Noto Sans CJK JP"):
        if name in available:
            plt.rcParams["font.family"] = name
            return name
    return None


# dataviz スキル準拠のカテゴリ配色(アクセシブルなプレースホルダ)
_CHART_COLORS = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2", "#edc948"]


def make_chart(path, kind: str, x: str, y: str, *, fmt: str = "png",
               title: str | None = None, sheet: str | None = None, out=None) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    src = Path(path)
    df, _, _ = _read(src, sheet=sheet)
    ys = [c.strip() for c in y.split(",")]
    for c in [x] + ys:
        if c not in df.columns:
            raise ValueError(
                f"列 '{c}' が見つかりません。利用可能: {', '.join(map(str, df.columns))}")
    _set_jp_font()
    xs = list(df[x])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if kind == "pie":
        vals = _to_numeric(df[ys[0]]).fillna(0)
        ax.pie(vals, labels=xs, colors=_CHART_COLORS, autopct="%1.1f%%")
    elif kind == "bar":
        pos = range(len(xs))
        width = 0.8 / max(len(ys), 1)
        for i, yc in enumerate(ys):
            ax.bar([p + i * width for p in pos], _to_numeric(df[yc]).fillna(0),
                   width=width, label=yc, color=_CHART_COLORS[i % len(_CHART_COLORS)])
        ax.set_xticks([p + width * (len(ys) - 1) / 2 for p in pos])
        ax.set_xticklabels(xs, rotation=0)
        if len(ys) > 1:
            ax.legend()
    else:  # line
        for i, yc in enumerate(ys):
            ax.plot(xs, _to_numeric(df[yc]).fillna(0), marker="o", label=yc,
                    color=_CHART_COLORS[i % len(_CHART_COLORS)])
        if len(ys) > 1:
            ax.legend()
    if title:
        ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    dst = Path(out) if out else src.with_name(
        f"{src.stem}_chart.{'html' if fmt == 'html' else 'png'}")
    if dst.resolve() == src.resolve():
        plt.close(fig)
        raise ValueError("出力先が入力と同一です(原本は変更しない方針)。")
    if fmt == "html":
        import io
        buf = io.StringIO()
        fig.savefig(buf, format="svg")
        plt.close(fig)
        dst.write_text(_chart_html_wrapper(title or src.stem, buf.getvalue()), encoding="utf-8")
    else:
        fig.savefig(dst, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return str(dst)


def _chart_html_wrapper(title: str, svg: str) -> str:
    return (
        "<!doctype html><html lang='ja'><head><meta charset='utf-8'>"
        f"<title>{title}</title><style>"
        "body{margin:0;padding:24px;font-family:sans-serif;background:#fff;color:#111}"
        "@media (prefers-color-scheme: dark){body{background:#111;color:#eee}"
        "svg{filter:invert(0.92) hue-rotate(180deg)}}"
        ".wrap{max-width:960px;margin:0 auto}svg{max-width:100%;height:auto}"
        f"</style></head><body><div class='wrap'><h2>{title}</h2>{svg}</div></body></html>"
    )


@dataclass
class DiffReport:
    changed: list = field(default_factory=list)      # (row_label, col, old, new)
    added_rows: list = field(default_factory=list)
    removed_rows: list = field(default_factory=list)
    added_cols: list = field(default_factory=list)
    removed_cols: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    sheet_diffs: list = field(default_factory=list)   # (sheet_name, DiffReport) — 共通シートごと
    added_sheets: list = field(default_factory=list)  # Bのみに存在するシート
    removed_sheets: list = field(default_factory=list)  # Aのみに存在するシート
    LIMIT: int = 200

    def _body_lines(self) -> list[str]:
        lines = [f"- 変更セル: {len(self.changed)}件 / 追加行: {len(self.added_rows)}件"
                 f" / 削除行: {len(self.removed_rows)}件"]
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
        return lines

    def to_markdown(self) -> str:
        if self.sheet_diffs or self.added_sheets or self.removed_sheets:
            lines = ["## 差分レポート(シート別)"]
            lines += [f"- {w}" for w in self.warnings]
            if self.added_sheets:
                lines.append(f"- B(新)のみに存在するシート: {', '.join(self.added_sheets)}")
            if self.removed_sheets:
                lines.append(f"- A(旧)のみに存在するシート: {', '.join(self.removed_sheets)}")
            for name, sub in self.sheet_diffs:
                lines.append("")
                lines.append(f"### シート: {name}")
                lines += sub._body_lines()
            return "\n".join(lines)
        lines = ["## 差分レポート"]
        lines += [f"- {w}" for w in self.warnings]
        lines += self._body_lines()
        return "\n".join(lines)


def _fill(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("")


def _compare_dfs(da: pd.DataFrame, db: pd.DataFrame, key: str | None) -> DiffReport:
    rep = DiffReport()
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


def _diff_xlsx_all_sheets(a: Path, b: Path, key: str | None) -> DiffReport:
    names_a = _xlsx_sheet_names(a)
    names_b = _xlsx_sheet_names(b)
    common = [n for n in names_a if n in names_b]
    rep = DiffReport()
    rep.added_sheets = [n for n in names_b if n not in names_a]
    rep.removed_sheets = [n for n in names_a if n not in names_b]
    for name in common:
        da = _fill(pd.read_excel(a, sheet_name=name, dtype=str))
        db = _fill(pd.read_excel(b, sheet_name=name, dtype=str))
        try:
            sub = _compare_dfs(da, db, key)
            rep.sheet_diffs.append((name, sub))
        except ValueError as e:
            rep.warnings.append(f"シート「{name}」はスキップしました: {e}")
    return rep


def diff_files(a, b, *, key: str | None = None, sheet: str | None = None) -> DiffReport:
    a, b = Path(a), Path(b)
    a_is_xlsx = a.suffix.lower() in (".xlsx", ".xlsm")
    b_is_xlsx = b.suffix.lower() in (".xlsx", ".xlsm")

    if sheet is None and a_is_xlsx and b_is_xlsx:
        return _diff_xlsx_all_sheets(a, b, key)

    da, _, note_a = _read(a, sheet=sheet)
    db, _, note_b = _read(b, sheet=sheet)
    da, db = _fill(da), _fill(db)
    rep = _compare_dfs(da, db, key)
    rep.warnings = [n for n in (note_a, note_b) if n]
    return rep


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="jp_excel.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_det = sub.add_parser("detect")
    p_det.add_argument("file")
    p_sheets = sub.add_parser("sheets")
    p_sheets.add_argument("file")
    p_cln = sub.add_parser("clean")
    p_cln.add_argument("file")
    p_cln.add_argument("--out")
    p_cln.add_argument("--encoding-out", default="utf-8-sig", choices=["utf-8-sig", "cp932"])
    p_cln.add_argument("--sheet")
    p_cln.add_argument("--format", default="csv", choices=["csv", "xlsx"], dest="out_format")
    p_dif = sub.add_parser("diff")
    p_dif.add_argument("file_a")
    p_dif.add_argument("file_b")
    p_dif.add_argument("--key")
    p_dif.add_argument("--sheet")
    p_cols = sub.add_parser("columns")
    p_cols.add_argument("file")
    p_cols.add_argument("--sheet")
    p_cols.add_argument("--format", default="md", choices=["md", "json"])
    p_piv = sub.add_parser("pivot")
    p_piv.add_argument("file")
    p_piv.add_argument("--index", required=True)
    p_piv.add_argument("--values", required=True)
    p_piv.add_argument("--agg", default="sum", choices=["sum", "count", "mean", "max", "min"])
    p_piv.add_argument("--columns")
    p_piv.add_argument("--sheet")
    p_piv.add_argument("--out")
    p_cht = sub.add_parser("chart")
    p_cht.add_argument("file")
    p_cht.add_argument("--kind", required=True, choices=["line", "bar", "pie"])
    p_cht.add_argument("--x", required=True)
    p_cht.add_argument("--y", required=True)
    p_cht.add_argument("--format", default="png", choices=["png", "html"])
    p_cht.add_argument("--title")
    p_cht.add_argument("--sheet")
    p_cht.add_argument("--out")
    args = ap.parse_args(argv[1:])
    if args.cmd == "detect":
        enc, evidence = detect_encoding(args.file)
        print(f"{enc}\t{evidence}")
    elif args.cmd == "sheets":
        names = list_sheets(args.file)
        if not names:
            print("(CSV: シートなし)")
        else:
            for n in names:
                print(n)
    elif args.cmd == "clean":
        print(clean_file(args.file, args.out, encoding_out=args.encoding_out,
                         sheet=args.sheet, out_format=args.out_format).to_markdown())
    elif args.cmd == "diff":
        print(diff_files(args.file_a, args.file_b, key=args.key, sheet=args.sheet).to_markdown())
    elif args.cmd == "columns":
        cols = column_summary(args.file, sheet=args.sheet)
        if args.format == "json":
            print(json.dumps(cols, ensure_ascii=False, indent=2))
        else:
            print(columns_to_markdown(cols))
    elif args.cmd == "pivot":
        print(pivot_report(args.file, args.index, args.values, agg=args.agg,
                           columns=args.columns, sheet=args.sheet, out=args.out).to_markdown())
    elif args.cmd == "chart":
        path = make_chart(args.file, args.kind, args.x, args.y, fmt=args.format,
                          title=args.title, sheet=args.sheet, out=args.out)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
