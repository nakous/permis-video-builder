"""
QUESTION — durée = durée réelle de question.mp3

Layout :
  [image contain — hauteur calculée sur le ratio réel]
  [bloc question — slide-up, fond semi-transparent, retour à la ligne]
  [séparateur PRIMARY]
  [choix A / B / C — chaque ligne slide séparément avec stagger]
"""
import os, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import ease_out, ease_spring, interpolate
from renderer.elements.background import gradient_overlay_bottom
from renderer.elements.typography import draw_multiline, multiline_height, _get_font
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.image_block import load_image  # noqa: F401 (used in helpers)
from renderer.elements.progress_bar import draw_progress_bar

PAD_H    = 48    # padding horizontal texte
TEXT_W   = WIDTH - PAD_H * 2
CHOICE_H = 96    # hauteur d'une ligne de choix
CHOICE_R = 24    # border-radius carte choix
BOT_PAD  = 48    # espace sous le dernier choix

_DIFF_COLORS = {"facile": theme.SUCCESS, "moyen": theme.WARNING, "difficile": theme.DANGER}
_DIFF_LABELS = {"facile": "FACILE", "moyen": "MOYEN", "difficile": "DIFFICILE"}
_CHOICE_COLOR = theme.PRIMARY   # couleur unique pour tous les choix


def _image_contain_height(path, max_w, max_h):
    """Retourne (render_w, render_h) de l'image après contain-fit dans max_w×max_h."""
    try:
        with Image.open(path) as im:
            sw, sh = im.size
    except Exception:
        return max_w, max_h
    scale   = min(max_w / sw, max_h / sh)
    return int(sw * scale), int(sh * scale)


GAP = 20   # espace uniforme entre toutes les sections


