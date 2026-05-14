"""
OUTRO — modern call-to-action.

  • Floating ambient particles bg
  • Pulsating glow
  • Logo : breath scale + draw-on reveal
  • Name : kinetic per-char (no duplicate URL below)
  • CTA card : continuous pulse to drive clicks
  • Socials : 3 logos (Instagram, YouTube, X) staggered bounce-in entrée
"""
import os, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT, ORIENTATION
import theme
from renderer.animations import (
    ease_out, ease_out_back, interpolate, pulse,
)
from renderer.elements.background import brand_bg_animated, draw_glow, draw_decorative_lines
from renderer.elements.typography import draw_kinetic_text, _get_font
from renderer.elements.card import draw_card
from renderer.elements.image_block import load_image
from renderer.elements.progress_bar import draw_progress_bar
from renderer.elements import effects
from renderer.elements.social_logos import get_logo

CX = WIDTH // 2

if ORIENTATION == "landscape":
    LOGO_SZ       = 140
    LOGO_Y        = 90
    NAME_Y        = LOGO_Y + LOGO_SZ + 16
    NAME_SIZE     = 64
    CTA_Y         = NAME_Y + 100
    CTA_H         = 96
    CTA_W_PAD     = 360            # padding latéral pour la CTA en landscape
    CTA_TXT_SIZE  = 32
    SOC_Y         = CTA_Y + CTA_H + 56
    SOC_LOGO_SZ   = 60
    SOC_GAP       = 22
    SOC_ROW_H     = 74
    SOC_HANDLE_SZ = 32
    GLOW_OFFSET_Y = -40
    GLOW_R_BASE   = 280
else:
    LOGO_SZ       = 200
    LOGO_Y        = (HEIGHT - 758) // 2 - 40
    NAME_Y        = LOGO_Y + LOGO_SZ + 32
    NAME_SIZE     = 82
    CTA_Y         = NAME_Y + 130
    CTA_H         = 120
    CTA_W_PAD     = 72
    CTA_TXT_SIZE  = 36
    SOC_Y         = CTA_Y + CTA_H + 80
    SOC_LOGO_SZ   = 76
    SOC_GAP       = 28
    SOC_ROW_H     = 86
    SOC_HANDLE_SZ = 34
    GLOW_OFFSET_Y = -100
    GLOW_R_BASE   = 380


