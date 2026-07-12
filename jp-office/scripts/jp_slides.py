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


def _apply_font(P, run, name, size_pt, *, bold=False, color=None):
    run.font.size = P["Pt"](size_pt)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(P["qn"](tag))
        if el is None:
            el = rPr.makeelement(P["qn"](tag), {})
            rPr.append(el)
        el.set("typeface", name)


def _rgb(P, hexstr):
    return P["RGBColor"].from_string(hexstr)


def _cell_text(P, cell, text, font, size, *, bold=False, color=None):
    """セルの段落に必ず1つ run を作ってからテキストを設定する。

    `cell.text = val` は val が空文字列だと run を0個生成し、
    直後の `runs[0]` 参照で IndexError になるため使わない。
    セルは既定で空段落を1つ持つので paragraphs[0] は必ず存在し、
    add_run() は常に run を1つ保証する。
    """
    p = cell.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = str(text) if text is not None else ""
    _apply_font(P, run, font, size, bold=bold, color=color)


def _new_presentation(P, theme, template=None):
    if template:
        if not Path(template).exists():
            raise RuntimeError(f"テンプレートが見つかりません: {template}")
        prs = P["Presentation"](template)
        return prs
    prs = P["Presentation"]()
    prs.slide_width = P["Inches"](13.333)
    prs.slide_height = P["Inches"](7.5)
    return prs


