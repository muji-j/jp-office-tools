"""jp-office: 日本ビジネス向けスライド(.pptx)生成 — テーマエンジン + ブランドテンプレート."""
from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Theme:
    key: str
    reading: str
    family: str
    bg: str
    text: str
    accent: str
    accent2: str | None
    rule: str
    heading_font: str
    body_font: str
    archetype: str
    dark: bool


ARCHETYPES = ("minimal-centered", "accent-bar", "header-band", "sidebar", "color-block")
SLIDE_TYPES = ("cover", "message", "table", "image", "section")

FONT_PAIRINGS = {
    "yu-gothic": ("游ゴシック", "游ゴシック"),
    "biz-ud": ("BIZ UDPGothic", "BIZ UDPGothic"),
    "yu-mincho": ("游明朝", "游ゴシック"),
    "meiryo": ("メイリオ", "メイリオ"),
}

# key, reading, family, bg, text, accent, accent2, rule, heading_font, body_font, archetype, dark
_THEME_ROWS = [
    ("霞", "かすみ", "ミニマル", "FAFAFA", "2B2B2B", "6B8CAE", None, "E2E2E2", "游ゴシック", "游ゴシック", "minimal-centered", False),
    ("白磁", "はくじ", "ミニマル", "FFFFFF", "111111", "888888", None, "DDDDDD", "BIZ UDPGothic", "BIZ UDPGothic", "minimal-centered", False),
    ("石板", "せきばん", "ミニマル", "F4F5F6", "33393F", "5A6B7B", None, "D3D8DC", "游ゴシック", "游ゴシック", "sidebar", False),
    ("藍", "あい", "コーポレート", "FFFFFF", "1A2A44", "2A4B8D", None, "DCE2EC", "游ゴシック", "游ゴシック", "accent-bar", False),
    ("常磐", "ときわ", "コーポレート", "FFFFFF", "14352A", "1E6E4B", None, "D6E4DC", "BIZ UDPGothic", "BIZ UDPGothic", "accent-bar", False),
    ("鉄紺", "てつこん", "コーポレート", "FFFFFF", "222222", "1B2A4A", "35507F", "D6DCE6", "游ゴシック", "游ゴシック", "header-band", False),
    ("青碧", "せいへき", "コーポレート", "FFFFFF", "123B3B", "148C8C", None, "D2E6E6", "BIZ UDPGothic", "BIZ UDPGothic", "accent-bar", False),
    ("朱", "しゅ", "モダン・ボールド", "FFFFFF", "222222", "E24A2B", "8C2A18", "F0D6CE", "游ゴシック", "游ゴシック", "color-block", False),
    ("山吹", "やまぶき", "モダン・ボールド", "FFFFFF", "2A2417", "E0A526", None, "EFE2C6", "游ゴシック", "游ゴシック", "accent-bar", False),
    ("彩層", "さいそう", "モダン・ボールド", "FFFFFF", "222222", "2D3E78", "F0A500", "DDDDDD", "BIZ UDPGothic", "BIZ UDPGothic", "color-block", False),
    ("墨", "すみ", "ダーク", "1C1C1E", "ECECEC", "38BDF8", None, "3A3A3E", "BIZ UDPGothic", "BIZ UDPGothic", "header-band", True),
    ("藍鉄", "あいてつ", "ダーク", "15213A", "E8ECF4", "6EA8FF", None, "2C3A56", "游ゴシック", "游ゴシック", "minimal-centered", True),
    ("桜", "さくら", "ソフト・ウォーム", "FFFBFB", "3A2E30", "E39AA6", None, "F0DEE2", "游ゴシック", "游ゴシック", "minimal-centered", False),
    ("亜麻", "あま", "ソフト・ウォーム", "F5F0E6", "4A423A", "C56A4A", None, "E4DAC8", "游ゴシック", "游ゴシック", "sidebar", False),
    ("藤", "ふじ", "ソフト・ウォーム", "FAF8FC", "322A3E", "8E7CC3", None, "E4DDF0", "游ゴシック", "游ゴシック", "minimal-centered", False),
    ("明朝", "みんちょう", "タイポグラフィ", "FFFFFF", "1E1E1E", "B0A0A0", None, "B0A0A0", "游明朝", "游ゴシック", "minimal-centered", False),
]
THEMES = {r[0]: Theme(*r) for r in _THEME_ROWS}


def list_themes() -> list[str]:
    lines = []
    for t in THEMES.values():
        a2 = f"/{t.accent2}" if t.accent2 else ""
        lines.append(f"{t.key}({t.reading})  [{t.family}]  accent #{t.accent}{a2}  {t.heading_font}  {t.archetype}")
    return lines


def parse_content(obj: dict) -> dict:
    """コンテンツJSONを検証・正規化。違反は ValueError(日本語)."""
    if not isinstance(obj, dict):
        raise ValueError("コンテンツはオブジェクト(dict)である必要があります。")
    theme = obj.get("theme", "藍")
    if theme not in THEMES:
        raise ValueError(f"未知のテーマです: {theme!r}(有効: {'・'.join(THEMES)})")
    pattern = obj.get("pattern", "conclusion")
    if pattern not in ("conclusion", "incident", "comparison"):
        raise ValueError(f"未知のパターンです: {pattern!r}")
    slides = obj.get("slides", [])
    if not isinstance(slides, list):
        raise ValueError("slides はリストである必要があります。")
    for i, s in enumerate(slides):
        if not isinstance(s, dict) or "type" not in s:
            raise ValueError(f"slides[{i}] に type がありません。")
        if s["type"] not in SLIDE_TYPES:
            raise ValueError(f"slides[{i}]: 未知のスライド種別(type) {s['type']!r}(有効: {'・'.join(SLIDE_TYPES)})")
    return {
        "meta": obj.get("meta", {}),
        "theme": theme,
        "pattern": pattern,
        "template": obj.get("template"),
        "accent": obj.get("accent"),
        "font": obj.get("font"),
        "variant": obj.get("variant", "light"),
        "slides": slides,
    }


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="jp-office スライド生成")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("themes")
    p_b = sub.add_parser("build")
    p_b.add_argument("content")
    p_b.add_argument("--pattern", choices=["conclusion", "incident", "comparison"])
    p_b.add_argument("--theme")
    p_b.add_argument("--template")
    p_b.add_argument("--accent")
    p_b.add_argument("--font", choices=list(FONT_PAIRINGS))
    p_b.add_argument("--variant", choices=["light", "dark"])
    p_b.add_argument("--out")
    p_g = sub.add_parser("gallery")
    p_g.add_argument("--out-dir", default="jp_slides_gallery")
    p_o = sub.add_parser("overview")
    p_o.add_argument("--out", default="jp_slides_overview.pptx")
    return ap


def main(argv: list[str]) -> int:
    try:
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = _build_argparser().parse_args(argv[1:])
    if args.cmd == "themes":
        print("\n".join(list_themes()))
        return 0
    # build/gallery/overview は後続タスクで実装
    raise NotImplementedError(f"未実装のサブコマンド: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