def make_frame(t, video_data, settings, progress=1.0):
    base = brand_bg_animated(t)
    base = draw_decorative_lines(base, color=theme.PRIMARY, alpha=10)

    # Ambient particles
    base = effects.floating_particles(base, t, n=22, color=theme.PRIMARY_LIGHT,
                                      seed=99, alpha=55)

    # Pulsing glow
    gl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_r = int(GLOW_R_BASE * pulse(t, period=2.4, amplitude=0.08))
    draw_glow(ImageDraw.Draw(gl), CX, HEIGHT // 2 + GLOW_OFFSET_Y, glow_r, theme.PRIMARY, steps=45)
    base = Image.alpha_composite(base.convert("RGBA"), gl).convert("RGB")
    draw = ImageDraw.Draw(base)

    site    = settings["site"]
    socials = settings["socials"]

    # ── Logo : pop in + draw-on reveal + continuous breath ───────────────────
    logo_in     = ease_out_back(min(1.0, t / 0.55))
    logo_breath = pulse(max(0, t - 0.55), period=3.2, amplitude=0.025) if t > 0.55 else 1.0
    logo_scale  = max(0.05, logo_in * logo_breath)
    if logo_scale > 0.05:
        sz = max(4, int(LOGO_SZ * logo_scale))
        lp = load_image(_asset(site["logo"]), sz, sz,
                        radius=sz // 7, fade_alpha=1.0)
        if t < 1.10:
            lp = effects.logo_reveal(lp, t, dur=0.95,
                                     scribble_color=theme.PRIMARY_LIGHT)
        base = base.convert("RGBA")
        base.paste(lp, (CX - sz // 2, LOGO_Y + (LOGO_SZ - sz) // 2), lp)
        base = base.convert("RGB")
        draw = ImageDraw.Draw(base)

    # ── Site name : kinetic ──────────────────────────────────────────────────
    draw_kinetic_text(
        draw, site["name"],
        x=CX, y=NAME_Y,
        size=NAME_SIZE, weight="ExtraBold",
        color=theme.PRIMARY, anchor="mt",
        t=t, base_delay=0.35, char_stagger=0.045,
        char_duration=0.5, slide_distance=26,
        shadow=True, shadow_offset=5,
    )

    # (séparateur teal + URL en doublon supprimés)

    # ── CTA : slide-up spring + continuous pulse ─────────────────────────────
    cta_p_in   = ease_out_back(max(0, (t - 0.7) / 0.55))
    cta_y_anim = int(interpolate(HEIGHT, CTA_Y, min(1.0, cta_p_in), 1.0))
    cta_pulse = pulse(max(0, t - 1.2), period=1.4, amplitude=0.025, base=1.0) if t > 1.2 else 1.0
    cta_full_w = WIDTH - CTA_W_PAD
    pulse_scale_w = int(cta_full_w * cta_pulse)
    pulse_scale_h = int(CTA_H * cta_pulse)
    cta_x_off = (cta_full_w - pulse_scale_w) // 2

    base = draw_card(base, (CTA_W_PAD // 2) + cta_x_off, cta_y_anim,
                     pulse_scale_w, pulse_scale_h,
                     radius=32, fill=theme.PRIMARY, alpha=0.96)
    draw = ImageDraw.Draw(base)

    if cta_p_in > 0.3:
        ca   = ease_out(max(0, (cta_p_in - 0.3) / 0.5))
        txt  = site.get("callToAction", "Testez vos connaissances !")
        font = _get_font(CTA_TXT_SIZE, "ExtraBold")
        bb   = draw.textbbox((0, 0), txt, font=font)
        tx   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        ty_  = cta_y_anim + pulse_scale_h // 2 - (bb[3] - bb[1]) // 2 - bb[1]
        draw.text((tx, ty_), txt, font=font,
                  fill=_blend(theme.TEXT_DARK, ca))

    # ── Socials : 3 lignes (Instagram / YouTube / X) avec entrée bounce ──────
    soc_items = []
    for key in ("instagram", "youtube", "x"):
        handle = socials.get(key)
        if handle:
            soc_items.append((key, handle))

    base = _draw_socials(base, t, soc_items)

    draw_progress_bar(base, progress)
    return np.array(base)


def _draw_socials(base, t, soc_items):
    """3 lignes empilées, centrées : [logo]  @handle — entrée bounce décalée.
    Même disposition en portrait et en landscape (Instagram / YouTube / X)."""
    if not soc_items:
        return base

    # Compute layout : centred horizontally, max width based on widest handle
    font = _get_font(SOC_HANDLE_SZ, theme.WEIGHT["semibold"])
    d_dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    handle_widths = [int(d_dummy.textlength(h, font=font)) for _, h in soc_items]
    max_handle_w  = max(handle_widths)
    row_w = SOC_LOGO_SZ + SOC_GAP + max_handle_w
    row_x = (WIDTH - row_w) // 2

    base_delay   = 1.20
    item_stagger = 0.22
    enter_dur    = 0.55

    for i, (key, handle) in enumerate(soc_items):
        delay = base_delay + i * item_stagger
        sp    = ease_out_back(max(0, (t - delay) / enter_dur))
        if sp < 0.02:
            continue
        # Slide up from below + slight scale + fade
        slide_y = int(interpolate(60, 0, min(1.0, sp), 1.0, ease_out))
        alpha   = min(1.0, sp)
        scale   = max(0.6, min(1.05, sp))

        row_y = SOC_Y + i * SOC_ROW_H + slide_y

        # Logo (with scale)
        logo_sz  = int(SOC_LOGO_SZ * scale)
        logo_img = get_logo(key, logo_sz)
        if logo_img is not None:
            # Apply global alpha
            if alpha < 0.99:
                r, g, b, a = logo_img.split()
                a = a.point(lambda p: int(p * alpha))
                logo_img = Image.merge("RGBA", (r, g, b, a))
            lx = row_x + (SOC_LOGO_SZ - logo_sz) // 2
            ly = row_y + (SOC_LOGO_SZ - logo_sz) // 2
            base = base.convert("RGBA")
            base.paste(logo_img, (lx, ly), logo_img)
            base = base.convert("RGB")

        # Handle text (slide-up + fade)
        draw = ImageDraw.Draw(base)
        text_color = _blend(theme.TEXT_WHITE, alpha)
        # Shadow
        draw.text((row_x + SOC_LOGO_SZ + SOC_GAP + 2,
                   row_y + SOC_LOGO_SZ // 2 + 2),
                  handle, font=font, fill=(0, 0, 0), anchor="lm")
        draw.text((row_x + SOC_LOGO_SZ + SOC_GAP,
                   row_y + SOC_LOGO_SZ // 2),
                  handle, font=font, fill=text_color, anchor="lm")
    return base


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
