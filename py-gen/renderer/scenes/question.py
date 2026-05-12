"""
QUESTION — modern look.

Improvements vs original :
  • image: subtle Ken Burns zoom (1.0 → 1.05 over scene)
  • question card: glassmorphism (blur of bg + frosted overlay)
  • choices: spring scale + slide stagger, badge with separate pop
  • difficulty pill: continuous breath glow
  • watermark: subtle pulse opacity

Layout (top→bottom):
  [image (Ken-Burns crop top half)]   ←  badge + watermark overlay
  [category]
  [question card  — glass]
  [separator]
  [choices A/B/C/...]
"""
import os, math, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import (
    ease_out, ease_out_back, interpolate, pulse, breath, lerp_color,
)
from renderer.elements.background import gradient_overlay_bottom
from renderer.elements.typography import draw_multiline, multiline_height, _get_font
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.image_block import load_image  # noqa: F401
from renderer.elements.progress_bar import draw_progress_bar
from renderer.elements import effects

PAD_H    = 48
TEXT_W   = WIDTH - PAD_H * 2
CHOICE_H = 96
CHOICE_R = 24
GAP      = 20

_DIFF_COLORS = {"facile": theme.SUCCESS, "moyen": theme.WARNING, "difficile": theme.DANGER}
_DIFF_LABELS = {"facile": "FACILE", "moyen": "MOYEN", "difficile": "DIFFICILE"}
_CHOICE_COLOR = theme.PRIMARY


