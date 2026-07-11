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
    assert "150" in md and "田中" not in md.split("追加列")[0]  # 변경표에 추가행 내용이 섞이지 않음

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
