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
