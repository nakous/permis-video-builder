"""
COUNTDOWN — 3 s
Image darkened + ring arc + grand chiffre + dots
"""
import os, math, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import ease_spring, ease_out
from renderer.elements.background import dark_overlay
from renderer.elements.typography import _get_font
from renderer.elements.image_block import load_image, paste_image
from renderer.elements.progress_bar import draw_progress_bar

CX    = WIDTH  // 2
CY    = HEIGHT // 2 - 40
RING_R = 160
RING_W = 16
TOTAL  = 3.0


def make_frame(t, video_data, settings, progress=0.0):
    q    = video_data["question"]
    img  = load_image(_asset(q["media"]), WIDTH, HEIGHT, radius=0)
    base = dark_overlay(Image.fromarray(np.array(img)[:, :, :3]) if img.mode == "RGBA"
                        else img.copy(), alpha=0.78)

    # Glow derrière le ring
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    fill_frac = max(0.0, 1.0 - t / TOTAL)
    for i in range(28, 0, -1):
        r   = RING_R + i * 3
        a   = int(45 * (1 - i / 28) * fill_frac)
        gd.arc([CX - r, CY - r, CX + r, CY + r],
               start=-90, end=-90 + 360 * fill_frac,
               fill=theme.PRIMARY + (a,), width=1)
    base = Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(base)

    # Ring fond
    draw.arc([CX - RING_R, CY - RING_R, CX + RING_R, CY + RING_R],
             start=-90, end=270, fill=theme.BG_CARD2, width=RING_W)
    # Ring progression
    if fill_frac > 0.01:
        draw.arc([CX - RING_R, CY - RING_R, CX + RING_R, CY + RING_R],
                 start=-90, end=-90 + 360 * fill_frac,
                 fill=theme.PRIMARY, width=RING_W)

    # Chiffre
    second_left = max(1, math.ceil(TOTAL - t))
    sec_prog    = min(1.0, (t % 1.0) / 0.22)
    digit_scale = ease_spring(sec_prog)
    digit_size  = max(8, int(180 * digit_scale))
    if digit_size >= 12:
        font = _get_font(digit_size, "ExtraBold")
        d2   = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bb   = d2.textbbox((0, 0), str(second_left), font=font)
        dx   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        dy   = CY - (bb[3] - bb[1]) // 2 - bb[1]
        draw.text((dx + 4, dy + 4), str(second_left), font=font, fill=(0, 0, 0))
        draw.text((dx, dy), str(second_left), font=font, fill=theme.PRIMARY)

    # Label
    label_a = ease_out(min(1.0, t / 0.3))
    lf  = _get_font(48, "Bold")
    lbl = "Répondez !"
    lb  = draw.textbbox((0, 0), lbl, font=lf)
    lx  = CX - (lb[2] - lb[0]) // 2 - lb[0]
    ly  = CY + RING_R + 32
    draw.text((lx + 2, ly + 2), lbl, font=lf, fill=(0, 0, 0))
    draw.text((lx, ly), lbl, font=lf,
              fill=_blend(theme.TEXT_MEDIUM, label_a))

    # Dots indicateurs
    for i in range(3):
        dot_x  = CX + (i - 1) * 36
        dot_y  = ly + 68
        active = i >= (second_left - 1)
        color  = theme.PRIMARY if active else theme.BG_CARD2
        draw.ellipse([dot_x - 10, dot_y - 10, dot_x + 10, dot_y + 10], fill=color)

    draw_progress_bar(base, progress)
    return np.array(base)


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
