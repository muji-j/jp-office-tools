import re

import pytest
import jp_slides

HEXRE = re.compile(r"^[0-9A-Fa-f]{6}$")

_REQUIRED_KEYS = (
    "key", "family", "dark", "bg", "ink", "accent", "accent2", "muted",
    "card", "rule", "shadow", "glow", "on_accent", "heading_font", "body_font",
    "layout", "bgsig", "kicker", "bullet", "card_style",
)
_FONTS = ("游ゴシック", "BIZ UDPGothic", "游明朝", "メイリオ")


def test_sixteen_profiles():
    assert len(jp_slides.THEME_PROFILES) == 16


def test_profile_required_keys_present():
    for key, prof in jp_slides.THEME_PROFILES.items():
        for k in _REQUIRED_KEYS:
            assert k in prof, f"{key}: {k} が欠けている"
        assert prof["key"] == key


def test_profile_colors_are_hex():
    for key, prof in jp_slides.THEME_PROFILES.items():
        for field in ("bg", "ink", "accent", "muted", "card", "rule", "shadow", "on_accent"):
            v = prof[field]
            assert HEXRE.match(v), f"{key}.{field}: 不正なHEX {v!r}"
        if prof["accent2"] is not None:
            assert HEXRE.match(prof["accent2"]), f"{key}.accent2: 不正なHEX"
        if prof["glow"] is not None:
            assert HEXRE.match(prof["glow"]), f"{key}.glow: 不正なHEX"


def test_profile_dark_flag_is_bool():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert isinstance(prof["dark"], bool), f"{key}: dark は bool である必要があります"


def test_profile_layout_enum():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert prof["layout"] in jp_slides.THEME_PROFILE_LAYOUTS, f"{key}: 未知の layout {prof['layout']!r}"


def test_profile_bgsig_enum():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert prof["bgsig"] in jp_slides.THEME_PROFILE_BGSIGS, f"{key}: 未知の bgsig {prof['bgsig']!r}"


def test_profile_kicker_enum():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert prof["kicker"] in jp_slides.THEME_PROFILE_KICKERS


def test_profile_bullet_enum():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert prof["bullet"] in jp_slides.THEME_PROFILE_BULLETS


def test_profile_card_style_enum():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert prof["card_style"] in jp_slides.THEME_PROFILE_CARD_STYLES


def test_profile_fonts_are_the_four_allowed():
    for key, prof in jp_slides.THEME_PROFILES.items():
        assert prof["heading_font"] in _FONTS, f"{key}: heading_font {prof['heading_font']!r}"
        assert prof["body_font"] in _FONTS, f"{key}: body_font {prof['body_font']!r}"


def test_profile_bgsig_unique_per_theme():
    # 16テーマそれぞれ異なるシグネチャ背景を持つ(デザイン上の多様性担保)。
    sigs = [prof["bgsig"] for prof in jp_slides.THEME_PROFILES.values()]
    assert len(set(sigs)) == 16


# ---- parse_content: stats タイプ ----

def test_parse_content_accepts_stats():
    c = jp_slides.parse_content({
        "meta": {"title": "t"}, "theme": "藍",
        "slides": [{"type": "stats", "headline": "指標",
                    "items": [{"value": "182億", "label": "エネルギー", "note": "+18%"}]}],
    })
    assert c["slides"][0]["type"] == "stats"
    assert c["slides"][0]["items"][0]["value"] == "182億"


def test_parse_content_rejects_stats_without_items():
    with pytest.raises(ValueError):
        jp_slides.parse_content({
            "theme": "藍", "slides": [{"type": "stats", "headline": "指標"}],
        })


def test_parse_content_rejects_stats_empty_items():
    with pytest.raises(ValueError):
        jp_slides.parse_content({
            "theme": "藍", "slides": [{"type": "stats", "headline": "指標", "items": []}],
        })


def test_parse_content_rejects_stats_item_missing_value():
    with pytest.raises(ValueError):
        jp_slides.parse_content({
            "theme": "藍",
            "slides": [{"type": "stats", "headline": "指標", "items": [{"label": "売上高"}]}],
        })


def test_parse_content_rejects_stats_item_missing_label():
    with pytest.raises(ValueError):
        jp_slides.parse_content({
            "theme": "藍",
            "slides": [{"type": "stats", "headline": "指標", "items": [{"value": "182億"}]}],
        })


def test_parse_content_rejects_stats_item_not_dict():
    with pytest.raises(ValueError):
        jp_slides.parse_content({
            "theme": "藍",
            "slides": [{"type": "stats", "headline": "指標", "items": ["182億"]}],
        })


# ---- themes CLI ----

def test_themes_cli_lists_all_profiles(capsys):
    rc = jp_slides.main(["jp_slides.py", "themes"])
    out = capsys.readouterr().out
    assert rc == 0
    for key in jp_slides.THEME_PROFILES:
        assert key in out


# ---- jp_slides_design ツールキット ----

def test_jp_slides_design_importable_and_builds_shapes():
    pytest.importorskip("pptx")
    import jp_slides_design as D

    prs = D.new_prs()
    s = D.slide(prs, "FFFFFF")
    shp = D.rect(s, 0.5, 0.5, 1.0, 1.0, fill="112233")
    assert shp is not None
    D.oval(s, 1.0, 1.0, 0.5, 0.5, fill="445566")
    D.pill(s, 0.5, 2.0, 2.0, 0.5, "テスト", "FFEEDD", "112233")
    D.text(s, 0.5, 3.0, 2.0, 0.5, [[D.R("見出し", D.GO, 18, "112233", True)]])
    D.card_plain(s, 0.5, 4.0, 2.0, 1.0, "FFFFFF", shadow="DDDDDD")
    assert len(prs.slides) == 1
    assert len(s.shapes) > 0
