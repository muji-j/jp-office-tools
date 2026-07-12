from pathlib import Path

import pandas as pd
import pytest

import jp_excel


def test_pivot_sum(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("店,金額\n東京,100\n東京,200\n大阪,50\n", encoding="utf-8")
    rep = jp_excel.pivot_report(f, index="店", values="金額", agg="sum")
    assert Path(rep.dst).exists()
    assert Path(rep.dst).name == "s_pivot.csv"
    out = pd.read_csv(rep.dst, encoding="utf-8-sig", dtype=str)
    # 東京=300, 大阪=50, 合計=350 のいずれも表に現れる
    joined = out.to_string()
    assert "300" in joined and "50" in joined and "350" in joined
    assert Path(f).read_text(encoding="utf-8").startswith("店")  # 원본 불변


def test_pivot_zenkaku_number(tmp_path):
    f = tmp_path / "z.csv"
    f.write_text("店,金額\n東京,１００\n東京,200\n", encoding="utf-8")
    rep = jp_excel.pivot_report(f, index="店", values="金額", agg="sum")
    assert "300" in rep.table_md  # 全角100が正規化され合計300


def test_pivot_missing_column(tmp_path):
    f = tmp_path / "m.csv"
    f.write_text("店,金額\n東京,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="見つかりません"):
        jp_excel.pivot_report(f, index="存在しない", values="金額")


def test_pivot_original_not_overwritten(tmp_path):
    f = tmp_path / "o.csv"
    f.write_text("店,金額\n東京,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="原本"):
        jp_excel.pivot_report(f, index="店", values="金額", out=str(f))
