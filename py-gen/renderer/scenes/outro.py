"""
OUTRO — modern call-to-action.

  • Floating ambient particles bg
  • Pulsating glow
  • Logo : breath scale
  • Name : kinetic per-char
  • CTA card : continuous pulse to drive clicks
  • Socials : bounce entry stagger
"""
import os, math, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import (
    ease_spring, ease_out, ease_out_back, interpolate, pulse, breath,
)
from renderer.elements.background import brand_bg, draw_glow, draw_decorative_lines
from renderer.elements.typography import draw_text, draw_kinetic_text, _get_font
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.image_block import load_image
from renderer.elements.progress_bar import draw_progress_bar
from renderer.elements import effects

CX = WIDTH // 2

LOGO_SZ  = 200
LOGO_Y   = (HEIGHT - 758) // 2 - 40
NAME_Y   = LOGO_Y + LOGO_SZ + 32
SEP_Y    = NAME_Y + 94
URL_Y    = SEP_Y  + 20
CTA_Y    = URL_Y  + 72
CTA_H    = 120
SOC_Y    = CTA_Y  + CTA_H + 60

_SOC_COLORS = {
    "tiktok":    (0,   0,   0),
    "instagram": (193, 53,  132),
}


def make_frame(t, video_data, settings, progress=1.0):
    base = brand_bg()
    base = draw_decorative_lines(base, color=theme.PRIMARY, alpha=10)

    # Floating ambient particles
    base = effects.floating_particles(base, t, n=22, color=theme.PRIMARY_LIGHT,
                                      seed=99, alpha=55)

    # Pulsing glow
    gl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_r = int(380 * pulse(t, period=2.4, amplitude=0.08))
    draw_glow(ImageDraw.Draw(gl), CX, HEIGHT // 2 - 100, glow_r, theme.PRIMARY, steps=45)
    base = Image.alpha_composite(base.convert("RGBA"), gl).convert("RGB")
    draw = ImageDraw.Draw(base)

    site    = settings["site"]
    socials = settings["socials"]

    # ── Logo : pop in + continuous breath ────────────────────────────────────
    logo_in    = ease_out_back(min(1.0, t / 0.55))
    logo_breath = pulse(max(0, t - 0.55), period=3.2, amplitude=0.025) if t > 0.55 else 1.0
    logo_scale = max(0.05, logo_in * logo_breath)
    if logo_scale > 0.05:
        sz = max(4, int(LOGO_SZ * logo_scale))
        lp = load_image(_asset(site["logo"]), sz, sz,
                        radius=sz // 7, fade_alpha=min(1.0, logo_in * 1.2))
        base = base.convert("RGBA")
        base.paste(lp, (CX - sz // 2, LOGO_Y + (LOGO_SZ - sz) // 2), lp)
        base = base.convert("RGB")
        draw = ImageDraw.Draw(base)

    # ── Site name : kinetic ──────────────────────────────────────────────────
    draw_kinetic_text(
        draw, site["name"],
        x=CX, y=NAME_Y,
        size=82, weight="ExtraBold",
        color=theme.PRIMARY, anchor="mt",
        t=t, base_delay=0.35, char_stagger=0.045,
        char_duration=0.5, slide_distance=26,
        shadow=True, shadow_offset=5,
    )

    # Separator
    a2 = ease_out(max(0, (t - 0.62) / 0.35))
    if a2 > 0:
        sw = int(200 * a2)
        draw.line([(CX - sw, SEP_Y), (CX + sw, SEP_Y)],
                  fill=_blend(theme.ACCENT, a2), width=3)

    # URL
    a3 = ease_out(max(0, (t - 0.72) / 0.35))
    if a3 > 0:
        url = site["url"].replace("https://", "")
        draw_text(draw, url, CX, URL_Y,
                  size=32, weight="Regular",
                  color=_blend(theme.TEXT_MEDIUM, a3 * 0.7),
                  anchor="mt", shadow=False)

    # ── CTA : slide-up spring + continuous pulse ─────────────────────────────
    cta_p_in   = ease_out_back(max(0, (t - 0.7) / 0.55))
    cta_y_anim = int(interpolate(HEIGHT, CTA_Y, min(1.0, cta_p_in), 1.0))
    # Continuous pulse after settled
    cta_pulse = pulse(max(0, t - 1.2), period=1.4, amplitude=0.025, base=1.0) if t > 1.2 else 1.0
    pulse_scale_w = int((WIDTH - 72) * cta_pulse)
    pulse_scale_h = int(CTA_H * cta_pulse)
    cta_x_off = (WIDTH - 72 - pulse_scale_w) // 2

    base = draw_card(base, 36 + cta_x_off, cta_y_anim,
                     pulse_scale_w, pulse_scale_h,
                     radius=32, fill=theme.PRIMARY, alpha=0.96)
    draw = ImageDraw.Draw(base)

    if cta_p_in > 0.3:
        ca   = ease_out(max(0, (cta_p_in - 0.3) / 0.5))
        txt  = site.get("callToAction", "Testez vos connaissances !")
        font = _get_font(36, "ExtraBold")
        bb   = draw.textbbox((0, 0), txt, font=font)
        tx   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        ty_  = cta_y_anim + pulse_scale_h // 2 - (bb[3] - bb[1]) // 2 - bb[1]
        draw.text((tx, ty_), txt, font=font,
                  fill=_blend(theme.TEXT_DARK, ca))

    # ── Socials : bounce-in slide from left ──────────────────────────────────
    soc_items = []
    if socials.get("tiktok"):
        soc_items.append(("TikTok",    socials["tiktok"],    _SOC_COLORS["tiktok"]))
    if socials.get("instagram"):
        soc_items.append(("Instagram", socials["instagram"], _SOC_COLORS["instagram"]))

    for i, (platform, handle, col) in enumerate(soc_items[:2]):
        sp = ease_out_back(max(0, (t - 1.20 - i * 0.18) / 0.45))
        if sp < 0.02:
            continue
        off   = int(interpolate(-WIDTH, 0, min(1.0, sp), 1.0))
        row_y = SOC_Y + i * 80

        bw, bh = 170, 56
        bx = CX - bw - 16 + off
        base = draw_card(base, bx, row_y, bw, bh, radius=14, fill=col, alpha=0.95)
        draw = ImageDraw.Draw(base)
        pf   = _get_font(28, "Bold")
        pb   = draw.textbbox((0, 0), platform, font=pf)
        draw.text((bx + bw // 2 - (pb[2] - pb[0]) // 2 - pb[0],
                   row_y + bh // 2 - (pb[3] - pb[1]) // 2 - pb[1]),
                  platform, font=pf, fill=theme.TEXT_WHITE)

        hf = _get_font(30, "SemiBold")
        draw.text((CX + 16 + off, row_y + bh // 2),
                  handle, font=hf,
                  fill=_blend(theme.TEXT_MEDIUM, min(1.0, sp)), anchor="lm")

    draw_progress_bar(base, progress)
    return np.array(base)


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