def _add_slide(P, prs, theme, template_mode=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    if not template_mode:
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = _rgb(P, theme.bg)
    return slide


def _textbox(P, slide, left, top, width, height):
    tb = slide.shapes.add_textbox(P["Inches"](left), P["Inches"](top),
                                  P["Inches"](width), P["Inches"](height))
    tb.text_frame.word_wrap = True
    return tb


def _rect(P, slide, left, top, width, height, hexcolor):
    shp = slide.shapes.add_shape(P["MSO_SHAPE"].RECTANGLE, P["Inches"](left),
                                 P["Inches"](top), P["Inches"](width), P["Inches"](height))
    shp.fill.solid()
    shp.fill.fore_color.rgb = _rgb(P, hexcolor)
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


# ---- スライドビルダー ----
def _slide_cover(P, prs, theme, s, template_mode=False):
    slide = _add_slide(P, prs, theme, template_mode)
    # アーキタイプ別アクセント要素
    if not template_mode:
        _accent_decor(P, slide, theme, cover=True)
    title = s.get("title", "")
    tb = _textbox(P, slide, 0.9, 2.7, 11.5, 2.0)
    p = tb.text_frame.paragraphs[0]
    _apply_font(P, p.add_run(), theme.heading_font, 40, bold=True, color=_rgb(P, theme.accent if not theme.dark else theme.text))
    p.runs[0].text = title
    sub = s.get("subtitle")
    meta_bits = [b for b in (s.get("date"), s.get("author"), s.get("submitted_to")) if b]
    line2 = "　".join([x for x in ([sub] if sub else []) + meta_bits])
    if line2:
        tb2 = _textbox(P, slide, 0.9, 4.6, 11.5, 1.0)
        p2 = tb2.text_frame.paragraphs[0]
        _apply_font(P, p2.add_run(), theme.body_font, 16, color=_rgb(P, theme.text))
        p2.runs[0].text = line2
    return slide


def _slide_message(P, prs, theme, s, template_mode=False):
    slide = _add_slide(P, prs, theme, template_mode)
    if not template_mode:
        _accent_decor(P, slide, theme, cover=False)
    tb = _textbox(P, slide, _content_left(theme), 1.5, _content_width(theme), 1.6)
    p = tb.text_frame.paragraphs[0]
    _apply_font(P, p.add_run(), theme.heading_font, 26, bold=True, color=_rgb(P, theme.text))
    p.runs[0].text = s.get("headline", "")
    body = s.get("body", []) or []
    if body:
        tb2 = _textbox(P, slide, _content_left(theme), 3.2, _content_width(theme), 3.4)
        tf = tb2.text_frame
        for i, item in enumerate(body):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.space_after = P["Pt"](10)
            _apply_font(P, para.add_run(), theme.body_font, 18, color=_rgb(P, theme.text))
            para.runs[0].text = "・" + str(item)
    return slide


# ---- アーキタイプ配置(5種すべて) ----
def _content_left(theme):
    return 1.8 if theme.archetype == "sidebar" else 0.9


def _content_width(theme):
    return 10.6 if theme.archetype == "sidebar" else 11.5


def _on_accent_text(theme):
    """アクセント/帯の上に置く文字色。明るいテーマ=bg、ダークテーマ=text。

    Task 4 の表ヘッダー文字色でも再利用するため、シグネチャは安定させる。
    """
    return theme.text if theme.dark else theme.bg


def _band_color(theme):
    """header-band の帯色。明るいテーマ=accent、ダークテーマ=rule(控えめな対比)。"""
    return theme.accent if not theme.dark else theme.rule


def _accent_decor(P, slide, theme, *, cover):
    a = theme.archetype
    if a == "accent-bar":
        _rect(P, slide, 0.9, 1.2, 3.2, 0.13, theme.accent)  # 上部左側の短いバー
    elif a == "minimal-centered":
        _rect(P, slide, 0.9, 1.25, 11.5, 0.02, theme.rule)  # 細いルール
    elif a == "header-band":
        _rect(P, slide, 0.0, 0.0, 13.333, 1.05, _band_color(theme))
        # 帯の上に細いアクセントライン(ダークテーマの差し色)
        if theme.dark:
            _rect(P, slide, 0.0, 1.05, 13.333, 0.06, theme.accent)
    elif a == "sidebar":
        _rect(P, slide, 0.0, 0.0, 1.4, 7.5, theme.accent)
    elif a == "color-block":
        _rect(P, slide, 0.0, 0.0, 0.55, 7.5, theme.accent)
        second = theme.accent2 or theme.text
        _rect(P, slide, 0.55, 0.0, 0.22, 7.5, second)


def _warn(msg):
    print(f"⚠ {msg}", file=sys.stderr)


def _slide_table(P, prs, theme, s, template_mode=False):
    slide = _add_slide(P, prs, theme, template_mode)
    if not template_mode:
        _accent_decor(P, slide, theme, cover=False)
    tb = _textbox(P, slide, _content_left(theme), 1.4, _content_width(theme), 1.0)
    p = tb.text_frame.paragraphs[0]
    _apply_font(P, p.add_run(), theme.heading_font, 24, bold=True, color=_rgb(P, theme.text))
    p.runs[0].text = s.get("headline", "")
    cols = s.get("columns", []) or []
    rows = s.get("rows", []) or []
    if not cols:
        return slide
    nrows, ncols = len(rows) + 1, len(cols)
    gf = slide.shapes.add_table(nrows, ncols, P["Inches"](_content_left(theme)),
                                P["Inches"](2.6), P["Inches"](_content_width(theme)),
                                P["Inches"](min(0.5 * nrows, 4.4)))
    table = gf.table
    for c, name in enumerate(cols):
        cell = table.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(P, theme.accent)
        _cell_text(P, cell, name, theme.body_font, 13, bold=True, color=_rgb(P, _on_accent_text(theme)))
    for r, row in enumerate(rows, start=1):
        for c in range(ncols):
            val = row[c] if c < len(row) else ""
            cell = table.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb(P, theme.bg)
            _cell_text(P, cell, val, theme.body_font, 12, color=_rgb(P, theme.text))
    return slide


def _slide_image(P, prs, theme, s, template_mode=False):
    slide = _add_slide(P, prs, theme, template_mode)
    if not template_mode:
        _accent_decor(P, slide, theme, cover=False)
    tb = _textbox(P, slide, _content_left(theme), 1.4, _content_width(theme), 1.0)
    p = tb.text_frame.paragraphs[0]
    _apply_font(P, p.add_run(), theme.heading_font, 24, bold=True, color=_rgb(P, theme.text))
    p.runs[0].text = s.get("headline", "")
    img = s.get("image")
    img_top = 2.5
    img_bottom = img_top
    if img and Path(img).exists():
        try:
            from PIL import Image as _PILImage
            with _PILImage.open(img) as _im:
                iw, ih = _im.size
            max_w = min(_content_width(theme), 8.0)
            max_h = 4.0
            w = max_w
            h = w * (ih / iw) if iw else max_h
            if h > max_h:
                h = max_h
                w = h * (iw / ih) if ih else max_w
            slide.shapes.add_picture(img, P["Inches"](_content_left(theme)), P["Inches"](img_top),
                                     width=P["Inches"](w), height=P["Inches"](h))
            img_bottom = img_top + h
        except Exception:
            _warn(f"画像の読み込みに失敗しました(スキップ): {img}")
    elif img:
        _warn(f"画像が見つかりません(スキップ): {img}")
    cap = s.get("caption")
    if cap:
        cap_top = min(img_bottom + 0.15, 6.9)
        tb2 = _textbox(P, slide, _content_left(theme), cap_top, _content_width(theme), 0.5)
        p2 = tb2.text_frame.paragraphs[0]
        _apply_font(P, p2.add_run(), theme.body_font, 12, color=_rgb(P, theme.text))
        p2.runs[0].text = str(cap)
    return slide


def _slide_section(P, prs, theme, s, template_mode=False):
    slide = _add_slide(P, prs, theme, template_mode)
    if not template_mode:
        _accent_decor(P, slide, theme, cover=True)
    tb = _textbox(P, slide, 0.9, 3.1, 11.5, 1.4)
    p = tb.text_frame.paragraphs[0]
    _apply_font(P, p.add_run(), theme.heading_font, 30, bold=True,
                color=_rgb(P, theme.accent if not theme.dark else theme.text))
    p.runs[0].text = s.get("title", "")
    return slide


_SLIDE_DISPATCH = {"table": _slide_table, "image": _slide_image, "section": _slide_section}


def render_deck(content: dict, *, out: str | None = None) -> str:
    P = _require_pptx()
    theme = _resolve_theme(content)
    template = content.get("template")
    tmode = bool(template)
    prs = _new_presentation(P, theme, template=template)
    dispatch = {"cover": _slide_cover, "message": _slide_message, **_SLIDE_DISPATCH}
    for s in content["slides"]:
        fn = dispatch.get(s["type"])
        if fn is None:
            raise RuntimeError(f"このタスクでは未対応のスライド種別: {s['type']}")
        fn(P, prs, theme, s, template_mode=tmode)
    title = content.get("meta", {}).get("title") or "slides"
    path = out or f"{title}.pptx"
    prs.save(path)
    return path


def _resolve_theme(content: dict):
    """テーマ + オーバーライド(accent/font/variant)を適用した Theme を返す。"""
    base = THEMES[content["theme"]]
    from dataclasses import replace
    changes = {}
    if content.get("accent"):
        changes["accent"] = str(content["accent"]).lstrip("#")
    if content.get("font") and content["font"] in FONT_PAIRINGS:
        h, b = FONT_PAIRINGS[content["font"]]
        changes["heading_font"] = h
        changes["body_font"] = b
    variant = content.get("variant")
    if variant == "dark" and not base.dark:
        changes.update(dark=True, bg="1C1C1E", text="ECECEC", rule="3A3A3E")
    elif variant == "light" and base.dark:
        changes.update(dark=False, bg="FFFFFF", text="1E1E1E", rule="DDDDDD")
    return replace(base, **changes) if changes else base


_SAMPLE_CONTENT = {
    "meta": {"title": "月次営業報告(サンプル)", "date": "2026年7月", "author": "山田太郎"},
    "pattern": "conclusion",
    "slides": [
        {"type": "cover", "title": "月次営業報告", "subtitle": "2026年6月度",
         "date": "2026年7月13日", "author": "企画部 山田太郎"},
        {"type": "message", "headline": "6月の売上は前月比12%増加した",
         "body": ["新規契約が8件成立", "解約はゼロ", "主力商品Aが牽引"]},
        {"type": "table", "headline": "案の比較", "columns": ["評価軸", "A案", "B案"],
         "rows": [["コスト", "低", "高"], ["納期", "3週間", "5週間"], ["実績", "多数", "少数"]]},
    ],
}


def build_gallery(out_dir: str) -> list[str]:
    """全16テーマを同一サンプルコンテンツでレンダーし、overview.pptx も添える。生成パス一覧を返す。"""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    made = []
    for key in THEMES:
        obj = dict(_SAMPLE_CONTENT)
        obj["theme"] = key
        content = parse_content(obj)
        made.append(render_deck(content, out=str(d / f"{key}.pptx")))
    made.append(build_overview(str(d / "overview.pptx")))
    return made


def build_overview(out: str) -> str:
    """単一スライドに全テーマの 4x4 カード(bg・accent スウォッチ・テーマ名)を並べて保存。"""
    P = _require_pptx()
    prs = _new_presentation(P, None)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(P, "FFFFFF")
    keys = list(THEMES)
    cols = 4
    cw, ch = 3.0, 1.6
    x0, y0, gx, gy = 0.55, 0.5, 0.2, 0.15
    for i, key in enumerate(keys):
        t = THEMES[key]
        r, c = divmod(i, cols)
        left = x0 + c * (cw + gx)
        top = y0 + r * (ch + gy)
        card = _rect(P, slide, left, top, cw, ch, t.bg)
        card.line.color.rgb = _rgb(P, t.rule)
        card.line.width = P["Pt"](0.75)
        _rect(P, slide, left + 0.12, top + 0.12, 0.5, 0.5, t.accent)
        if t.accent2:
            _rect(P, slide, left + 0.66, top + 0.12, 0.28, 0.5, t.accent2)
        tb = _textbox(P, slide, left + 0.12, top + 0.72, cw - 0.24, 0.7)
        p = tb.text_frame.paragraphs[0]
        _apply_font(P, p.add_run(), t.heading_font, 16, bold=True, color=_rgb(P, t.text))
        p.runs[0].text = f"{t.key}"
        p2 = tb.text_frame.add_paragraph()
        _apply_font(P, p2.add_run(), t.body_font, 9, color=_rgb(P, t.text))
        p2.runs[0].text = f"{t.family} / {t.archetype}"
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
        print("\n".join(list_themes()))
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
