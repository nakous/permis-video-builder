"""
INTRO — modern animated brand intro.

Layered animations:
  • animated radial glow that pulses
  • floating ambient particles
  • logo: spring scale-in + slight rotation
  • site name: kinetic typography (per-char slide+fade)
  • separator: width-wipe from center
  • category: per-char stagger
  • difficulty badge: bounce-in + glow ring
"""
import os, math, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import (
    ease_spring, ease_out, ease_in_out, ease_out_back, ease_out_bounce,
    interpolate, pulse, breath,
)
from renderer.elements.background import brand_bg, draw_glow, draw_decorative_lines
from renderer.elements.typography import draw_text, draw_kinetic_text, _get_font
from renderer.elements.image_block import load_image
from renderer.elements import effects

CX = WIDTH // 2

LOGO_SZ    = 260
_CONTENT_H = 660
LOGO_Y_BASE = (HEIGHT - _CONTENT_H) // 2


def make_frame(t, video_data, settings):
    base = brand_bg()
    base = draw_decorative_lines(base, color=theme.PRIMARY, alpha=12)

    # Floating ambient particles — adds life to the bg
    base = effects.floating_particles(base, t, n=22, color=theme.PRIMARY_LIGHT,
                                      seed=42, alpha=55)

    glow_cy = LOGO_Y_BASE + _CONTENT_H // 2

    # Pulsating glow
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw  = ImageDraw.Draw(glow_layer)
    glow_radius = int(500 * pulse(t, period=2.4, amplitude=0.08))
    draw_glow(glow_draw, CX, glow_cy, glow_radius, theme.PRIMARY, steps=55)
    base = Image.alpha_composite(base.convert("RGBA"), glow_layer).convert("RGB")
    draw = ImageDraw.Draw(base)

    logo_y = LOGO_Y_BASE

    # ── Logo : scale-in spring + subtle continuous breath ────────────────────
    logo_path = _asset(settings["site"]["logo"])
    logo_in   = ease_out_back(min(1.0, t / 0.55))
    breath_s  = pulse(max(0, t - 0.55), period=3.0, amplitude=0.025) if t > 0.55 else 1.0
    logo_scale = max(0.05, logo_in * breath_s)

    if logo_scale > 0.05:
        sz  = max(4, int(LOGO_SZ * logo_scale))
        lim = load_image(logo_path, sz, sz, radius=sz // 6,
                         fade_alpha=min(1.0, logo_in * 1.2))
        base = base.convert("RGBA")
        base.paste(lim, (CX - sz // 2, logo_y + (LOGO_SZ - sz) // 2), lim)
        base = base.convert("RGB")
        draw = ImageDraw.Draw(base)

    # ── Site name : kinetic per-char ──────────────────────────────────────────
    name_y = logo_y + LOGO_SZ + 40
    draw_kinetic_text(
        draw, settings["site"]["name"],
        x=CX, y=name_y,
        size=92, weight="ExtraBold",
        color=theme.PRIMARY, anchor="mt",
        t=t, base_delay=0.42, char_stagger=0.05,
        char_duration=0.55, slide_distance=32,
        easing=ease_out_back, shadow=True, shadow_offset=5,
    )

    # ── Separator : wipe from center ─────────────────────────────────────────
    sep_y  = name_y + 118
    sep_p  = ease_out(max(0, (t - 0.78) / 0.45))
    if sep_p > 0:
        sw = int(240 * sep_p)
        draw.line([(CX - sw, sep_y), (CX + sw, sep_y)],
                  fill=_blend(theme.ACCENT, sep_p), width=4)
        # subtle glow dot at center
        if sep_p > 0.3:
            ds = int(8 * (sep_p - 0.3) / 0.7)
            if ds > 0:
                draw.ellipse([CX - ds, sep_y - ds, CX + ds, sep_y + ds],
                             fill=theme.PRIMARY_LIGHT)

    # ── Category : kinetic letter-spaced ──────────────────────────────────────
    cat_y = sep_y + 28
    cat   = "  ".join(video_data["categorie"].upper())
    draw_kinetic_text(
        draw, cat,
        x=CX, y=cat_y,
        size=46, weight="Bold",
        color=theme.TEXT_MEDIUM, anchor="mt",
        t=t, base_delay=0.95, char_stagger=0.025,
        char_duration=0.4, slide_distance=18,
        easing=ease_out, shadow=False,
    )

    # ── Difficulty badge : bounce + glow ring ────────────────────────────────
    badge_y = cat_y + 105
    badge_p = ease_out_back(max(0, (t - 1.25) / 0.55))
    if badge_p > 0.02:
        base = _draw_diff_badge_modern(base, video_data, badge_p, t, cx=CX, y=badge_y)

    return np.array(base)


def _draw_diff_badge_modern(base, video_data, prog, t, cx, y):
    from renderer.elements.card import draw_pill
    COLORS = {"facile": theme.SUCCESS, "moyen": theme.WARNING, "difficile": theme.DANGER}
    LABELS = {"facile": "FACILE", "moyen": "MOYEN", "difficile": "DIFFICILE"}
    diff   = video_data.get("difficulty", "facile")
    color  = COLORS.get(diff, theme.SUCCESS)
    label  = LABELS.get(diff, diff.upper())

    # Animated glow ring around badge (continuous)
    if prog > 0.6:
        ring_breath = pulse(t - 1.25, period=1.6, amplitude=0.12, base=1.0)
        ring_r = int(120 * ring_breath)
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd   = ImageDraw.Draw(glow)
        for i in range(18, 0, -1):
            a = int(28 * (1 - i / 18) * ((prog - 0.6) / 0.4))
            r = ring_r + i * 4
            gd.ellipse([cx - r, y - r // 2, cx + r, y + r // 2],
                       outline=color + (a,), width=1)
        base = Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")

    # Pill scale via prog
    pill_color = tuple(int(color[i] * min(1.0, prog * 1.1)
                            + theme.BG_DARK[i] * (1 - min(1.0, prog * 1.1)))
                       for i in range(3))
    base = draw_pill(base, cx, y, label, pill_color,
                     font_size=int(44 * min(1.05, prog)),
                     font_weight="ExtraBold",
                     pad_x=int(54 * min(1.05, prog)),
                     pad_y=int(22 * min(1.05, prog)))
    return base


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))


def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
