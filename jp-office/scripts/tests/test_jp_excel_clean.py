from pathlib import Path

import pandas as pd
import pytest

import jp_excel


def _write_cp932(p: Path) -> Path:
    f = p / "sales.csv"
    text = "商品名,数量,日付,備考\nりんご,１２３,令和6年4月1日, 余白あり \nみかん,45,R6.5.10,ﾊﾝｶｸｶﾅ\n"
    f.write_bytes(text.encode("cp932"))
    return f

def test_detect_cp932(tmp_path):
    f = _write_cp932(tmp_path)
    enc, evidence = jp_excel.detect_encoding(f)
    assert enc == "cp932"
    assert evidence  # 判定根拠の文字列が空でない

def test_detect_utf8_bom(tmp_path):
    f = tmp_path / "a.csv"
    f.write_bytes("列,値\nあ,1\n".encode("utf-8-sig"))
    assert jp_excel.detect_encoding(f)[0] == "utf-8-sig"

def test_clean_writes_copy_not_original(tmp_path):
    f = _write_cp932(tmp_path)
    before = f.read_bytes()
    report = jp_excel.clean_file(f)
    assert f.read_bytes() == before               # 原本は不変
    assert Path(report.dst).name == "sales_cleaned.csv"
    assert Path(report.dst).exists()

def test_clean_normalizes(tmp_path):
    f = _write_cp932(tmp_path)
    report = jp_excel.clean_file(f)
    df = pd.read_csv(report.dst, dtype=str)
    assert df.loc[0, "数量"] == "123"             # 全角数字 → 半角 (NFKC)
    assert df.loc[0, "日付"] == "2024-04-01"      # 和暦 → ISO
    assert df.loc[1, "日付"] == "2024-05-10"      # 略記 和暦 → ISO
    assert df.loc[0, "備考"] == "余白あり"          # 前後の空白除去
    assert df.loc[1, "備考"] == "ハンカクカナ"       # 半角カナ → 全角 (NFKC)
    assert report.cells_nfkc >= 2 and report.cells_wareki == 2 and report.cells_stripped >= 1

def test_clean_output_encoding_default_bom(tmp_path):
    f = _write_cp932(tmp_path)
    report = jp_excel.clean_file(f)
    assert Path(report.dst).read_bytes().startswith(b"\xef\xbb\xbf")  # utf-8-sig

def test_row_guard(tmp_path):
    f = tmp_path / "big.csv"
    with f.open("w", encoding="utf-8") as fh:
        fh.write("c\n")
        for _ in range(jp_excel.ROW_GUARD + 1):
            fh.write("1\n")
    with pytest.raises(jp_excel.RowGuardError):
        jp_excel.clean_file(f)

def test_report_markdown(tmp_path):
    f = _write_cp932(tmp_path)
    md = jp_excel.clean_file(f).to_markdown()
    assert "cp932" in md and "utf-8-sig" in md

def test_clean_wareki_substring_preserved(tmp_path):
    f = tmp_path / "memo.csv"
    f.write_text("備考\n納期: R6.5.10 予定\n", encoding="utf-8")
    report = jp_excel.clean_file(f)
    df = pd.read_csv(report.dst, dtype=str)
    assert df.loc[0, "備考"] == "納期: R6.5.10 予定"

def test_clean_undecodable_fallback(tmp_path):
    f = tmp_path / "broken.csv"
    f.write_bytes(b"col\n\x81\x39\xfe\xff abc\n")
    report = jp_excel.clean_file(f)
    assert Path(report.dst).exists()


def _write_xlsx(path, sheets: dict):
    from openpyxl import Workbook
    wb = Workbook()
    first = True
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet()
        if first:
            ws.title = name
            first = False
        else:
            ws.title = name
        for r in rows:
            ws.append(r)
    wb.save(path)

def test_detect_xlsx_is_honest(tmp_path):
    p = tmp_path / "book.xlsx"
    _write_xlsx(p, {"Sheet1": [["a", "b"], ["1", "2"]]})
    enc, evidence = jp_excel.detect_encoding(p)
    assert enc == "xlsx"
    assert "デコード失敗" not in evidence

def test_clean_xlsx_multisheet_all_processed(tmp_path):
    p = tmp_path / "multi.xlsx"
    _write_xlsx(p, {"Yosan": [["col"], ["１"]], "Jisseki": [["col"], ["２"]]})
    report = jp_excel.clean_file(p)
    names = {s[0] for s in report.sheet_outputs}
    assert names == {"Yosan", "Jisseki"}
    for name, path, *_ in report.sheet_outputs:
        df = pd.read_csv(path, dtype=str)
        assert df.loc[0, "col"] in ("1", "2")  # 全角→半角 正規化を確認

def test_clean_xlsx_singlesheet_no_warn(tmp_path):
    p = tmp_path / "single.xlsx"
    _write_xlsx(p, {"Only": [["col"], ["1"]]})
    report = jp_excel.clean_file(p)
    md = report.to_markdown()
    assert "複数シート" not in md
    assert report.sheet_outputs == []

def test_list_sheets_xlsx_multi(tmp_path):
    p = tmp_path / "multi.xlsx"
    _write_xlsx(p, {"Yosan": [["col"], ["1"]], "Jisseki": [["col"], ["2"]]})
    assert jp_excel.list_sheets(p) == ["Yosan", "Jisseki"]

