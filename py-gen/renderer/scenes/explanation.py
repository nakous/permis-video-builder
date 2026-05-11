"""
EXPLANATION — image haut (top-alignée) + badge/watermark overlay + catégorie + titre + points + badge bas
"""
import os, re, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import ease_out, interpolate
from renderer.elements.background import brand_bg, gradient_overlay_bottom
from renderer.elements.typography import draw_text, draw_multiline, multiline_height, _get_font
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.progress_bar import draw_progress_bar

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

    # ── Image top-alignée (plus de barre noire au-dessus) ────────────────────
    MAX_IMG_H = int(HEIGHT * 0.42)
    img_path  = _asset(expl["media"])
    img_render_w, img_render_h = _image_contain_size(img_path, WIDTH, MAX_IMG_H)
    img_x   = (WIDTH - img_render_w) // 2
    img_a   = ease_out(min(1.0, t / 0.45))

    try:
        raw = Image.open(img_path).convert("RGB")
        raw = raw.resize((img_render_w, img_render_h), Image.LANCZOS)
        raw = raw.convert("RGBA")
        if img_a < 1.0:
            r, g, b, a = raw.split()
            a = a.point(lambda p: int(p * img_a))
            raw = Image.merge("RGBA", (r, g, b, a))
    except Exception:
        raw = Image.new("RGBA", (img_render_w, img_render_h), theme.BG_CARD2)

    base = base.convert("RGBA")
    base.paste(raw, (img_x, 0), raw)
    base = base.convert("RGB")
    base = gradient_overlay_bottom(base, start_y=max(0, img_render_h - 100), color=theme.BG_DARK)
    draw = ImageDraw.Draw(base)

    # ── Badge difficulté + watermark (overlay sur l'image) ───────────────────
    WMK_H  = 56
    WMK_CY = 20 + WMK_H // 2

    diff = video_data.get("difficulty", "facile")
    dcol = _DIFF_COLORS.get(diff, theme.SUCCESS)
    dlbl = _DIFF_LABELS.get(diff, diff.upper())
    base = draw_pill(base, 88, WMK_CY, dlbl, dcol,
                     font_size=26, font_weight="Bold", pad_x=22, pad_y=12)

    wmk_path = _asset(settings["site"]["watermark"])
    if os.path.exists(wmk_path):
        wmk   = Image.open(wmk_path).convert("RGBA")
        wmk_w = int(wmk.width * WMK_H / wmk.height)
        wmk   = wmk.resize((wmk_w, WMK_H), Image.LANCZOS)
        r2, g2, b2, a2 = wmk.split()
        a2 = a2.point(lambda p: int(p * 0.65))
        wmk.putalpha(a2)
        base = base.convert("RGBA")
        base.paste(wmk, (WIDTH - wmk_w - 16, 20), wmk)
        base = base.convert("RGB")

    draw = ImageDraw.Draw(base)

    # Ligne séparatrice sous l'image
    draw.line([(0, img_render_h), (WIDTH, img_render_h)], fill=theme.ACCENT, width=2)

    # ── Calcul positions verticales (espacement uniforme GAP) ─────────────────
    CAT_Y   = img_render_h + GAP
    cat_h   = 40
    TITLE_Y = CAT_Y + cat_h + GAP

    # ── Catégorie ─────────────────────────────────────────────────────────────
    cat_prog = ease_out(min(1.0, t / 0.35))
    if cat_prog > 0.02 and categorie:
        draw_multiline(draw, categorie.upper(),
                       WIDTH // 2, CAT_Y,
                       max_width=WIDTH - 80,
                       size=30, weight="SemiBold",
                       color=_blend(theme.PRIMARY, cat_prog),
                       line_spacing=1.2,
                       anchor_x="center", shadow=False)

    # ── Titre ─────────────────────────────────────────────────────────────────
    title_prog = ease_out(min(1.0, t / 0.4))
    title_txt  = expl.get("titre", "")
    title_h    = multiline_height(title_txt, WIDTH - 80, 52, "ExtraBold", 1.3)
    draw_multiline(draw, title_txt,
                   WIDTH // 2, TITLE_Y,
                   max_width=WIDTH - 80,
                   size=52, weight="ExtraBold",
                   color=_blend(theme.PRIMARY, title_prog),
                   line_spacing=1.3,
                   anchor_x="center",
                   shadow=True, shadow_offset=3)

    # ── Points (hauteur dynamique) ────────────────────────────────────────────
    points_top = TITLE_Y + title_h + GAP
    points     = expl.get("points", [])[:4]
    MAX_TXT_W  = WIDTH - PAD_L - 36
    cursor_y   = points_top

    for i, pt in enumerate(points):
        delay = 0.25 + i * 0.18
        prog  = ease_out(max(0, (t - delay) / 0.28))
        txt   = _strip_emoji(pt["texte"])
        pt_h  = multiline_height(txt, MAX_TXT_W, PT_FONT, "SemiBold", line_spacing=1.35)

        if prog >= 0.02:
            off = int(interpolate(-120, 0, prog, 1.0, ease_out))
            col = _blend(theme.TEXT_WHITE, prog)
            draw.rectangle([PAD_L + off - 22, cursor_y,
                             PAD_L + off - 22 + SIDE_W, cursor_y + pt_h],
                            fill=_blend(theme.PRIMARY, prog))
            draw_multiline(draw, txt,
                           PAD_L + off, cursor_y,
                           max_width=MAX_TXT_W,
                           size=PT_FONT, weight="SemiBold",
                           color=col, line_spacing=1.35, shadow=False)

        cursor_y += pt_h + GAP

    # ── Badge bas ─────────────────────────────────────────────────────────────
    badge_prog = ease_out(max(0, (t - 0.85) / 0.35))
    BADGE_H    = 90
    badge_y0   = HEIGHT - 56 - BADGE_H
    if badge_prog > 0.05:
        badge = expl.get("badge", {})
        btype = badge.get("type", "warning")
        BCOL  = {"danger": theme.DANGER, "warning": theme.WARNING, "success": theme.SUCCESS}
        bcol  = BCOL.get(btype, theme.WARNING)
        btxt  = _strip_emoji(badge.get("texte", ""))
        by    = int(interpolate(HEIGHT, badge_y0, badge_prog, 1.0, ease_out))
        base  = draw_card(base, 28, by, WIDTH - 56, BADGE_H,
                          radius=24, fill=bcol, alpha=0.95)
        draw  = ImageDraw.Draw(base)
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
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
