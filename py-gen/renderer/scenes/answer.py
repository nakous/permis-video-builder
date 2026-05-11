"""
ANSWER — durée = audio correct/wrong
VRAI/FAUX ou lettre QCM + bonne réponse + mauvais choix barrés
"""
import numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import ease_spring, ease_out
from renderer.elements.background import radial_gradient
from renderer.elements.typography import _get_font, draw_text, draw_multiline
from renderer.elements.progress_bar import draw_progress_bar

CX       = WIDTH  // 2
GROUP_CY = int(HEIGHT * 0.42)


def make_frame(t, video_data, settings, progress=0.0):
    q      = video_data["question"]
    q_type = q.get("type", "vrai_faux")
    choix  = q.get("choix", [])
    reponse = video_data["reponse"]   # ex: "VRAI", "FAUX", "A - 80 km/h"

    # Détermine couleur : vert si VRAI ou si première lettre correspond au bon choix
    if q_type == "vrai_faux":
        is_correct_color = reponse.upper() == "VRAI"
    else:
        # Pour QCM on utilise SUCCESS par défaut (bonne réponse est toujours bonne)
        is_correct_color = True

    accent = theme.SUCCESS if is_correct_color else theme.DANGER
    edge   = (5, 50, 40) if is_correct_color else (50, 5, 5)

    base = radial_gradient(
        center_color=tuple(int(c * 0.60) for c in accent),
        edge_color=edge,
        cx=CX, cy=GROUP_CY,
        radius=max(WIDTH, HEIGHT) * 0.90
    )

    # Particules de lumière
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for cx2, cy2, r2, a2 in [
        (CX, GROUP_CY, 340, 35),
        (CX - 200, GROUP_CY + 200, 180, 18),
        (CX + 220, GROUP_CY - 150, 160, 15),
    ]:
        for i in range(r2, 0, -10):
            alpha = int(a2 * (1 - i / r2))
            gd.ellipse([cx2 - i, cy2 - i, cx2 + i, cy2 + i],
                       fill=accent + (alpha,))
    base = Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(base)

    if q_type == "vrai_faux":
        _draw_vrai_faux(draw, base, t, reponse, accent, is_correct_color)
    else:
        _draw_qcm(draw, base, t, reponse, choix, accent)

    draw_progress_bar(base, progress)
    return np.array(base)


def _draw_vrai_faux(draw, base, t, reponse, accent, is_vrai):
    label = reponse.upper()

    # Icône check / cross
    icon_scale = ease_spring(min(1.0, t / 0.35))
    icon_size  = int(140 * icon_scale)
    icon_cy    = GROUP_CY - 120
    if icon_size > 8:
        _draw_icon(draw, CX, icon_cy, is_vrai, theme.TEXT_WHITE, icon_size)

    # Grand label
    label_scale = ease_spring(min(1.0, max(0, (t - 0.08)) / 0.45))
    lsize = int(180 * label_scale)
    label_y = GROUP_CY + 30
    if lsize >= 12:
        font = _get_font(lsize, "ExtraBold")
        d2   = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bb   = d2.textbbox((0, 0), label, font=font)
        lx   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        for ox, oy in [(5, 5), (-3, 5), (5, -3), (0, 6)]:
            draw.text((lx + ox, label_y + oy), label, font=font, fill=(0, 0, 0))
        draw.text((lx, label_y), label, font=font, fill=theme.TEXT_WHITE)

    sep_y = label_y + lsize + 24 if lsize else label_y + 200
    _draw_separator_and_title(draw, base, t, sep_y)


def _draw_qcm(draw, base, t, reponse, choix, accent):
    # "Réponse :" label
    label_a = ease_spring(min(1.0, t / 0.4))
    lsize   = int(60 * label_a)
    if lsize >= 10:
        font = _get_font(lsize, "Bold")
        d2   = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bb   = d2.textbbox((0, 0), "Réponse :", font=font)
        lx   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        ly   = GROUP_CY - 260
        draw.text((lx + 3, ly + 3), "Réponse :", font=font, fill=(0, 0, 0))
        draw.text((lx, ly), "Réponse :", font=font, fill=theme.TEXT_MEDIUM)

    # Bonne réponse en grand (ex: "A - 80 km/h")
    ans_scale = ease_spring(min(1.0, max(0, (t - 0.1)) / 0.45))
    asize     = int(110 * ans_scale)
    ans_y     = GROUP_CY - 160
    if asize >= 12:
        font = _get_font(asize, "ExtraBold")
        d2   = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bb   = d2.textbbox((0, 0), reponse, font=font)
        ax   = CX - (bb[2] - bb[0]) // 2 - bb[0]
        for ox, oy in [(4, 4), (-2, 4)]:
            draw.text((ax + ox, ans_y + oy), reponse, font=font, fill=(0, 0, 0))
        draw.text((ax, ans_y), reponse, font=font, fill=theme.TEXT_WHITE)

    # Mauvais choix barrés
    bad_choix = [c for c in choix if not reponse.startswith(c["lettre"])]
    for i, c in enumerate(bad_choix):
        bp    = ease_out(max(0, (t - 0.5 - i * 0.15) / 0.3))
        if bp < 0.02:
            continue
        by    = GROUP_CY + 60 + i * 80
        label = f"{c['lettre']} - {c['texte']}"
        font  = _get_font(40, "SemiBold")
        d2    = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bb    = d2.textbbox((0, 0), label, font=font)
        lw    = bb[2] - bb[0]
        lx    = CX - lw // 2 - bb[0]
        col   = _blend(theme.TEXT_MEDIUM, bp * 0.6)
        draw.text((lx, by), label, font=font, fill=col)
        # barre rouge
        mid_y = by + (bb[3] - bb[1]) // 2
        bar_a = int(200 * bp)
        draw.line([(lx - 4, mid_y), (lx + lw + 4, mid_y)],
                  fill=theme.DANGER + (bar_a,), width=4)

    sep_y = GROUP_CY + 60 + max(1, len(bad_choix)) * 80 + 20
    _draw_separator_and_title(draw, base, t, sep_y)


def _draw_separator_and_title(draw, base, t, sep_y):
    sep_a = ease_out(max(0, (t - 0.5) / 0.3))
    if sep_a > 0:
        sw = int(180 * sep_a)
        draw.line([(CX - sw, sep_y), (CX + sw, sep_y)],
                  fill=(255, 255, 255), width=2)

    conf_a = ease_out(max(0, (t - 0.6) / 0.4))
    if conf_a > 0.05:
        from renderer.elements.typography import draw_multiline
        titre = ""
        draw_multiline(draw, titre,
                       CX, sep_y + 20,
                       max_width=WIDTH - 120,
                       size=42, weight="Bold",
                       color=_blend(theme.TEXT_WHITE, conf_a * 0.85),
                       anchor_x="center", shadow=True)


def _draw_icon(draw, cx, cy, is_vrai, color, size):
    h  = size // 2
    th = max(10, size // 8)
    if is_vrai:
        pts = [(cx - h * 0.55, cy + h * 0.05),
               (cx - h * 0.05, cy + h * 0.55),
               (cx + h * 0.60, cy - h * 0.55)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=color, width=th)
    else:
        draw.line([(cx - h * 0.62, cy - h * 0.62),
                   (cx + h * 0.62, cy + h * 0.62)], fill=color, width=th)
        draw.line([(cx + h * 0.62, cy - h * 0.62),
                   (cx - h * 0.62, cy + h * 0.62)], fill=color, width=th)


def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
