# -*- coding: utf-8 -*-
"""jp-slides 描画ツールキット。

SP3 で承認された16テーマ・モダンデザインの共通ヘルパー群(矩形・楕円・多角形・波形・
ピル・カード各種・テキスト・罫線)。承認済みプロトタイプ(design_ref/sp3_rich.py)から
座標・色・構成を変えずに移植したもので、以降のタスクで render_cover 等から利用する。

このモジュールはレンダリング時にのみインポートされる想定のため、python-pptx は
モジュール冒頭で直接インポートする(未インストール環境向けの遅延インポートは
呼び出し側の jp_slides.py の _require_pptx が担う)。
"""
from __future__ import annotations

import math

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

SW, SH = 13.333, 7.5
RR = MSO_SHAPE.ROUNDED_RECTANGLE
RTOP = MSO_SHAPE.ROUND_2_SAME_RECTANGLE
GO = "游ゴシック"


def rgb(h):
    return RGBColor.from_string(h)


def new_prs():
    p = Presentation()
    p.slide_width = Inches(SW)
    p.slide_height = Inches(SH)
    return p


def slide(prs, bg):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(bg)
    return s


def _ea(run, name):
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", name)


def _spc(run, val):
    try:
        run._r.get_or_add_rPr().set("spc", str(int(val)))
    except Exception:
        pass


def _alpha(sp, pct):
    try:
        el = sp.fill.fore_color._xFill.find(qn('a:srgbClr'))
        a = el.makeelement(qn('a:alpha'), {'val': str(int(pct * 1000))})
        el.append(a)
    except Exception:
        pass


def rect(s, x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE,
          alpha=None, radius=None, rot=None, lalpha=None):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.shadow.inherit = False
    if rot:
        sp.rotation = rot
    if radius is not None:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
        if alpha is not None:
            _alpha(sp, alpha)
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Pt(lw)
        if lalpha is not None:
            try:
                el = sp.line.color._xFill.find(qn('a:srgbClr'))
                a = el.makeelement(qn('a:alpha'), {'val': str(int(lalpha * 1000))})
                el.append(a)
            except Exception:
                pass
    return sp


def oval(s, x, y, w, h, fill=None, line=None, lw=1.0, alpha=None):
    return rect(s, x, y, w, h, fill=fill, line=line, lw=lw, shape=MSO_SHAPE.OVAL, alpha=alpha)


def poly(s, pts, fill=None, alpha=None, line=None, lw=1.0):
    P = [(int(x * 914400), int(y * 914400)) for x, y in pts]
    fb = s.shapes.build_freeform(P[0][0], P[0][1], scale=1.0)
    fb.add_line_segments(P[1:], close=True)
    sp = fb.convert_to_shape()
    sp.shadow.inherit = False
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
        if alpha is not None:
            _alpha(sp, alpha)
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Pt(lw)
    return sp


def wave(s, x0, x1, ybase, amp, periods, fill, alpha=None, down=True, samples=64):
    pts = []
    for i in range(samples + 1):
        t = i / samples
        x = x0 + (x1 - x0) * t
        y = ybase + amp * math.sin(2 * math.pi * periods * t + math.pi)
        pts.append((x, y))
    pts += [(x1, SH + 0.6 if down else -0.6), (x0, SH + 0.6 if down else -0.6)]
    return poly(s, pts, fill=fill, alpha=alpha)


def R(txt, font, size, color, bold=False, spc=0):
    return (txt, font, size, color, bold, spc)


def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, ls=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    first = True
    for line in runs:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        if ls:
            p.line_spacing = ls
        for (t, f, sz, c, b, sp) in line:
            r = p.add_run()
            r.text = t
            r.font.size = Pt(sz)
            r.font.bold = b
            r.font.color.rgb = rgb(c)
            _ea(r, f)
            if sp:
                _spc(r, sp)
    return tb


def pill(s, x, y, w, h, txt, fill, fg, size=11, line=None, lw=1.0):
    rect(s, x, y, w, h, fill=fill, line=line, lw=lw, shape=RR, radius=0.5)
    text(s, x, y, w, h, [[R(txt, GO, size, fg, True, 60)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def hline(s, x, y, w, color, pt=1.0, alpha=None):
    rect(s, x, y, w, pt / 72.0, fill=color, alpha=alpha)


def vline(s, x, y, h, color, pt=1.0, alpha=None):
    rect(s, x, y, pt / 72.0, h, fill=color, alpha=alpha)


# ---- カードバリエーション ----
def card_plain(s, x, y, w, h, fill, shadow=None, radius=0.06, line=None, lw=0.75, alpha=None, lalpha=None):
    if shadow:
        shp = rect(s, x + 0.05, y + 0.09, w, h, fill=shadow, shape=RR, radius=radius)
        _alpha(shp, 50)
    return rect(s, x, y, w, h, fill=fill, shape=RR, radius=radius, line=line, lw=lw, alpha=alpha, lalpha=lalpha)


def card_topstrip(s, x, y, w, h, body, strip, shadow=None, radius=0.06, sh_h=0.16):
    card_plain(s, x, y, w, h, body, shadow=shadow, radius=radius)
    rect(s, x, y, w, sh_h, fill=strip, shape=RTOP, radius=0.5)


def card_leftbar(s, x, y, w, h, body, bar, shadow=None, radius=0.06):
    card_plain(s, x, y, w, h, body, shadow=shadow, radius=radius)
    rect(s, x + 0.28, y + 0.3, 0.1, h - 0.6, fill=bar, shape=RR, radius=0.5)


def card_outline(s, x, y, w, h, line, lw=1.25, radius=0.06, fill=None, alpha=None):
    return rect(s, x, y, w, h, fill=fill, alpha=alpha, line=line, lw=lw, shape=RR, radius=radius)


def card_split(s, x, y, w, h, body, divider, shadow=None, radius=0.06):
    card_plain(s, x, y, w, h, body, shadow=shadow, radius=radius)
    hline(s, x + 0.4, y + h * 0.5, w - 0.8, divider, 1.0)