def make_frame(t, video_data, settings, progress=0.0):
    q        = video_data["question"]
    q_type   = q.get("type", "vrai_faux")
    choix    = q.get("choix", [])
    q_text   = q["texte"]
    categorie = video_data.get("categorie", "")
    img_path = _asset(q["media"])

    # ── Image : contain alignée en HAUT (pas de barre noire au-dessus) ────────
    MAX_IMG_H = int(HEIGHT * 0.44)
    img_render_w, img_render_h = _image_contain_height(img_path, WIDTH, MAX_IMG_H)
    img_x      = (WIDTH - img_render_w) // 2   # centré horizontalement
    img_bottom = img_render_h                   # colle directement au top=0

    img_alpha = ease_out(min(1.0, t / 0.4))
    # Charge l'image redimensionnée sans letterbox vertical
    try:
        raw = Image.open(img_path).convert("RGB")
        raw = raw.resize((img_render_w, img_render_h), Image.LANCZOS)
        if img_alpha < 1.0:
            raw = raw.convert("RGBA")
            r, g, b, a = raw.split()
            a = a.point(lambda p: int(p * img_alpha))
            raw = Image.merge("RGBA", (r, g, b, a))
        else:
            raw = raw.convert("RGBA")
    except Exception:
        raw = Image.new("RGBA", (img_render_w, img_render_h), theme.BG_CARD2)

    base = Image.new("RGB", (WIDTH, HEIGHT), theme.BG_DARK)
    base = base.convert("RGBA")
    base.paste(raw, (img_x, 0), raw)
    base = base.convert("RGB")

    # Dégradé bas de l'image → fond
    base = gradient_overlay_bottom(base,
                                   start_y=max(0, img_bottom - 100),
                                   color=theme.BG_DARK)
    draw = ImageDraw.Draw(base)

    # ── Badge difficulté + watermark (overlay sur l'image, même axe Y) ────────
    WMK_H  = 56
    WMK_CY = 20 + WMK_H // 2

    diff = video_data.get("difficulty", "facile")
    dcol = _DIFF_COLORS.get(diff, theme.SUCCESS)
    dlbl = _DIFF_LABELS.get(diff, diff.upper())
    base = draw_pill(base, 88, WMK_CY, dlbl, dcol,
                     font_size=26, font_weight="Bold", pad_x=22, pad_y=12)

    wmk_path = _asset(settings["site"]["watermark"])
    if os.path.exists(wmk_path):
        wmk = Image.open(wmk_path).convert("RGBA")
        wmk_w = int(wmk.width * WMK_H / wmk.height)
        wmk   = wmk.resize((wmk_w, WMK_H), Image.LANCZOS)
        r2, g2, b2, a2 = wmk.split()
        a2 = a2.point(lambda p: int(p * 0.65))
        wmk.putalpha(a2)
        base = base.convert("RGBA")
        base.paste(wmk, (WIDTH - wmk_w - 16, 20), wmk)
        base = base.convert("RGB")

    draw = ImageDraw.Draw(base)

    # ── Calcul positions verticales (espacement uniforme GAP) ─────────────────
    CAT_Y       = img_bottom + GAP
    cat_h       = 52
    Q_Y         = CAT_Y + cat_h + GAP
    q_h         = multiline_height(q_text, TEXT_W - 16, 44, "Bold", line_spacing=1.35)
    SEP_Y       = Q_Y + q_h + GAP
    CHOICES_TOP = SEP_Y + GAP + 8

    # ── Catégorie (fade-in sous l'image) ──────────────────────────────────────
    cat_prog = ease_out(max(0, (t - 0.15) / 0.35))
    if cat_prog > 0.02 and categorie:
        draw_multiline(draw, categorie.upper(),
                       WIDTH // 2, CAT_Y,
                       max_width=TEXT_W,
                       size=32, weight="SemiBold",
                       color=_blend(theme.PRIMARY, cat_prog),
                       line_spacing=1.2,
                       anchor_x="center", shadow=False)

    # ── Bloc question (slide-up depuis le bas) ────────────────────────────────
    q_prog  = ease_out(max(0, (t - 0.20) / 0.45))
    q_off   = int(interpolate(80, 0, q_prog, 1.0, ease_out))
    q_alpha = q_prog

    if q_alpha > 0.02:
        bg_h = q_h + 32
        base = draw_card(base, PAD_H - 16, Q_Y + q_off - 8,
                         WIDTH - (PAD_H - 16) * 2, bg_h,
                         radius=20, fill=theme.BG_CARD, alpha=0.55)
        draw = ImageDraw.Draw(base)

        draw.rectangle([PAD_H - 16, Q_Y + q_off,
                         PAD_H - 16 + 6, Q_Y + q_off + q_h],
                        fill=_blend(theme.PRIMARY, q_alpha))

        draw_multiline(draw, q_text,
                       PAD_H + 4, Q_Y + q_off,
                       max_width=TEXT_W - 16,
                       size=44, weight="Bold",
                       color=_blend(theme.TEXT_WHITE, q_alpha),
                       line_spacing=1.35,
                       shadow=True, shadow_offset=2)

    # ── Séparateur ────────────────────────────────────────────────────────────
    sep_prog = ease_out(max(0, (t - 0.45) / 0.3))
    if sep_prog > 0.01:
        sw = int((WIDTH - PAD_H * 2) * sep_prog)
        draw.line([(PAD_H, SEP_Y), (PAD_H + sw, SEP_Y)],
                  fill=_blend(theme.PRIMARY, sep_prog), width=3)

    # ── Choix (chaque ligne slide individuellement depuis la droite) ──────────
    if q_type == "vrai_faux":
        base = _draw_vrai_faux_choices(base, t, CHOICES_TOP)
    else:
        base = _draw_qcm_choices(base, t, choix, CHOICES_TOP)

    draw_progress_bar(base, progress)
    return np.array(base)