def make_frame(t, video_data, settings, progress=0.0,
               tick_local=None, countdown_dur=3.0):
    """
    `tick_local` : seconds since first tick (0..countdown_dur), or None when
                   the scene is in its question-reading phase.
    `countdown_dur` : total countdown length in seconds (default 3.0).
    """
    q         = video_data["question"]
    q_type    = q.get("type", "vrai_faux")
    choix     = q.get("choix", [])
    q_text    = q["texte"]
    categorie = video_data.get("categorie", "")
    img_path  = _asset(q["media"])

    # ── Image with subtle Ken Burns zoom ─────────────────────────────────────
    MAX_IMG_H = int(HEIGHT * 0.44)
    img_render_w, img_render_h = _image_contain_size(img_path, WIDTH, MAX_IMG_H)
    img_x = (WIDTH - img_render_w) // 2

    img_alpha = ease_out(min(1.0, t / 0.5))
    KB_DUR = 8.0
    try:
        raw = Image.open(img_path).convert("RGB")
        kb_img = effects.ken_burns(
            raw, t, KB_DUR,
            target_w=img_render_w, target_h=img_render_h,
            start_scale=1.0, end_scale=1.06, pan_x=0.0, pan_y=-0.15,
        ).convert("RGBA")
        if img_alpha < 1.0:
            r, g, b, a = kb_img.split()
            a = a.point(lambda p: int(p * img_alpha))
            kb_img = Image.merge("RGBA", (r, g, b, a))
    except Exception:
        kb_img = Image.new("RGBA", (img_render_w, img_render_h), theme.BG_CARD2)

    base = Image.new("RGB", (WIDTH, HEIGHT), theme.BG_DARK)
    base = base.convert("RGBA")
    base.paste(kb_img, (img_x, 0), kb_img)
    base = base.convert("RGB")

    base = gradient_overlay_bottom(
        base, start_y=max(0, img_render_h - 110), color=theme.BG_DARK)
    draw = ImageDraw.Draw(base)

    # ── Difficulty pill (breath) + watermark (opacity pulse) ─────────────────
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

    # ── Layout positions ─────────────────────────────────────────────────────
    CAT_Y = img_render_h + GAP
    cat_h = 52
    Q_Y   = CAT_Y + cat_h + GAP

    has_q = bool(q_text and q_text.strip())
    if has_q:
        q_h = multiline_height(q_text, TEXT_W - 32, 44, "Bold", line_spacing=1.35)
    else:
        q_h = 0
    SEP_Y       = Q_Y + (q_h + GAP if has_q else 0)
    CHOICES_TOP = SEP_Y + GAP + 8

    # ── Category — letter-spaced fade in ─────────────────────────────────────
    cat_prog = ease_out(max(0, (t - 0.15) / 0.35))
    if cat_prog > 0.02 and categorie:
        draw_multiline(draw, "  ".join(categorie.upper()),
                       WIDTH // 2, CAT_Y,
                       max_width=TEXT_W,
                       size=32, weight="SemiBold",
                       color=_blend(theme.PRIMARY, cat_prog),
                       line_spacing=1.2,
                       anchor_x="center", shadow=False)

    # ── Question card : GLASSMORPHISM ────────────────────────────────────────
    if has_q:
        q_prog = ease_out(max(0, (t - 0.20) / 0.5))
        q_off  = int(interpolate(70, 0, q_prog, 1.0, ease_out))
        if q_prog > 0.05:
            card_w = WIDTH - (PAD_H - 16) * 2
            card_h = q_h + 36
            card_x = PAD_H - 16
            card_y = Q_Y + q_off - 12

            base = effects.glass_card(
                base, card_x, card_y, card_w, card_h,
                radius=22, tint=theme.BG_CARD,
                tint_alpha=0.55, blur_radius=18,
                border_alpha=int(110 * q_prog), border_width=2,
            )
            draw = ImageDraw.Draw(base)

            bar_h = q_h
            draw.rectangle(
                [card_x + 14, card_y + 18, card_x + 14 + 6, card_y + 18 + bar_h],
                fill=_blend(theme.PRIMARY, q_prog),
            )

            draw_multiline(draw, q_text,
                           card_x + 36, card_y + 18,
                           max_width=TEXT_W - 32,
                           size=44, weight="Bold",
                           color=_blend(theme.TEXT_WHITE, q_prog),
                           line_spacing=1.35,
                           shadow=True, shadow_offset=2)

    # ── Separator (animated wipe + glow dot) ─────────────────────────────────
    sep_prog = ease_out(max(0, (t - 0.45) / 0.32))
    if sep_prog > 0.01:
        sw = int((WIDTH - PAD_H * 2) * sep_prog)
        draw.line([(PAD_H, SEP_Y), (PAD_H + sw, SEP_Y)],
                  fill=_blend(theme.PRIMARY, sep_prog), width=3)
        if sep_prog > 0.4:
            ds = int(6 * (sep_prog - 0.4) / 0.6)
            if ds > 0:
                cxd = PAD_H + sw - ds
                draw.ellipse([cxd - ds, SEP_Y - ds, cxd + ds, SEP_Y + ds],
                             fill=theme.PRIMARY_LIGHT)

    # ── Choices ──────────────────────────────────────────────────────────────
    if q_type == "vrai_faux":
        base = _draw_vrai_faux_choices(base, t, CHOICES_TOP)
    else:
        base = _draw_qcm_choices(base, t, choix, CHOICES_TOP)

    # ── Countdown widget (bottom-right of image, only during tick phase) ─────
    if tick_local is not None:
        base = _draw_countdown_widget(
            base, tick_local, countdown_dur,
            img_x=img_x, img_w=img_render_w, img_h=img_render_h,
        )

    draw_progress_bar(base, progress)
    return np.array(base)


# ─── countdown widget : compact ring + digit, bottom-right of image ─────────

CD_RADIUS  = 78    # ring outer radius
CD_STROKE  = 12    # ring stroke width
CD_MARGIN  = 24    # margin from image edges
CD_BG_PAD  = 10    # backdrop disc inset under the ring
CD_FONT_SZ = 92    # main digit size


