"""
INTRO — durée = durée réelle de intro.mp3 (pas fixe)
Design : fond brand + glow central + logo + titre + catégorie + badge difficulté
"""
import os, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import ease_spring, ease_out, ease_in_out
from renderer.elements.background import brand_bg, draw_glow, draw_decorative_lines
from renderer.elements.typography import draw_text, _get_font
from renderer.elements.image_block import load_image

CX = WIDTH // 2

# Layout :
#   LOGO_SZ  = 260
#   gap_logo_name = 40
#   name text ≈ 96px (size 90)
#   gap_name_sep = 20
#   sep         = 4
#   gap_sep_cat = 24
#   cat text ≈ 52px (size 46)
#   gap_cat_badge = 48
#   badge H  = 100
# Total ≈ 260+40+96+20+4+24+52+48+100 = 644px
_CONTENT_H = 644
LOGO_SZ    = 260
LOGO_Y_BASE = (HEIGHT - _CONTENT_H) // 2   # ~638


def make_frame(t, video_data, settings):
    base = brand_bg()
    base = draw_decorative_lines(base, color=theme.PRIMARY, alpha=12)

    glow_cy = LOGO_Y_BASE + _CONTENT_H // 2

    # Glow central PRIMARY
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw  = ImageDraw.Draw(glow_layer)
    draw_glow(glow_draw, CX, glow_cy, 500, theme.PRIMARY, steps=55)
    base = Image.alpha_composite(base.convert("RGBA"), glow_layer).convert("RGB")
    draw = ImageDraw.Draw(base)

    logo_y = LOGO_Y_BASE

    # ── Logo scale-in ────────────────────────────────────────────────────────
    logo_path = _asset(settings["site"]["logo"])
    logo_prog = ease_spring(min(1.0, t / 0.55))

    if logo_prog > 0.02:
        sz  = max(4, int(LOGO_SZ * logo_prog))
        lim = load_image(logo_path, sz, sz, radius=sz // 6, fade_alpha=logo_prog)
        base = base.convert("RGBA")
        base.paste(lim, (CX - sz // 2, logo_y + (LOGO_SZ - sz) // 2), lim)
        base = base.convert("RGB")
        draw = ImageDraw.Draw(base)

    # ── Site name ────────────────────────────────────────────────────────────
    a1 = ease_out(max(0, (t - 0.4) / 0.45))
    name_y = logo_y + LOGO_SZ + 40
    if a1 > 0:
        draw_text(draw, settings["site"]["name"],
                  CX, name_y,
                  size=90, weight="ExtraBold",
                  color=_blend(theme.PRIMARY, a1), anchor="mt",
                  shadow=True, shadow_offset=5)

    # ── Séparateur ───────────────────────────────────────────────────────────
    a2 = ease_out(max(0, (t - 0.62) / 0.35))
    sep_y = name_y + 116   # ≈ 96px font height + 20 gap
    if a2 > 0:
        sw = int(220 * a2)
        draw.line([(CX - sw, sep_y), (CX + sw, sep_y)],
                  fill=_blend(theme.ACCENT, a2), width=4)

    # ── Catégorie ────────────────────────────────────────────────────────────
    a3 = ease_out(max(0, (t - 0.75) / 0.35))
    cat_y = sep_y + 28
    if a3 > 0:
        cat = "  ".join(video_data["categorie"].upper())
        draw_text(draw, cat, CX, cat_y,
                  size=46, weight="Bold",
                  color=_blend(theme.TEXT_MEDIUM, a3), anchor="mt",
                  shadow=False)

    # ── Badge difficulté ─────────────────────────────────────────────────────
    a5 = ease_out(max(0, (t - 0.95) / 0.4))
    badge_y = cat_y + 100   # ≈ 52px font height + 48 gap
    if a5 > 0:
        _draw_diff_badge(base, draw, video_data, a5, cx=CX, y=badge_y)

    return np.array(base)


def _draw_diff_badge(base, draw, video_data, alpha, cx, y):
    from renderer.elements.card import draw_pill
    COLORS = {"facile": theme.SUCCESS, "moyen": theme.WARNING, "difficile": theme.DANGER}
    LABELS = {"facile": "FACILE", "moyen": "MOYEN", "difficile": "DIFFICILE"}
    diff  = video_data.get("difficulty", "facile")
    color = COLORS.get(diff, theme.SUCCESS)
    label = LABELS.get(diff, diff.upper())
    # Blend color toward bg based on alpha
    blended = tuple(int(color[i] * alpha + theme.BG_DARK[i] * (1 - alpha)) for i in range(3))
    base2 = draw_pill(base, cx, y, label, blended,
                      font_size=44, font_weight="ExtraBold", pad_x=52, pad_y=22)
    base.paste(base2)


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))


def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
