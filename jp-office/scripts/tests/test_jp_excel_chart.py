from pathlib import Path

import pytest

import jp_excel


def _csv(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("月,売上\n1月,100\n2月,150\n3月,120\n", encoding="utf-8")
    return f


def test_chart_png(tmp_path):
    f = _csv(tmp_path)
    out = jp_excel.make_chart(f, kind="line", x="月", y="売上", fmt="png")
    p = Path(out)
    assert p.exists() and p.suffix == ".png" and p.stat().st_size > 0


def test_chart_bar_html(tmp_path):
    f = _csv(tmp_path)
    out = jp_excel.make_chart(f, kind="bar", x="月", y="売上", fmt="html")
    p = Path(out)
    assert p.exists() and p.suffix == ".html"
    text = p.read_text(encoding="utf-8")
    assert "<svg" in text.lower() and "prefers-color-scheme" in text


def test_chart_pie(tmp_path):
    f = _csv(tmp_path)
    out = jp_excel.make_chart(f, kind="pie", x="月", y="売上", fmt="png")
    assert Path(out).exists()


def test_chart_missing_column(tmp_path):
    f = _csv(tmp_path)
    with pytest.raises(ValueError, match="見つかりません"):
        jp_excel.make_chart(f, kind="line", x="無い", y="売上")


def test_chart_original_not_overwritten(tmp_path):
    f = _csv(tmp_path)
    before = f.read_bytes()
    jp_excel.make_chart(f, kind="line", x="月", y="売上", fmt="png")
    assert f.read_bytes() == before