def test_list_sheets_csv_empty(tmp_path):
    f = _write_cp932(tmp_path)
    assert jp_excel.list_sheets(f) == []

def test_sheets_cli_lists_xlsx_names(tmp_path, capsys):
    p = tmp_path / "multi.xlsx"
    _write_xlsx(p, {"Yosan": [["col"], ["1"]], "Jisseki": [["col"], ["2"]]})
    rc = jp_excel.main(["jp_excel.py", "sheets", str(p)])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.splitlines() == ["Yosan", "Jisseki"]

def test_sheets_cli_csv_says_no_sheets(tmp_path, capsys):
    f = _write_cp932(tmp_path)
    rc = jp_excel.main(["jp_excel.py", "sheets", str(f)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "CSV" in out and "シートなし" in out

def test_clean_sheet_specific(tmp_path):
    p = tmp_path / "multi.xlsx"
    _write_xlsx(p, {"Yosan": [["col"], ["１"]], "Jisseki": [["col"], ["２"]]})
    report = jp_excel.clean_file(p, sheet="Jisseki")
    assert Path(report.dst).name == "multi_Jisseki_cleaned.csv"
    assert report.sheet_outputs == []
    df = pd.read_csv(report.dst, dtype=str)
    assert df.loc[0, "col"] == "2"

def test_clean_sheet_name_safe_filename(tmp_path):
    p = tmp_path / "multi2.xlsx"
    _write_xlsx(p, {"A|B": [["col"], ["1"]], 'C"D': [["col"], ["2"]]})
    report = jp_excel.clean_file(p)
    by_name = {name: Path(path).name for name, path, *_ in report.sheet_outputs}
    assert by_name["A|B"] == "multi2_A_B_cleaned.csv"
    assert by_name['C"D'] == "multi2_C_D_cleaned.csv"

def test_clean_sheet_name_collision_no_data_loss(tmp_path):
    p = tmp_path / "coll.xlsx"
    _write_xlsx(p, {"A_B": [["col"], ["1"]], "A|B": [["col"], ["2"]]})
    report = jp_excel.clean_file(p)
    paths = [s[1] for s in report.sheet_outputs]
    assert len(set(paths)) == 2  # 二つのシートがそれぞれ別ファイルに
    vals = set()
    for _, path, *_ in report.sheet_outputs:
        vals.add(pd.read_csv(path, dtype=str).loc[0, "col"])
    assert vals == {"1", "2"}  # 二つのシートのデータがどちらも保持される


def test_clean_format_xlsx_from_csv(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("列\n１２３\n", encoding="utf-8")
    rep = jp_excel.clean_file(f, out_format="xlsx")
    import pandas as pd
    assert Path(rep.dst).suffix == ".xlsx" and Path(rep.dst).exists()
    df = pd.read_excel(rep.dst, dtype=str)
    assert df.loc[0, "列"] == "123"  # NFKC 正規化


def test_clean_format_xlsx_multisheet(tmp_path):
    p = tmp_path / "multi.xlsx"
    _write_xlsx(p, {"Yosan": [["col"], ["１"]], "Jisseki": [["col"], ["２"]]})
    rep = jp_excel.clean_file(p, out_format="xlsx")
    import pandas as pd
    xls = pd.ExcelFile(rep.dst)
    assert set(xls.sheet_names) >= {"Yosan", "Jisseki"}
    d1 = pd.read_excel(rep.dst, sheet_name="Yosan", dtype=str)
    assert d1.loc[0, "col"] == "1"  # 全角→半角


def test_clean_format_csv_still_default(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("列\n１２３\n", encoding="utf-8")
    rep = jp_excel.clean_file(f)  # デフォルト csv
    assert Path(rep.dst).suffix == ".csv"


def test_detect_postal_leading_zero(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("氏名,郵便番号\n佐藤,1000001\n鈴木,600001\n", encoding="utf-8")
    rep = jp_excel.clean_file(f)
    md = rep.to_markdown()
    assert "郵便番号" in md and "先頭0" in md


def test_detect_no_false_positive(tmp_path):
    f = tmp_path / "n.csv"
    f.write_text("氏名,金額\n佐藤,100\n鈴木,200\n", encoding="utf-8")
    rep = jp_excel.clean_file(f)
    assert rep.column_warnings == []


def test_phone_zenkaku_zero_no_false_positive(tmp_path):
    f = tmp_path / "ph.csv"
    f.write_text("氏名,電話\n佐藤,０９０１２３４５６７８\n", encoding="utf-8")
    rep = jp_excel.clean_file(f)
    assert not any(("電話" in w and "先頭0" in w) for w in rep.column_warnings)


def test_clean_xlsx_multisheet_csv_warnings(tmp_path):
    p = tmp_path / "m.xlsx"
    _write_xlsx(p, {"S1": [["氏名", "郵便番号"], ["佐藤", "600001"]], "S2": [["col"], ["x"]]})
    rep = jp_excel.clean_file(p)  # デフォルト csv、複数シート → _clean_xlsx_all_sheets 経路
    assert any("郵便番号" in w for w in rep.column_warnings)
