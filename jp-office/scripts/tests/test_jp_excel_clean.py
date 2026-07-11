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
    assert evidence  # 판별 근거 문자열이 비어있지 않음

def test_detect_utf8_bom(tmp_path):
    f = tmp_path / "a.csv"
    f.write_bytes("列,値\nあ,1\n".encode("utf-8-sig"))
    assert jp_excel.detect_encoding(f)[0] == "utf-8-sig"

def test_clean_writes_copy_not_original(tmp_path):
    f = _write_cp932(tmp_path)
    before = f.read_bytes()
    report = jp_excel.clean_file(f)
    assert f.read_bytes() == before               # 원본 불변
    assert Path(report.dst).name == "sales_cleaned.csv"
    assert Path(report.dst).exists()

def test_clean_normalizes(tmp_path):
    f = _write_cp932(tmp_path)
    report = jp_excel.clean_file(f)
    df = pd.read_csv(report.dst, dtype=str)
    assert df.loc[0, "数量"] == "123"             # 全角숫자 → 반각 (NFKC)
    assert df.loc[0, "日付"] == "2024-04-01"      # 和暦 → ISO
    assert df.loc[1, "日付"] == "2024-05-10"      # 약기 和暦 → ISO
    assert df.loc[0, "備考"] == "余白あり"          # 전후 공백 제거
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
