from pathlib import Path

import pytest

import jp_excel


def _pair(tmp_path: Path):
    a = tmp_path / "old.csv"
    b = tmp_path / "new.csv"
    a.write_text("ID,名前,金額\n1,佐藤,100\n2,鈴木,200\n3,高橋,300\n", encoding="utf-8")
    b.write_text("ID,名前,金額,部署\n1,佐藤,150\n2,鈴木,200,営業\n4,田中,400,総務\n", encoding="utf-8")
    return a, b

def test_diff_keyed(tmp_path):
    rep = jp_excel.diff_files(*_pair(tmp_path), key="ID")
    assert ("1", "金額", "100", "150") in rep.changed
    assert rep.added_rows == ["4"] and rep.removed_rows == ["3"]
    assert rep.added_cols == ["部署"] and rep.removed_cols == []

def test_diff_positional(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text("c1,c2\nx,1\ny,2\n", encoding="utf-8")
    b.write_text("c1,c2\nx,9\ny,2\nz,3\n", encoding="utf-8")
    rep = jp_excel.diff_files(a, b)
    assert ("行2", "c2", "1", "9") in rep.changed
    assert rep.added_rows == ["行4"]

def test_diff_markdown(tmp_path):
    md = jp_excel.diff_files(*_pair(tmp_path), key="ID").to_markdown()
    assert "150" in md and "田中" not in md.split("追加列")[0]  # 変更表に追加行の内容が混ざらない

def test_diff_key_duplicates_rejected(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text("ID,v\n1,a\n1,b\n", encoding="utf-8")
    b.write_text("ID,v\n1,a\n2,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="重複"):
        jp_excel.diff_files(a, b, key="ID")

def test_diff_key_blank_rejected(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text("ID,v\n1,a\n,b\n", encoding="utf-8")
    b.write_text("ID,v\n1,a\n", encoding="utf-8")
    with pytest.raises(ValueError, match="空"):
        jp_excel.diff_files(a, b, key="ID")


def _write_xlsx(path, sheets: dict):
    from openpyxl import Workbook
    wb = Workbook()
    first = True
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet()
        ws.title = name
        first = False
        for r in rows:
            ws.append(r)
    wb.save(path)


def test_diff_multisheet_common_and_unique(tmp_path):
    a = tmp_path / "a.xlsx"
    b = tmp_path / "b.xlsx"
    _write_xlsx(a, {"Yosan": [["ID", "v"], ["1", "100"]], "OnlyA": [["x"], ["1"]]})
    _write_xlsx(b, {"Yosan": [["ID", "v"], ["1", "150"]], "OnlyB": [["y"], ["2"]]})
    rep = jp_excel.diff_files(a, b)
    names = {s[0] for s in rep.sheet_diffs}
    assert names == {"Yosan"}
    yosan_sub = dict(rep.sheet_diffs)["Yosan"]
    assert ("行2", "v", "100", "150") in yosan_sub.changed
    assert rep.added_sheets == ["OnlyB"]
    assert rep.removed_sheets == ["OnlyA"]
    md = rep.to_markdown()
    assert "Yosan" in md and "OnlyA" in md and "OnlyB" in md


def test_diff_multisheet_with_key(tmp_path):
    a = tmp_path / "a.xlsx"
    b = tmp_path / "b.xlsx"
    _write_xlsx(a, {"Sheet1": [["ID", "v"], ["1", "100"], ["2", "200"]]})
    _write_xlsx(b, {"Sheet1": [["ID", "v"], ["1", "150"], ["3", "300"]]})
    rep = jp_excel.diff_files(a, b, key="ID")
    sub = dict(rep.sheet_diffs)["Sheet1"]
    assert ("1", "v", "100", "150") in sub.changed
    assert sub.added_rows == ["3"] and sub.removed_rows == ["2"]


def test_diff_sheet_isolation(tmp_path):
    a = tmp_path / "a.xlsx"
    b = tmp_path / "b.xlsx"
    # Sheet1: ID キー正常 / Notes: ID列なし(キー不可)
    _write_xlsx(a, {"Sheet1": [["ID", "値"], ["1", "a"]], "Notes": [["メモ"], ["x"]]})
    _write_xlsx(b, {"Sheet1": [["ID", "値"], ["1", "b"]], "Notes": [["メモ"], ["y"]]})
    rep = jp_excel.diff_files(a, b, key="ID")
    md = rep.to_markdown()
    assert "スキップ" in md and "Notes" in md          # 問題シートはスキップ
    assert any(name == "Sheet1" for name, _ in rep.sheet_diffs)  # 正常シートは比較される


def test_diff_single_sheet_specified(tmp_path):
    a = tmp_path / "a.xlsx"
    b = tmp_path / "b.xlsx"
    _write_xlsx(a, {"Yosan": [["col"], ["1"]], "Jisseki": [["col"], ["9"]]})
    _write_xlsx(b, {"Yosan": [["col"], ["2"]], "Jisseki": [["col"], ["9"]]})
    rep = jp_excel.diff_files(a, b, sheet="Yosan")
    assert rep.sheet_diffs == []
    assert ("行2", "col", "1", "2") in rep.changed
