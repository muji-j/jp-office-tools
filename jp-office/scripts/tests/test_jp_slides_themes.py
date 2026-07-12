import re
import pytest
import jp_slides


def test_sixteen_themes():
    assert len(jp_slides.THEMES) == 16


def test_theme_fields_valid():
    hexre = re.compile(r"^[0-9A-Fa-f]{6}$")
    for key, t in jp_slides.THEMES.items():
        assert t.key == key
        for h in (t.bg, t.text, t.accent, t.rule):
            assert hexre.match(h), f"{key}: 不正なHEX {h}"
        if t.accent2 is not None:
            assert hexre.match(t.accent2)
        assert t.archetype in jp_slides.ARCHETYPES, f"{key}: 未知アーキタイプ {t.archetype}"
        assert t.heading_font in ("游ゴシック", "BIZ UDPGothic", "游明朝", "メイリオ")
        assert t.body_font in ("游ゴシック", "BIZ UDPGothic", "游明朝", "メイリオ")


def test_two_dark_themes():
    dark = [k for k, t in jp_slides.THEMES.items() if t.dark]
    assert set(dark) == {"墨", "藍鉄"}


def test_color_block_have_accent2():
    for key in ("朱", "彩層"):
        assert jp_slides.THEMES[key].accent2 is not None


def test_font_pairings():
    assert set(jp_slides.FONT_PAIRINGS) == {"yu-gothic", "biz-ud", "yu-mincho", "meiryo"}


def test_parse_content_minimal():
    c = jp_slides.parse_content({
        "meta": {"title": "月次報告"},
        "theme": "藍",
        "slides": [{"type": "cover", "title": "月次報告"}],
    })
    assert c["theme"] == "藍"
    assert c["slides"][0]["type"] == "cover"


def test_parse_content_rejects_unknown_theme():
    with pytest.raises(ValueError, match="テーマ"):
        jp_slides.parse_content({"theme": "存在しない", "slides": []})


def test_parse_content_rejects_unknown_slide_type():
    with pytest.raises(ValueError, match="スライド種別|type"):
        jp_slides.parse_content({"theme": "藍", "slides": [{"type": "grille"}]})


def test_themes_cli_lists_all(capsys):
    rc = jp_slides.main(["jp_slides.py", "themes"])
    out = capsys.readouterr().out
    assert rc == 0
    for key in jp_slides.THEMES:
        assert key in out
