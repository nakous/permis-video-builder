"""
EXPLANATION — modern look.

  • image with Ken Burns slow zoom
  • title : kinetic typography
  • points : left bar grows from top, then text fades + slides
  • bottom badge : pulse glow, scale-bounce in
  • category : letter-spaced fade
"""
import os, re, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import (
    ease_out, ease_out_back, interpolate, pulse, breath,
)
from renderer.elements.background import brand_bg, gradient_overlay_bottom
from renderer.elements.typography import (
    draw_text, draw_multiline, multiline_height, _get_font, draw_kinetic_text,
)
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.progress_bar import draw_progress_bar
from renderer.elements import effects

GAP     = 20
SIDE_W  = 8
PT_FONT = 46
PAD_L   = 60

_DIFF_COLORS = {"facile": theme.SUCCESS, "moyen": theme.WARNING, "difficile": theme.DANGER}
_DIFF_LABELS = {"facile": "FACILE", "moyen": "MOYEN", "difficile": "DIFFICILE"}


def _image_contain_size(path, max_w, max_h):
    try:
        with Image.open(path) as im:
            sw, sh = im.size
    except Exception:
        return max_w, max_h
    scale = min(max_w / sw, max_h / sh)
    return int(sw * scale), int(sh * scale)


def make_frame(t, video_data, settings, progress=0.0):
    expl      = video_data["explication"]
    categorie = video_data.get("categorie", "")

    base = brand_bg()

    # ── Image : Ken Burns slow zoom ──────────────────────────────────────────
    MAX_IMG_H = int(HEIGHT * 0.42)
    img_path  = _asset(expl["media"])
    img_render_w, img_render_h = _image_contain_size(img_path, WIDTH, MAX_IMG_H)
    img_x = (WIDTH - img_render_w) // 2
    img_a = ease_out(min(1.0, t / 0.5))

    KB_DUR = 10.0
    try:
        raw = Image.open(img_path).convert("RGB")
        kb_img = effects.ken_burns(
            raw, t, KB_DUR,
            target_w=img_render_w, target_h=img_render_h,
            start_scale=1.0, end_scale=1.07, pan_x=0.10, pan_y=-0.10,
        ).convert("RGBA")
        if img_a < 1.0:
            r, g, b, a = kb_img.split()
            a = a.point(lambda p: int(p * img_a))
            kb_img = Image.merge("RGBA", (r, g, b, a))
    except Exception:
        kb_img = Image.new("RGBA", (img_render_w, img_render_h), theme.BG_CARD2)

    base = base.convert("RGBA")
    base.paste(kb_img, (img_x, 0), kb_img)
    base = base.convert("RGB")
    base = gradient_overlay_bottom(base, start_y=max(0, img_render_h - 100), color=theme.BG_DARK)
    draw = ImageDraw.Draw(base)

    # ── Difficulty badge + watermark ─────────────────────────────────────────
    WMK_H  = 56
    WMK_CY = 20 + WMK_H // 2
    diff   = video_data.get("difficulty", "facile")
    dcol   = _DIFF_COLORS.get(diff, theme.SUCCESS)
    dlbl   = _DIFF_LABELS.get(diff, diff.upper())
    pad_x  = int(22 * pulse(t, period=2.0, amplitude=0.04))
    base   = draw_pill(base, 88, WMK_CY, dlbl, dcol,
                       font_size=26, font_weight="Bold", pad_x=pad_x, pad_y=12)

    wmk_path = _asset(settings["site"]["watermark"])
    if os.path.exists(wmk_path):
        wmk = Image.open(wmk_path).convert("RGBA")
        wmk_w = int(wmk.width * WMK_H / wmk.height)
        wmk   = wmk.resize((wmk_w, WMK_H), Image.LANCZOS)
        wmk_alpha = breath(t, period=3.0, low=0.45, high=0.75)
        r2, g2, b2, a2 = wmk.split()
        a2 = a2.point(lambda p: int(p * wmk_alpha))
        wmk.putalpha(a2)
        base = base.convert("RGBA")
        base.paste(wmk, (WIDTH - wmk_w - 16, 20), wmk)
        base = base.convert("RGB")

    draw = ImageDraw.Draw(base)

    # Sep line below image — animated wipe + glow dot
    sep_p = ease_out(min(1.0, t / 0.5))
    if sep_p > 0.01:
        sw = int(WIDTH * sep_p)
        draw.line([(0, img_render_h), (sw, img_render_h)],
                  fill=theme.ACCENT, width=2)

    # ── Layout positions ─────────────────────────────────────────────────────
    CAT_Y   = img_render_h + GAP
    cat_h   = 40
    TITLE_Y = CAT_Y + cat_h + GAP

    # ── Category ─────────────────────────────────────────────────────────────
    cat_prog = ease_out(min(1.0, t / 0.35))
    if cat_prog > 0.02 and categorie:
        draw_multiline(draw, "  ".join(categorie.upper()),
                       WIDTH // 2, CAT_Y,
                       max_width=WIDTH - 80,
                       size=30, weight="SemiBold",
                       color=_blend(theme.PRIMARY, cat_prog),
                       line_spacing=1.2,
                       anchor_x="center", shadow=False)

    # ── Title : kinetic per-char ─────────────────────────────────────────────
    title_txt = expl.get("titre", "")
    title_h   = multiline_height(title_txt, WIDTH - 80, 52, "ExtraBold", 1.3)
    if title_txt:
        draw_kinetic_text(
            draw, title_txt,
            x=WIDTH // 2, y=TITLE_Y,
            size=52, weight="ExtraBold",
            color=theme.PRIMARY, anchor="mt",
            t=t, base_delay=0.20, char_stagger=0.025,
            char_duration=0.5, slide_distance=22,
            shadow=True, shadow_offset=3,
        )

    # ── Points : bar grows down, then text slides in ─────────────────────────
    points_top = TITLE_Y + title_h + GAP
    points     = expl.get("points", [])[:4]
    MAX_TXT_W  = WIDTH - PAD_L - 36
    cursor_y   = points_top

    for i, pt in enumerate(points):
        delay  = 0.55 + i * 0.20
        bar_p  = ease_out(max(0, (t - delay) / 0.32))
        text_p = ease_out(max(0, (t - delay - 0.10) / 0.36))
        txt    = _strip_emoji(pt["texte"])
        pt_h   = multiline_height(txt, MAX_TXT_W, PT_FONT, "SemiBold", line_spacing=1.35)

        # Vertical bar grows from top
        if bar_p > 0.02:
            bar_full_h = pt_h
            bar_drawn  = int(bar_full_h * bar_p)
            draw.rectangle(
                [PAD_L - 22, cursor_y,
                 PAD_L - 22 + SIDE_W, cursor_y + bar_drawn],
                fill=_blend(theme.PRIMARY, bar_p),
            )

        # Text : slide in left + fade
        if text_p > 0.02:
            off = int(interpolate(-90, 0, text_p, 1.0, ease_out))
            col = _blend(theme.TEXT_WHITE, text_p)
            draw_multiline(draw, txt,
                           PAD_L + off, cursor_y,
                           max_width=MAX_TXT_W,
                           size=PT_FONT, weight="SemiBold",
                           color=col, line_spacing=1.35, shadow=False)

        cursor_y += pt_h + GAP

    # ── Bottom badge : bounce + pulse glow ───────────────────────────────────
    badge_prog = ease_out_back(max(0, (t - 1.20) / 0.45))
    BADGE_H    = 90
    badge_y0   = HEIGHT - 56 - BADGE_H
    if badge_prog > 0.05:
        badge = expl.get("badge", {})
        btype = badge.get("type", "warning")
        BCOL  = {"danger": theme.DANGER, "warning": theme.WARNING, "success": theme.SUCCESS}
        bcol  = BCOL.get(btype, theme.WARNING)
        btxt  = _strip_emoji(badge.get("texte", ""))
        # Slide-up + slight overshoot
        by    = int(interpolate(HEIGHT, badge_y0, min(1.0, badge_prog), 1.0))

        # Continuous pulse glow under it
        if badge_prog > 0.7:
            glow_amp = pulse(t - 1.2, period=1.6, amplitude=0.15, base=1.0)
            gl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            gd = ImageDraw.Draw(gl)
            for i in range(20, 0, -1):
                ry = int(40 * i / 20 * glow_amp)
                rx = int(420 * (i / 20) * glow_amp)
                a  = int(40 * (1 - i / 20) ** 2)
                gd.ellipse([WIDTH // 2 - rx, by + BADGE_H // 2 - ry,
                            WIDTH // 2 + rx, by + BADGE_H // 2 + ry],
                           fill=bcol + (a,))
            base = Image.alpha_composite(base.convert("RGBA"), gl).convert("RGB")

        base = draw_card(base, 28, by, WIDTH - 56, BADGE_H,
                         radius=24, fill=bcol, alpha=0.95)
        draw = ImageDraw.Draw(base)
        if btxt:
            font = _get_font(42, "ExtraBold")
            bb   = draw.textbbox((0, 0), btxt, font=font)
            bx   = WIDTH // 2 - (bb[2] - bb[0]) // 2 - bb[0]
            by2  = by + BADGE_H // 2 - (bb[3] - bb[1]) // 2 - bb[1]
            draw.text((bx + 2, by2 + 2), btxt, font=font, fill=(0, 0, 0))
            draw.text((bx, by2), btxt, font=font, fill=theme.TEXT_WHITE)

    draw_progress_bar(base, progress)
    return np.array(base)


def _strip_emoji(text):
    emoji_re = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251" "]+",
        flags=re.UNICODE)
    return emoji_re.sub("", text).strip()


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
