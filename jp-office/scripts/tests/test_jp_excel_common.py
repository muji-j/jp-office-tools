"""jp_excel: 共有モジュール(jp_office_common)利用の回帰 + .xls 形式ガード。"""
from pathlib import Path

import pandas as pd
import pytest

import jp_excel
from jp_office_common import UnsupportedFormatError

# OLE2(旧 .xls バイナリ形式)の先頭マジックナンバー。
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def _write_xlsx(path, rows):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    wb.save(path)


def test_detect_encoding_euc_jp_reexported(tmp_path):
    f = tmp_path / "e.csv"
    f.write_bytes("日本語のテスト".encode("euc_jp"))
    enc, evidence = jp_excel.detect_encoding(f)
    assert enc == "euc_jp"
    assert evidence


def test_clean_file_euc_jp_csv_no_crash(tmp_path):
    """H2 回帰: euc_jp CSV を clean_file がクラッシュせず処理できる。"""
    f = tmp_path / "euc.csv"
    f.write_bytes("列,値\nあ,1\n".encode("euc_jp"))
    report = jp_excel.clean_file(f)
    assert Path(report.dst).exists()
    df = pd.read_csv(report.dst, dtype=str)
    assert df.loc[0, "値"] == "1"


def test_clean_file_rejects_xls_binary(tmp_path):
    """M5: 旧 .xls(OLE2 マジック)は UnsupportedFormatError で弾かれる。"""
    f = tmp_path / "old.xls"
    f.write_bytes(_OLE2_MAGIC + b"\x00" * 32)
    with pytest.raises(UnsupportedFormatError):
        jp_excel.clean_file(f)


def test_column_summary_rejects_xls_binary(tmp_path):
    f = tmp_path / "old.xls"
    f.write_bytes(_OLE2_MAGIC + b"\x00" * 32)
    with pytest.raises(UnsupportedFormatError):
        jp_excel.column_summary(f)


def test_diff_files_rejects_xls_binary(tmp_path):
    a = tmp_path / "old.xls"
    a.write_bytes(_OLE2_MAGIC + b"\x00" * 32)
    b = tmp_path / "new.csv"
    b.write_text("列\n1\n", encoding="utf-8")
    with pytest.raises(UnsupportedFormatError):
        jp_excel.diff_files(a, b)


def test_row_guard_error_is_jp_office_error():
    """RowGuardError は JpOfficeError 系統(T5 の run_cli ガード対象)。"""
    from jp_office_common import JpOfficeError
    assert issubclass(jp_excel.RowGuardError, JpOfficeError)


def test_normal_csv_still_processed(tmp_path):
    """回帰: 通常の csv は引き続き正常処理される。"""
    f = tmp_path / "ok.csv"
    f.write_text("列,値\nあ,1\n", encoding="utf-8")
    report = jp_excel.clean_file(f)
    assert Path(report.dst).exists()


def test_normal_xlsx_still_processed(tmp_path):
    """回帰: 通常の xlsx は引き続き正常処理される。"""
    f = tmp_path / "ok.xlsx"
    _write_xlsx(f, [["a", "b"], ["1", "2"]])
    report = jp_excel.clean_file(f)
    assert Path(report.dst).exists()


def test_list_sheets_uses_shared_is_xlsx(tmp_path):
    f = tmp_path / "ok.xlsx"
    _write_xlsx(f, [["a"], ["1"]])
    names = jp_excel.list_sheets(f)
    assert names == ["Sheet"]


def test_list_sheets_rejects_xls_binary(tmp_path):
    """SP5 Fix 4: sheets サブコマンド経路も旧 .xls を UnsupportedFormatError で弾く
    (修正前は _check_supported_format を通らず '(CSV: シートなし)' に誤分類していた)。"""
    f = tmp_path / "old.xls"
    f.write_bytes(_OLE2_MAGIC + b"\x00" * 32)
    with pytest.raises(UnsupportedFormatError):
        jp_excel.list_sheets(f)


def test_make_chart_matplotlib_missing_raises_jp_office_error(tmp_path, monkeypatch):
    """SP5 Fix 3: matplotlib 未インストール時は生の ImportError ではなく
    JpOfficeError(親切な日本語メッセージ)に変換される。"""
    from jp_office_common import JpOfficeError

    f = tmp_path / "d.csv"
    f.write_text("月,売上\n1月,100\n", encoding="utf-8")

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise ImportError("No module named 'matplotlib'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    with pytest.raises(JpOfficeError, match="matplotlib"):
        jp_excel.make_chart(f, kind="line", x="月", y="売上")


def test_clean_file_corrupted_xlsx_clean_error(tmp_path, capsys):
    """SP5 Fix 2 回帰: 壊れた(truncated zip)偽 .xlsx は run_cli 経由でトレースバックなし rc1。"""
    from jp_office_common import run_cli

    f = tmp_path / "broken.xlsx"
    f.write_bytes(b"PK\x03\x04not a real zip")
    rc = run_cli(jp_excel.main, ["jp_excel.py", "columns", str(f)])
    err = capsys.readouterr().err
    assert rc == 1
    assert err.strip() != ""
    assert "Traceback" not in err