def _draw_countdown_widget(base, tick_t, total_dur, img_x, img_w, img_h):
    """
    Compact circular countdown anchored at bottom-right of the image area.
    Pops in over 0.25s, ring drains across `total_dur` seconds, digit pops
    each integer second, fades out during the last 0.18s.
    """
    cx = img_x + img_w - CD_MARGIN - CD_RADIUS
    cy = img_h         - CD_MARGIN - CD_RADIUS

    # Entry pop + exit fade timing
    entry_dur = 0.25
    exit_dur  = 0.20
    if tick_t < entry_dur:
        scale = ease_out_back(tick_t / entry_dur)
        alpha = min(1.0, tick_t / entry_dur)
    elif tick_t > total_dur - exit_dur:
        et    = (tick_t - (total_dur - exit_dur)) / exit_dur
        scale = 1.0 + 0.30 * et
        alpha = max(0.0, 1.0 - et)
    else:
        scale = 1.0
        alpha = 1.0

    if alpha <= 0.02 or scale <= 0.05:
        return base

    R       = max(8, int(CD_RADIUS * scale))
    bg_R    = R - CD_BG_PAD
    stroke  = max(4, int(CD_STROKE * scale))
    fill_frac = max(0.0, 1.0 - tick_t / total_dur)
    sub_t     = tick_t - math.floor(tick_t)            # 0..1 within current second

    # Per-tick flash on the image (light pulse around the ring)
    flash = max(0.0, 1.0 - sub_t / 0.12) * 0.55 if sub_t < 0.12 else 0.0

    # Glow halo around the ring (breathes + per-tick flash boost)
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    glow_color = lerp_color(theme.PRIMARY, theme.PRIMARY_LIGHT, sub_t)
    glow_amp   = pulse(tick_t, period=1.0, amplitude=0.18, base=1.0)
    for i in range(20, 0, -1):
        rr = int((R + i * 5) * glow_amp)
        a  = int((40 + 90 * flash) * (1 - i / 20) ** 2 * alpha)
        gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                   fill=glow_color + (a,))
    base = Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(base)

    # Backdrop dark disc (so digit reads on any image)
    bd = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(bd).ellipse(
        [cx - bg_R, cy - bg_R, cx + bg_R, cy + bg_R],
        fill=(0, 0, 0, int(180 * alpha)),
    )
    base = Image.alpha_composite(base.convert("RGBA"), bd).convert("RGB")
    draw = ImageDraw.Draw(base)

    # Ring background track
    draw.arc([cx - R, cy - R, cx + R, cy + R],
             start=-90, end=270,
             fill=_blend(theme.BG_CARD2, alpha), width=stroke)

    # Ring fill (drains as time passes)
    if fill_frac > 0.01:
        ring_col = lerp_color(theme.PRIMARY_DARK, theme.PRIMARY_LIGHT, sub_t)
        draw.arc([cx - R, cy - R, cx + R, cy + R],
                 start=-90, end=-90 + 360 * fill_frac,
                 fill=_blend(ring_col, alpha), width=stroke)
        # Tip dot
        ang = math.radians(-90 + 360 * fill_frac)
        tx  = cx + R * math.cos(ang)
        ty  = cy + R * math.sin(ang)
        td  = max(3, int(8 * scale))
        draw.ellipse([tx - td, ty - td, tx + td, ty + td],
                     fill=_blend(theme.PRIMARY_LIGHT, alpha))

    # Digit (1..3) — pop on each second boundary
    second_left = max(1, math.ceil(total_dur - tick_t))
    if sub_t < 0.25:
        digit_scale = ease_out_back(sub_t / 0.25)
    elif sub_t < 0.85:
        digit_scale = 1.0
    else:
        out_p = (sub_t - 0.85) / 0.15
        digit_scale = 1.0 + 0.4 * out_p
    digit_alpha = alpha if sub_t < 0.85 else max(0.0, alpha * (1 - (sub_t - 0.85) / 0.15))
    digit_size  = max(10, int(CD_FONT_SZ * scale * digit_scale))
    if digit_size >= 12 and digit_alpha > 0.05:
        font = _get_font(digit_size, "ExtraBold")
        d2   = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bb   = d2.textbbox((0, 0), str(second_left), font=font)
        dx   = cx - (bb[2] - bb[0]) // 2 - bb[0]
        dy   = cy - (bb[3] - bb[1]) // 2 - bb[1]
        col  = _blend(theme.PRIMARY_LIGHT, digit_alpha)
        # Layered shadow
        for sx, sy in [(3, 4), (1, 2)]:
            draw.text((dx + sx, dy + sy), str(second_left), font=font, fill=(0, 0, 0))
        draw.text((dx, dy), str(second_left), font=font, fill=col)

    return base


def _image_contain_size(path, max_w, max_h):
    try:
        with Image.open(path) as im:
            sw, sh = im.size
    except Exception:
        return max_w, max_h
    scale = min(max_w / sw, max_h / sh)
    return int(sw * scale), int(sh * scale)


