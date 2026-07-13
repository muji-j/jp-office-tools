"""T5 L2: render_message/render_table の str 入力に対する低水準防御。

body(render_message)や columns/rows(render_table)に文字列を渡した際、Python の
`for c in "文字列"` が文字単位に分解してしまう事故(意図しない箇条書き複数生成・
列の文字分解)を防ぐ isinstance ガードの回帰テスト。
"""
import pytest

pytest.importorskip("pptx")

import jp_slides
import jp_slides_design as D

_PROF = jp_slides.THEME_PROFILES["藍"]


def _texts(slide):
    return [shp.text_frame.text for shp in slide.shapes if shp.has_text_frame and shp.text_frame.text]


def test_render_message_str_body_not_split_into_chars():
    prs = D.new_prs()
    slide = D.render_message(prs, _PROF, "見出し", "一文")
    texts = _texts(slide)
    # 全文が1つのテキストボックスにまとまっており、文字単位(「一」「文」)には分解されない
    assert "一文" in texts
    assert "一" not in texts
    assert "文" not in texts


def test_render_message_list_body_still_works():
    # 回帰: list の body は従来どおり複数の箇条書きになる
    prs = D.new_prs()
    slide = D.render_message(prs, _PROF, "見出し", ["項目A", "項目B"])
    texts = _texts(slide)
    assert "項目A" in texts and "項目B" in texts


def test_render_message_none_body_still_safe():
    prs = D.new_prs()
    slide = D.render_message(prs, _PROF, "見出しのみ", None)
    assert slide is not None


def test_render_table_str_columns_and_rows_no_crash():
    prs = D.new_prs()
    slide = D.render_table(prs, _PROF, "見出し", "軸", "x")
    tables = [shp for shp in slide.shapes if shp.has_table]
    assert len(tables) == 1
    table = tables[0].table
    # columns="軸" は1列として扱われる(文字単位に分解されない)
    assert len(table.columns) == 1
    # rows="x" は文字列のため無視され、ヘッダー行のみの1行になる
    assert len(table.rows) == 1
    assert table.cell(0, 0).text_frame.text == "軸"


def test_render_table_list_columns_and_rows_still_works():
    # 回帰: list の columns/rows は従来どおり処理される
    prs = D.new_prs()
    slide = D.render_table(prs, _PROF, "見出し", ["A", "B"], [["1", "2"]])
    tables = [shp for shp in slide.shapes if shp.has_table]
    table = tables[0].table
    assert len(table.columns) == 2
    assert len(table.rows) == 2
