"""jp-office: 日本ビジネス向けスライド(.pptx)生成 — テーマエンジン + ブランドテンプレート."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


SLIDE_TYPES = ("cover", "message", "stats", "table", "image", "section")

FONT_PAIRINGS = {
    "yu-gothic": ("游ゴシック", "游ゴシック"),
    "biz-ud": ("BIZ UDPGothic", "BIZ UDPGothic"),
    "yu-mincho": ("游明朝", "游ゴシック"),
    "meiryo": ("メイリオ", "メイリオ"),
}

# 16テーマのモダンデザインプロファイル(SP3 承認済みプロトタイプ design_ref/sp3_themes.py
# の各テーマ関数の冒頭パレット変数から抽出)。純粋なデータ構造で python-pptx は不要。
# layout: message/stats の配置アーキタイプ、bgsig: シグネチャ背景ディスパッチキー、
# kicker: 見出し上のラベル装飾、bullet: 箇条書き装飾、card_style: カードの見た目。
THEME_PROFILE_LAYOUTS = ("list", "bento", "cards", "poster")
THEME_PROFILE_BGSIGS = (
    "airyrule", "mono", "rail", "panel", "diagonal", "band", "lines", "circle",
    "ghostnum", "colorblock", "glassdark", "horizon", "wave", "bottomband",
    "frame", "spine",
)
THEME_PROFILE_KICKERS = ("pill", "pill_outline", "underline", "plain")
THEME_PROFILE_BULLETS = ("square", "dash", "chevron", "ring", "number", "tick")
THEME_PROFILE_CARD_STYLES = ("plain", "topstrip", "leftbar", "glass", "outline", "rounded")

_THEME_PROFILE_ROWS = [
    # key, family, dark, bg, ink, accent, accent2, muted, card, rule, shadow, glow,
    # on_accent, heading_font, body_font, layout, bgsig, kicker, bullet, card_style
    ("霞", "ミニマル", False, "FAFBFC", "2B2B2B", "6B8CAE", None, "8A94A0",
     "FFFFFF", "E2E6EA", "ECECEC", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "list", "airyrule", "underline", "tick", "plain"),
    ("白磁", "ミニマル", False, "FFFFFF", "111111", "888888", None, "8A8A8A",
     "FFFFFF", "DDDDDD", "ECECEC", None, "FFFFFF", "BIZ UDPGothic", "BIZ UDPGothic",
     "poster", "mono", "pill_outline", "dash", "plain"),
    ("石板", "ミニマル", False, "F4F5F6", "33393F", "5A6B7B", None, "6E7A85",
     "FFFFFF", "D3D8DC", "E1E4E7", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "bento", "rail", "plain", "square", "plain"),
    ("藍", "コーポレート", False, "F5F7FB", "1B2A44", "2A4B8D", None, "667085",
     "FFFFFF", "DCE2EC", "DDE3EE", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "bento", "panel", "pill", "square", "plain"),
    ("常磐", "コーポレート", False, "FFFFFF", "14352A", "1E6E4B", None, "5E6E64",
     "FFFFFF", "D6E4DC", "DBEAE2", None, "FFFFFF", "BIZ UDPGothic", "BIZ UDPGothic",
     "cards", "diagonal", "pill", "chevron", "topstrip"),
    ("鉄紺", "コーポレート", False, "FFFFFF", "222222", "1B2A4A", "35507F", "5A6473",
     "F4F6FA", "D6DCE6", "E3E7EE", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "bento", "band", "pill", "square", "leftbar"),
    ("青碧", "コーポレート", False, "FFFFFF", "123B3B", "148C8C", None, "5E7373",
     "FFFFFF", "D2E6E6", "D6E6E6", None, "FFFFFF", "BIZ UDPGothic", "BIZ UDPGothic",
     "cards", "lines", "pill", "square", "leftbar"),
    ("朱", "モダン・ボールド", False, "FFFFFF", "1A1A1A", "E24A2B", "B5341C", "666666",
     "FFFFFF", "F0D6CE", "FCE9E4", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "poster", "circle", "pill", "chevron", "plain"),
    ("山吹", "モダン・ボールド", False, "FFFDF7", "2A2417", "D99A1C", None, "8A8168",
     "FFFFFF", "EFE2C6", "EEE3C9", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "cards", "ghostnum", "pill", "number", "plain"),
    ("彩層", "モダン・ボールド", False, "FFFFFF", "222222", "2D3E78", "F0A500", "6A6A6A",
     "FFFFFF", "DDDDDD", "E5E5EA", None, "FFFFFF", "BIZ UDPGothic", "BIZ UDPGothic",
     "cards", "colorblock", "pill", "square", "plain"),
    ("墨", "ダーク", True, "111318", "F2F5F9", "45D0C5", None, "8A93A3",
     "1B1E26", "262A34", "0B0D11", "45D0C5", "0B1418", "BIZ UDPGothic", "BIZ UDPGothic",
     "bento", "glassdark", "pill_outline", "square", "glass"),
    ("藍鉄", "ダーク", True, "0F1626", "EAF0FC", "7FB2FF", None, "93A0BC",
     "16223A", "1B2740", "080D18", "7FB2FF", "0B1420", "游ゴシック", "游ゴシック",
     "bento", "horizon", "pill_outline", "ring", "glass"),
    ("桜", "ソフト・ウォーム", False, "FFF8FA", "3A2E33", "E39AA6", "6B4A52", "8A7B80",
     "FFFFFF", "F0DEE2", "F1DCE2", None, "FFFFFF", "游ゴシック", "游ゴシック",
     "cards", "wave", "pill", "ring", "topstrip"),
    ("亜麻", "ソフト・ウォーム", False, "F5F0E6", "4A423A", "C56A4A", None, "8A7E6E",
     "FFFDFA", "F3E4D8", "E4DAC8", None, "FFF6EE", "游ゴシック", "游ゴシック",
     "cards", "bottomband", "pill", "ring", "rounded"),
    ("藤", "ソフト・ウォーム", False, "FAF8FC", "322A3E", "8E7CC3", None, "7A7186",
     "FFFFFF", "BCA9DB", "F1EDF7", None, "FFFFFF", "游明朝", "游ゴシック",
     "list", "frame", "plain", "tick", "plain"),
    ("明朝", "タイポグラフィ", False, "FFFFFF", "1E1E1E", "B0A0A0", None, "6B6B6B",
     "FFFFFF", "B0A0A0", "E5E0E0", None, "FFFFFF", "游明朝", "游ゴシック",
     "list", "spine", "plain", "tick", "plain"),
]

_THEME_PROFILE_KEYS = (
    "key", "family", "dark", "bg", "ink", "accent", "accent2", "muted",
    "card", "rule", "shadow", "glow", "on_accent", "heading_font", "body_font",
    "layout", "bgsig", "kicker", "bullet", "card_style",
)

THEME_PROFILES: dict[str, dict] = {
    row[0]: dict(zip(_THEME_PROFILE_KEYS, row)) for row in _THEME_PROFILE_ROWS
}


def list_theme_profiles() -> list[str]:
    """16プロファイルを `key(family) layout/bgsig` 形式で一覧化する。"""
    lines = []
    for key, prof in THEME_PROFILES.items():
        lines.append(f"{key}({prof['family']})  {prof['layout']}/{prof['bgsig']}"
                      f"  kicker={prof['kicker']} bullet={prof['bullet']} card={prof['card_style']}")
    return lines


def parse_content(obj: dict) -> dict:
    """コンテンツJSONを検証・正規化。違反は ValueError(日本語)."""
    if not isinstance(obj, dict):
        raise ValueError("コンテンツはオブジェクト(dict)である必要があります。")
    theme = obj.get("theme", "藍")
    if theme not in THEME_PROFILES:
        raise ValueError(f"未知のテーマです: {theme!r}(有効: {'・'.join(THEME_PROFILES)})")
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
        if s["type"] == "stats":
            items = s.get("items")
            if not isinstance(items, list) or not items:
                raise ValueError(f"slides[{i}]: stats には items(リスト)が必要です。")
            for j, it in enumerate(items):
                if not isinstance(it, dict):
                    raise ValueError(f"slides[{i}].items[{j}] はオブジェクト(dict)である必要があります。")
                if "value" not in it or "label" not in it:
                    raise ValueError(f"slides[{i}].items[{j}] には value と label が必要です。")
        elif s["type"] == "message":
            body = s.get("body")
            if body is not None:
                if isinstance(body, str):
                    # 単一項目の便宜coercing(文字列を1文字ずつ箇条書きに分解する事故を防ぐ)。
                    s["body"] = [body]
                elif not isinstance(body, list):
                    raise ValueError(f"slides[{i}]: message の body はリストである必要があります(文字列は単一項目として許容)。")
        elif s["type"] == "table":
            columns = s.get("columns")
            if columns is not None and not isinstance(columns, list):
                raise ValueError(f"slides[{i}]: table の columns はリストである必要があります。")
            rows = s.get("rows")
            if rows is not None:
                if not isinstance(rows, list):
                    raise ValueError(f"slides[{i}]: table の rows はリストである必要があります。")
                for j, row in enumerate(rows):
                    if row is not None and not isinstance(row, list):
                        raise ValueError(f"slides[{i}].rows[{j}] はリスト(または null)である必要があります。")
    return {
        "meta": obj.get("meta", {}),
        "theme": theme,
        "pattern": pattern,
        "template": obj.get("template"),
        "accent": obj.get("accent"),
        "font": obj.get("font"),
        "variant": obj.get("variant"),
        "slides": slides,
    }


def _require_pptx():
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt, Emu
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.oxml.ns import qn
        return dict(Presentation=Presentation, Inches=Inches, Pt=Pt, Emu=Emu,
                    RGBColor=RGBColor, PP_ALIGN=PP_ALIGN, MSO_ANCHOR=MSO_ANCHOR,
                    MSO_SHAPE=MSO_SHAPE, qn=qn)
    except ImportError as e:
        raise RuntimeError(
            "python-pptx が見つかりません。`/jp-office-setup` で導入するか "
            "`pip install python-pptx>=1.0` を実行してください。"
        ) from e


def render_deck(content: dict, *, out: str | None = None) -> str:
    """コンテンツJSONを新エンジン(jp_slides_design)でレンダーし、保存先パスを返す。"""
    P = _require_pptx()
    import jp_slides_design as D

    prof = _resolve_profile(content)
    template = content.get("template")
    tmode = bool(template)
    if tmode:
        if not Path(template).exists():
            raise RuntimeError(f"テンプレートが見つかりません: {template}")
        prs = P["Presentation"](template)
    else:
        prs = D.new_prs()

    dispatch = {
        "cover": lambda s: D.render_cover(prs, prof, s, template_mode=tmode),
        "message": lambda s: D.render_message(prs, prof, s.get("headline", ""), s.get("body"),
                                               template_mode=tmode),
        "stats": lambda s: D.render_stats(prs, prof, s.get("headline", ""), s.get("items"),
                                           template_mode=tmode),
        "table": lambda s: D.render_table(prs, prof, s.get("headline", ""),
                                           s.get("columns") or [], s.get("rows") or [],
                                           template_mode=tmode),
        "image": lambda s: D.render_image(prs, prof, s.get("headline", ""), s.get("image"),
                                           s.get("caption"), template_mode=tmode),
        "section": lambda s: D.render_section(prs, prof, s.get("number", ""), s.get("title", ""),
                                               template_mode=tmode),
    }
    for s in content["slides"]:
        fn = dispatch.get(s["type"])
        if fn is None:
            raise RuntimeError(f"未対応のスライド種別です: {s['type']}")
        fn(s)
    title = content.get("meta", {}).get("title") or "slides"
    path = out or f"{title}.pptx"
    prs.save(path)
    return path


def _resolve_profile(content: dict) -> dict:
    """テーマプロファイル + オーバーライド(accent/font/variant)を適用した dict を返す。

    variant のライト/ダーク切替は bg/ink/rule をコヒーレントにリマップする
    (背景色だけでなく文字・罫線色も一貫させ、旧 _resolve_theme のロジックを
    プロファイル(dict)向けに移植したもの)。
    """
    prof = dict(THEME_PROFILES[content["theme"]])
    if content.get("accent"):
        prof["accent"] = str(content["accent"]).lstrip("#").upper()
    if content.get("font") and content["font"] in FONT_PAIRINGS:
        h, b = FONT_PAIRINGS[content["font"]]
        prof["heading_font"] = h
        prof["body_font"] = b
    variant = content.get("variant")
    if variant == "dark" and not prof["dark"]:
        prof.update(dark=True, bg="1C1C1E", ink="ECECEC", rule="3A3A3E")
    elif variant == "light" and prof["dark"]:
        prof.update(dark=False, bg="FFFFFF", ink="1E1E1E", rule="DDDDDD")
    return prof


_SAMPLE_CONTENT = {
    "meta": {"title": "月次営業報告(サンプル)", "date": "2026年7月", "author": "山田太郎"},
    "slides": [
        {"type": "cover", "title": "月次営業報告", "subtitle": "株式会社サンプル 2026年6月度",
         "date": "2026年7月13日", "author": "企画部 山田太郎"},
        {"type": "message", "headline": "6月の売上は前月比12%増加した",
         "body": ["新規契約が8件成立", "解約はゼロ", "主力商品Aが牽引"]},
        {"type": "stats", "headline": "主要指標の伸び", "items": [
            {"value": "182億", "label": "エネルギー事業", "note": "+18%"},
            {"value": "24億", "label": "SaaS事業", "note": "黒字化"},
            {"value": "97億", "label": "海外事業", "note": "+4%"},
        ]},
        {"type": "table", "headline": "案の比較", "columns": ["評価軸", "A案", "B案"],
         "rows": [["コスト", "低", "高"], ["納期", "3週間", "5週間"], ["実績", "多数", "少数"]]},
        {"type": "section", "title": "次期の重点施策", "number": "02"},
    ],
}


def build_gallery(out_dir: str) -> list[str]:
    """全16テーマを同一サンプルコンテンツでレンダーし、overview.pptx も添える。生成パス一覧を返す。"""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    made = []
    for key in THEME_PROFILES:
        obj = dict(_SAMPLE_CONTENT)
        obj["theme"] = key
        content = parse_content(obj)
        made.append(render_deck(content, out=str(d / f"{key}.pptx")))
    made.append(build_overview(str(d / "overview.pptx")))
    return made


def build_overview(out: str) -> str:
    """単一スライドに全16テーマのカード(bg・accentスウォッチ・family/layout/bgsig)を並べて保存。"""
    _require_pptx()
    import jp_slides_design as D

    prs = D.new_prs()
    s = D.slide(prs, "FFFFFF")
    keys = list(THEME_PROFILES)
    cols = 4
    cw, ch = 3.0, 1.6
    x0, y0, gx, gy = 0.35, 0.35, 0.18, 0.14
    for i, key in enumerate(keys):
        prof = THEME_PROFILES[key]
        r, c = divmod(i, cols)
        left = x0 + c * (cw + gx)
        top = y0 + r * (ch + gy)
        D.rect(s, left, top, cw, ch, fill=prof["bg"], line=prof["rule"], lw=0.75)
        D.rect(s, left + 0.12, top + 0.12, 0.5, 0.5, fill=prof["accent"])
        if prof.get("accent2"):
            D.rect(s, left + 0.66, top + 0.12, 0.28, 0.5, fill=prof["accent2"])
        D.text(s, left + 0.12, top + 0.68, cw - 0.24, 0.4,
               [[D.R(key, prof["heading_font"], 15, prof["ink"], True)]])
        D.text(s, left + 0.12, top + 1.06, cw - 0.24, 0.48,
               [[D.R(f"{prof['family']} / {prof['layout']}・{prof['bgsig']}",
                     prof["body_font"], 8.5, prof["ink"])]])
    prs.save(out)
    return out


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
        print("\n".join(list_theme_profiles()))
        return 0
    if args.cmd == "build":
        obj = json.loads(Path(args.content).read_text(encoding="utf-8"))
        for k in ("pattern", "theme", "template", "accent", "font", "variant"):
            v = getattr(args, k, None)
            if v is not None:
                obj[k] = v
        content = parse_content(obj)
        print(render_deck(content, out=args.out))
        return 0
    if args.cmd == "gallery":
        paths = build_gallery(args.out_dir)
        print(f"{len(paths)} ファイルを生成: {args.out_dir}")
        return 0
    if args.cmd == "overview":
        print(build_overview(args.out))
        return 0
    raise NotImplementedError(f"未実装のサブコマンド: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
