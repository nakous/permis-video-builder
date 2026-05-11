"""
OUTRO — plein écran centré verticalement
Logo + nom + CTA + socials
"""
import os, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import ease_spring, ease_out, interpolate
from renderer.elements.background import brand_bg, draw_glow, draw_decorative_lines
from renderer.elements.typography import draw_text, _get_font
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.image_block import load_image
from renderer.elements.progress_bar import draw_progress_bar

CX = WIDTH // 2

# Layout centré à ~40% de la hauteur pour laisser espace bas
LOGO_SZ  = 200
# Total group height ≈ 200+32+96+20+70+120+60+160 = ~758px
LOGO_Y   = (HEIGHT - 758) // 2 - 40   # ~521
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

    # Glow
    gl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_glow(ImageDraw.Draw(gl), CX, HEIGHT // 2 - 100, 380, theme.PRIMARY, steps=45)
    base = Image.alpha_composite(base.convert("RGBA"), gl).convert("RGB")
    draw = ImageDraw.Draw(base)

    site    = settings["site"]
    socials = settings["socials"]

    # ── Logo ────────────────────────────────────────────────────────────────
    logo_a = ease_out(min(1.0, t / 0.5))
    if logo_a > 0.02:
        lp = load_image(_asset(site["logo"]), LOGO_SZ, LOGO_SZ,
                        radius=LOGO_SZ // 7, fade_alpha=logo_a)
        base = base.convert("RGBA")
        base.paste(lp, (CX - LOGO_SZ // 2, LOGO_Y), lp)
        base = base.convert("RGB")
        draw = ImageDraw.Draw(base)

    # ── Nom ──────────────────────────────────────────────────────────────────
    a1 = ease_out(max(0, (t - 0.35) / 0.4))
    if a1 > 0:
        draw_text(draw, site["name"], CX, NAME_Y,
                  size=80, weight="ExtraBold",
                  color=_blend(theme.PRIMARY, a1), anchor="mt",
                  shadow=True, shadow_offset=5)

    # Séparateur
    a2 = ease_out(max(0, (t - 0.55) / 0.35))
    if a2 > 0:
        sw = int(180 * a2)
        draw.line([(CX - sw, SEP_Y), (CX + sw, SEP_Y)],
                  fill=_blend(theme.ACCENT, a2), width=3)

    # URL
    a3 = ease_out(max(0, (t - 0.65) / 0.35))
    if a3 > 0:
        url = site["url"].replace("https://", "")
        draw_text(draw, url, CX, URL_Y,
                  size=32, weight="Regular",
                  color=_blend(theme.TEXT_MEDIUM, a3 * 0.7), anchor="mt", shadow=False)

    # ── CTA card (slide-up) ───────────────────────────────────────────────────
    cta_p = ease_spring(max(0, (t - 0.7) / 0.5))
    cta_y = int(interpolate(HEIGHT, CTA_Y, cta_p, 1.0, ease_out))
    base  = draw_card(base, 36, cta_y, WIDTH - 72, CTA_H,
                      radius=32, fill=theme.PRIMARY, alpha=0.96)
    draw  = ImageDraw.Draw(base)
    if cta_p > 0.3:
        ca   = ease_out(max(0, (cta_p - 0.3) / 0.5))
        txt  = site.get("callToAction", "Testez vos connaissances !")
        font = _get_font(36, "ExtraBold")
        bb   = draw.textbbox((0, 0), txt, font=font)
        tx   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        ty_  = cta_y + CTA_H // 2 - (bb[3] - bb[1]) // 2 - bb[1]
        draw.text((tx, ty_), txt, font=font,
                  fill=_blend(theme.TEXT_DARK, ca))

    # ── Socials ───────────────────────────────────────────────────────────────
    soc_items = []
    if socials.get("tiktok"):
        soc_items.append(("TikTok",    socials["tiktok"],    _SOC_COLORS["tiktok"]))
    if socials.get("instagram"):
        soc_items.append(("Instagram", socials["instagram"], _SOC_COLORS["instagram"]))

    for i, (platform, handle, col) in enumerate(soc_items[:2]):
        sp  = ease_out(max(0, (t - 1.1 - i * 0.2) / 0.4))
        if sp < 0.02:
            continue
        off   = int(interpolate(-WIDTH, 0, sp, 1.0, ease_out))
        row_y = SOC_Y + i * 80

        # Badge plateforme
        bw, bh = 170, 56
        bx = CX - bw - 16 + off
        base = draw_card(base, bx, row_y, bw, bh, radius=14, fill=col, alpha=0.95)
        draw = ImageDraw.Draw(base)
        pf   = _get_font(28, "Bold")
        pb   = draw.textbbox((0, 0), platform, font=pf)
        draw.text((bx + bw // 2 - (pb[2] - pb[0]) // 2 - pb[0],
                   row_y + bh // 2 - (pb[3] - pb[1]) // 2 - pb[1]),
                  platform, font=pf, fill=theme.TEXT_WHITE)

        # Handle
        hf = _get_font(30, "SemiBold")
        draw.text((CX + 16 + off, row_y + bh // 2),
                  handle, font=hf,
                  fill=_blend(theme.TEXT_MEDIUM, sp), anchor="lm")

    draw_progress_bar(base, progress)
    return np.array(base)


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