def _draw_vrai_faux_choices(base, t, top_y):
    options = [("VRAI", theme.SUCCESS), ("FAUX", theme.DANGER)]
    for i, (label, color) in enumerate(options):
        delay = 0.55 + i * 0.13
        cp    = ease_out_back(max(0, (t - delay) / 0.45))
        if cp < 0.02:
            continue
        off  = int(interpolate(WIDTH, 0, ease_out(min(1.0, cp)), 1.0))
        cy   = top_y + i * (CHOICE_H + 14)

        base = draw_card(base, PAD_H + off, cy, WIDTH - PAD_H * 2, CHOICE_H,
                         radius=CHOICE_R,
                         fill=tuple(int(c * 0.25) for c in color),
                         alpha=0.92, border_color=color, border_width=3)
        draw = ImageDraw.Draw(base)
        font = _get_font(46, "ExtraBold")
        bb   = draw.textbbox((0, 0), label, font=font)
        lx   = WIDTH // 2 - (bb[2] - bb[0]) // 2 - bb[0] + off
        ly   = cy + CHOICE_H // 2 - (bb[3] - bb[1]) // 2 - bb[1]
        draw.text((lx + 2, ly + 2), label, font=font, fill=(0, 0, 0))
        draw.text((lx, ly), label, font=font, fill=_blend(color, min(1.0, cp)))
    return base


def _draw_qcm_choices(base, t, choix, top_y):
    for i, c in enumerate(choix):
        delay = 0.50 + i * 0.13
        cp_card = ease_out(max(0, (t - delay) / 0.42))
        if cp_card < 0.02:
            continue
        off  = int(interpolate(WIDTH + 60, 0, cp_card, 1.0, ease_out))
        cy   = top_y + i * (CHOICE_H + 14)
        lcol = _CHOICE_COLOR

        card_fill = tuple(int(lcol[j] * 0.18 + theme.BG_DARK[j] * 0.82) for j in range(3))
        base = draw_card(base, PAD_H + off, cy, WIDTH - PAD_H * 2, CHOICE_H,
                         radius=CHOICE_R, fill=card_fill, alpha=0.96,
                         border_color=lcol, border_width=3)
        draw = ImageDraw.Draw(base)

        bar_x = PAD_H + off
        draw.rounded_rectangle([bar_x, cy, bar_x + 10, cy + CHOICE_H],
                                radius=CHOICE_R, fill=_blend(lcol, cp_card))

        # Letter circle pop-in spring (delayed after card)
        cp_letter = ease_out_back(max(0, (t - delay - 0.18) / 0.4))
        circle_cx = bar_x + 10 + 48
        circle_cy = cy + CHOICE_H // 2
        R = max(4, int(34 * min(1.05, cp_letter))) if cp_letter > 0.02 else 0
        if R > 4:
            draw.ellipse([circle_cx - R, circle_cy - R,
                           circle_cx + R, circle_cy + R],
                          fill=_blend(lcol, min(1.0, cp_letter)))
            lf = _get_font(int(36 * min(1.05, cp_letter)), "ExtraBold")
            lb = draw.textbbox((0, 0), c["lettre"], font=lf)
            draw.text((circle_cx - (lb[2] - lb[0]) // 2 - lb[0] + 1,
                       circle_cy - (lb[3] - lb[1]) // 2 - lb[1] + 1),
                      c["lettre"], font=lf, fill=(0, 0, 0))
            draw.text((circle_cx - (lb[2] - lb[0]) // 2 - lb[0],
                       circle_cy - (lb[3] - lb[1]) // 2 - lb[1]),
                      c["lettre"], font=lf, fill=theme.TEXT_WHITE)

        cp_text = ease_out(max(0, (t - delay - 0.12) / 0.45))
        txt_x     = bar_x + 10 + 48 + 34 + 18
        max_txt_w = WIDTH - PAD_H - (10 + 48 + 34 + 18) - 24
        txt_h     = multiline_height(c["texte"], max_txt_w, 42, "Bold", 1.25)
        txt_y     = cy + CHOICE_H // 2 - txt_h // 2
        draw_multiline(draw, c["texte"],
                       txt_x, txt_y,
                       max_width=max_txt_w,
                       size=42, weight="Bold",
                       color=_blend(theme.TEXT_WHITE, cp_text),
                       line_spacing=1.25, shadow=True, shadow_offset=2)
    return base


def _asset(rel):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     rel.lstrip("./")))

def _blend(color, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
