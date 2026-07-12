from pathlib import Path

import jp_excel


def test_column_summary_types(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("名前,金額,日付\n佐藤,100,2024-04-01\n鈴木,200,2024-05-01\n佐藤,300,2024-06-01\n",
                 encoding="utf-8")
    cols = jp_excel.column_summary(f)
    by = {c["name"]: c for c in cols}
    assert by["金額"]["type"] == "numeric"
    assert by["日付"]["type"] == "date"
    assert by["名前"]["type"] == "text"
    assert by["名前"]["n_unique"] == 2
    assert by["名前"]["non_null"] == 3
    assert len(by["名前"]["samples"]) <= 3


def test_column_summary_zenkaku_numeric(tmp_path):
    f = tmp_path / "z.csv"
    f.write_text("値\n１２３\n４５６\n", encoding="utf-8")
    by = {c["name"]: c for c in jp_excel.column_summary(f)}
    assert by["値"]["type"] == "numeric"


def test_columns_to_markdown(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("名前,金額\n佐藤,100\n", encoding="utf-8")
    md = jp_excel.columns_to_markdown(jp_excel.column_summary(f))
    assert "名前" in md and "金額" in md and "numeric" in md


def test_column_summary_xlsx_sheet(tmp_path):
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "データ"
    ws.append(["名前", "金額"]); ws.append(["佐藤", "100"])
    p = tmp_path / "b.xlsx"; wb.save(p)
    by = {c["name"]: c for c in jp_excel.column_summary(p, sheet="データ")}
    assert by["金額"]["type"] == "numeric"