def _draw_vrai_faux_choices(base, t, top_y):
    options = [("VRAI", theme.SUCCESS), ("FAUX", theme.DANGER)]
    for i, (label, color) in enumerate(options):
        delay = 0.50 + i * 0.15
        cp    = ease_spring(max(0, (t - delay) / 0.38))
        if cp < 0.02:
            continue
        off  = int(interpolate(WIDTH, 0, cp, 1.0, ease_out))
        cy   = top_y + i * (CHOICE_H + 14)
        base = draw_card(base, PAD_H + off, cy, WIDTH - PAD_H * 2, CHOICE_H,
                         radius=CHOICE_R,
                         fill=tuple(int(c * 0.25) for c in color),
                         alpha=0.92, border_color=color, border_width=3)
        draw = ImageDraw.Draw(base)
        font = _get_font(44, "ExtraBold")
        bb   = draw.textbbox((0, 0), label, font=font)
        lx   = WIDTH // 2 - (bb[2] - bb[0]) // 2 - bb[0] + off
        ly   = cy + CHOICE_H // 2 - (bb[3] - bb[1]) // 2 - bb[1]
        draw.text((lx + 2, ly + 2), label, font=font, fill=(0, 0, 0))
        draw.text((lx, ly), label, font=font, fill=_blend(color, cp))
    return base


def _draw_qcm_choices(base, t, choix, top_y):
    for i, c in enumerate(choix):
        delay = 0.50 + i * 0.18
        cp    = ease_spring(max(0, (t - delay) / 0.38))
        if cp < 0.02:
            continue

        off  = int(interpolate(WIDTH + 60, 0, cp, 1.0, ease_out))
        cy   = top_y + i * (CHOICE_H + 14)
        lcol = _CHOICE_COLOR

        # Fond teinté avec la couleur de la lettre
        card_fill = tuple(int(lcol[j] * 0.18 + theme.BG_DARK[j] * 0.82) for j in range(3))
        base = draw_card(base, PAD_H + off, cy, WIDTH - PAD_H * 2, CHOICE_H,
                         radius=CHOICE_R, fill=card_fill, alpha=0.96,
                         border_color=lcol, border_width=3)
        draw = ImageDraw.Draw(base)

        # Bande couleur à gauche
        bar_x = PAD_H + off
        draw.rounded_rectangle([bar_x, cy, bar_x + 10, cy + CHOICE_H],
                                radius=CHOICE_R, fill=_blend(lcol, cp))

        # Cercle lettre
        circle_cx = bar_x + 10 + 48
        circle_cy = cy + CHOICE_H // 2
        R = 34
        draw.ellipse([circle_cx - R, circle_cy - R,
                       circle_cx + R, circle_cy + R],
                      fill=_blend(lcol, cp))
        # Ombre cercle
        draw.ellipse([circle_cx - R + 2, circle_cy - R + 2,
                       circle_cx + R + 2, circle_cy + R + 2],
                      outline=(0, 0, 0), width=2)
        lf = _get_font(36, "ExtraBold")
        lb = draw.textbbox((0, 0), c["lettre"], font=lf)
        draw.text((circle_cx - (lb[2] - lb[0]) // 2 - lb[0] + 1,
                   circle_cy - (lb[3] - lb[1]) // 2 - lb[1] + 1),
                  c["lettre"], font=lf, fill=(0, 0, 0))
        draw.text((circle_cx - (lb[2] - lb[0]) // 2 - lb[0],
                   circle_cy - (lb[3] - lb[1]) // 2 - lb[1]),
                  c["lettre"], font=lf, fill=theme.TEXT_WHITE)

        # Texte choix avec retour à la ligne
        txt_x     = bar_x + 10 + 48 + R + 18
        max_txt_w = WIDTH - PAD_H - (10 + 48 + R + 18) - 24
        txt_h     = multiline_height(c["texte"], max_txt_w, 42, "Bold", 1.25)
        txt_y     = cy + CHOICE_H // 2 - txt_h // 2
        draw_multiline(draw, c["texte"],
                       txt_x, txt_y,
                       max_width=max_txt_w,
                       size=42, weight="Bold",
                       color=_blend(theme.TEXT_WHITE, cp),
                       line_spacing=1.25, shadow=True, shadow_offset=2)
    return base


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
