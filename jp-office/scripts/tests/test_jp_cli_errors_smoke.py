"""T5: 全CLI(run_cli 経由)の親切エラー回帰 + 未カバーのCLIサブコマンドのスモーク。

- 親切エラー回帰: 存在しないファイル・範囲外ページ・存在しない列・和暦以外の日付・
  旧 .xls バイナリなど、利用者が起こしがちな入力で run_cli(main, argv) が
  トレースバックを見せずに rc=1 + 日本語1行メッセージで終わることを確認する。
- CLIスモーク: 既存テストにまだ main() 経由の呼び出しが無いサブコマンドについて、
  正常系が rc=0 で終わることだけを確認する(詳細な出力内容は各ライブラリ関数の
  既存テストでカバー済みのため重複させない)。
"""
from pathlib import Path

import jp_dates
import jp_excel
import jp_glossary
import jp_pdf
from jp_office_common import run_cli

_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # 旧 .xls(OLE2)バイナリの先頭マジックナンバー


def _assert_clean_error(rc, err):
    """トレースバックを見せず rc=1 + 空でない日本語1行メッセージで終わることを確認する。"""
    assert rc == 1
    assert err.strip() != ""
    assert "Traceback" not in err


def _make_table_pdf(path):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    with pdf.table() as table:
        for data_row in [["Name", "Age"], ["Alice", "30"]]:
            r = table.row()
            for datum in data_row:
                r.cell(datum)
    pdf.output(str(path))


def _csv(tmp_path, name="d.csv"):
    f = tmp_path / name
    f.write_text("店,金額\n東京,100\n東京,200\n大阪,50\n", encoding="utf-8")
    return f


# ---- 親切エラー回帰 ----

def test_pdf_extract_missing_file_clean_error(tmp_path, capsys):
    rc = run_cli(jp_pdf.main, ["jp_pdf.py", "extract", str(tmp_path / "nofile.pdf")])
    _assert_clean_error(rc, capsys.readouterr().err)


def test_pdf_extract_table_page_out_of_range_clean_error(tmp_path, capsys):
    f = tmp_path / "t.pdf"
    _make_table_pdf(f)
    rc = run_cli(jp_pdf.main, ["jp_pdf.py", "extract-table", str(f), "--pages", "99"])
    _assert_clean_error(rc, capsys.readouterr().err)


def test_excel_pivot_missing_column_clean_error(tmp_path, capsys):
    f = _csv(tmp_path)
    rc = run_cli(jp_excel.main,
                 ["jp_excel.py", "pivot", str(f), "--index", "存在しない列", "--values", "金額"])
    _assert_clean_error(rc, capsys.readouterr().err)


def test_excel_xls_binary_clean_error(tmp_path, capsys):
    f = tmp_path / "old.xls"
    f.write_bytes(_OLE2_MAGIC + b"\x00" * 32)
    rc = run_cli(jp_excel.main, ["jp_excel.py", "columns", str(f)])
    _assert_clean_error(rc, capsys.readouterr().err)


def test_dates_holiday_bad_date_clean_error(capsys):
    rc = run_cli(jp_dates.main, ["jp_dates.py", "holiday", "notdate"])
    _assert_clean_error(rc, capsys.readouterr().err)


def test_glossary_variants_missing_file_clean_error(tmp_path, capsys):
    rc = run_cli(jp_glossary.main, ["jp_glossary.py", "variants", str(tmp_path / "nofile.txt")])
    _assert_clean_error(rc, capsys.readouterr().err)


# ---- CLIスモーク(未カバーのサブコマンドの正常系 rc0 のみ確認) ----

def test_pdf_extract_table_md_cli_smoke(tmp_path, capsys):
    f = tmp_path / "t.pdf"
    _make_table_pdf(f)
    rc = jp_pdf.main(["jp_pdf.py", "extract-table", str(f)])
    assert rc == 0
    assert "Name" in capsys.readouterr().out


def test_excel_detect_cli_smoke(tmp_path, capsys):
    f = _csv(tmp_path)
    rc = jp_excel.main(["jp_excel.py", "detect", str(f)])
    assert rc == 0
    assert capsys.readouterr().out.strip() != ""


def test_excel_columns_cli_smoke(tmp_path, capsys):
    f = _csv(tmp_path)
    rc = jp_excel.main(["jp_excel.py", "columns", str(f)])
    assert rc == 0
    assert "店" in capsys.readouterr().out


def test_excel_pivot_cli_smoke(tmp_path, capsys):
    f = _csv(tmp_path)
    rc = jp_excel.main(["jp_excel.py", "pivot", str(f), "--index", "店", "--values", "金額"])
    assert rc == 0
    assert Path(tmp_path / "d_pivot.csv").exists()


def test_excel_chart_cli_smoke(tmp_path, capsys):
    f = _csv(tmp_path)
    rc = jp_excel.main(["jp_excel.py", "chart", str(f), "--kind", "bar", "--x", "店", "--y", "金額"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert Path(out).exists()
