"""
EXPLANATION — modern look.

  • image with Ken Burns slow zoom
  • title : kinetic typography
  • points : left bar grows from top, then text fades + slides
  • bottom badge : pulse glow, scale-bounce in
  • category : letter-spaced fade
"""
import os, re, numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT, ORIENTATION
import theme
from renderer.animations import (
    ease_out, ease_out_back, interpolate, pulse,
)
from renderer.elements.background import brand_bg_animated, gradient_overlay_bottom
from renderer.elements.typography import (
    draw_text, draw_multiline, multiline_height, _get_font, draw_kinetic_text,
    _wrap_lines,
)
from renderer.elements.card import draw_card, draw_pill
from renderer.elements.image_block import blur_backdrop, contain_dims
from renderer.elements.progress_bar import draw_progress_bar
from renderer.elements import effects

GAP     = theme.SPACE["lg"]
SIDE_W  = theme.SPACE["sm"]
PT_FONT = theme.TEXT_SIZE["lg"]
PAD_L   = theme.SPACE["3xl"]


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

    base = brand_bg_animated(t)

    # ── Compute layout regions based on orientation ──────────────────────────
    img_path = _asset(expl["media"])
    if ORIENTATION == "landscape":
        img_render_w = WIDTH // 2
        img_render_h = HEIGHT
        img_x        = 0
        content_x    = WIDTH // 2 + 36
        content_w    = WIDTH // 2 - 72
        content_top  = 48
        title_size   = 44
        pad_l_local  = content_x + 22
    else:
        MAX_IMG_H = int(HEIGHT * 0.42)
        img_render_w, img_render_h = _image_contain_size(img_path, WIDTH, MAX_IMG_H)
        img_x        = (WIDTH - img_render_w) // 2
        content_x    = 0
        content_w    = WIDTH
        content_top  = img_render_h + GAP
        title_size   = 52
        pad_l_local  = PAD_L
    img_a = ease_out(min(1.0, t / 0.5))

    # ── Image : Ken Burns slow zoom ──────────────────────────────────────────
    KB_DUR = 10.0
    base = base.convert("RGBA")

    if ORIENTATION == "landscape":
        bd = blur_backdrop(img_path, img_render_w, img_render_h)
        base.paste(bd.convert("RGBA"), (img_x, 0))

        fg_w, fg_h = contain_dims(img_path, img_render_w, img_render_h)
        try:
            raw = Image.open(img_path).convert("RGB")
            fg = effects.ken_burns(
                raw, t, KB_DUR,
                target_w=fg_w, target_h=fg_h,
                start_scale=1.0, end_scale=1.07, pan_x=0.08, pan_y=-0.08,
            ).convert("RGBA")
            if img_a < 1.0:
                r, g, b, a = fg.split()
                a = a.point(lambda p: int(p * img_a))
                fg = Image.merge("RGBA", (r, g, b, a))
        except Exception:
            fg = Image.new("RGBA", (fg_w, fg_h), theme.BG_CARD2)

        fx = img_x + (img_render_w - fg_w) // 2
        fy = (img_render_h - fg_h) // 2
        base.paste(fg, (fx, fy), fg)
    else:
        try:
            raw = Image.open(img_path).convert("RGB")
            kb_img = effects.ken_burns(
                raw, t, KB_DUR,
                target_w=img_render_w, target_h=img_render_h,
                start_scale=1.0, end_scale=1.07, pan_x=0.10, pan_y=-0.10,
            ).convert("RGBA")
            if img_a < 1.0:
                r, g, b, a = kb_img.split()
                a = a.point(lambda p: int(p * img_a))
                kb_img = Image.merge("RGBA", (r, g, b, a))
        except Exception:
            kb_img = Image.new("RGBA", (img_render_w, img_render_h), theme.BG_CARD2)
        base.paste(kb_img, (img_x, 0), kb_img)
    base = base.convert("RGB")

    if ORIENTATION == "landscape":
        # Soft vertical seam between image and content
        base = base.convert("RGBA")
        seam = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        sd   = ImageDraw.Draw(seam)
        for dx in range(60):
            a = int(180 * (1 - dx / 60) ** 1.5)
            sd.line([(img_render_w + dx, 0), (img_render_w + dx, HEIGHT)],
                    fill=theme.BG_DARK + (a,))
        base = Image.alpha_composite(base, seam).convert("RGB")
    else:
        base = gradient_overlay_bottom(base, start_y=max(0, img_render_h - 100), color=theme.BG_DARK)
    draw = ImageDraw.Draw(base)

    # ── Difficulty badge — watermark removed (UX A) ──────────────────────────
    WMK_H  = 56
    WMK_CY = 20 + WMK_H // 2
    diff   = video_data.get("difficulty", "facile")
    diff_t = theme.DIFFICULTY.get(diff, theme.DIFFICULTY["facile"])
    dcol, dlbl = diff_t["color"], diff_t["label"]
    pad_x  = int(theme.LAYOUT["pill_pad_x"] * pulse(t, period=2.0, amplitude=0.04))
    base   = draw_pill(base, 88, WMK_CY, dlbl, dcol,
                       font_size=theme.TEXT_SIZE["sm"], font_weight=theme.WEIGHT["bold"],
                       pad_x=pad_x, pad_y=theme.LAYOUT["pill_pad_y"])
    draw = ImageDraw.Draw(base)

    # Sep line below image — animated wipe + glow dot (portrait only)
    if ORIENTATION != "landscape":
        sep_p = ease_out(min(1.0, t / 0.5))
        if sep_p > 0.01:
            sw = int(WIDTH * sep_p)
            draw.line([(0, img_render_h), (sw, img_render_h)],
                      fill=theme.ACCENT, width=2)

    # ── Layout positions ─────────────────────────────────────────────────────
    CAT_Y   = content_top
    cat_h   = 40
    TITLE_Y = CAT_Y + cat_h + GAP
    cat_cx  = content_x + content_w // 2 if ORIENTATION == "landscape" else WIDTH // 2

    # ── Category — real letter-spacing (UX B) ────────────────────────────────
    cat_prog = ease_out(min(1.0, t / 0.35))
    if cat_prog > 0.02 and categorie:
        from renderer.elements.typography import draw_letter_spaced
        draw_letter_spaced(draw, categorie.upper(),
                           x=cat_cx, y=CAT_Y,
                           size=theme.TEXT_SIZE["base"] - 2, weight=theme.WEIGHT["semibold"],
                           color=_blend(theme.PRIMARY, cat_prog),
                           anchor="mt", tracking=7, shadow=False)

    # ── Title : kinetic per-char ─────────────────────────────────────────────
    title_txt = expl.get("titre", "")
    title_max_w = content_w - 16 if ORIENTATION == "landscape" else WIDTH - 80
    title_h   = multiline_height(title_txt, title_max_w, title_size, "ExtraBold", 1.3)
    if title_txt:
        draw_kinetic_text(
            draw, title_txt,
            x=cat_cx, y=TITLE_Y,
            size=title_size, weight="ExtraBold",
            color=theme.PRIMARY, anchor="mt",
            t=t, base_delay=0.20, char_stagger=0.025,
            char_duration=0.5, slide_distance=22,
            shadow=True, shadow_offset=3,
        )

    # ── Bonne réponse block : compute its height (sits above the badge) ─────
    reponse       = video_data.get("reponse", "")
    BR_PILL_H     = 46
    BR_GAP_INNER  = 12
    BR_GAP_BELOW  = 22    # gap entre le bloc bonne réponse et le badge
    BR_GAP_ABOVE  = GAP   # gap entre les points et le bloc bonne réponse
    BR_TEXT_W     = content_w - 16 if ORIENTATION == "landscape" else WIDTH - 80
    br_text_size  = 32 if ORIENTATION == "landscape" else 40
    br_lines      = []
    br_line_h     = int(br_text_size * 1.25)
    br_block_h    = 0
    if reponse:
        br_lines = _wrap_lines(reponse, BR_TEXT_W, br_text_size, "ExtraBold")
        while len(br_lines) > 2 and br_text_size > 24:
            br_text_size -= 2
            br_lines = _wrap_lines(reponse, BR_TEXT_W, br_text_size, "ExtraBold")
        br_line_h  = int(br_text_size * 1.25)
        br_text_h  = len(br_lines) * br_line_h
        br_block_h = BR_PILL_H + BR_GAP_INNER + br_text_h

    # ── Points : auto-fit (UX D) — shrink font until tout rentre au-dessus du badge ──
    points_top = TITLE_Y + title_h + GAP
    points     = expl.get("points", [])[:4]
    if ORIENTATION == "landscape":
        MAX_TXT_W = content_w - 36
        BADGE_H_FOR_RES = 72
        BOTTOM_MARGIN = 36
    else:
        MAX_TXT_W = WIDTH - PAD_L - 36
        BADGE_H_FOR_RES = 90
        BOTTOM_MARGIN = 56
    BADGE_RES  = BADGE_H_FOR_RES + BOTTOM_MARGIN + 24    # badge h + bottom margin + safety
    if br_block_h:
        BADGE_RES += br_block_h + BR_GAP_ABOVE + BR_GAP_BELOW
    avail_h    = HEIGHT - points_top - BADGE_RES

    pt_font = PT_FONT
    line_sp = 1.35
    min_pt_font = 24 if ORIENTATION == "landscape" else 30
    while pt_font >= min_pt_font:
        heights = [
            multiline_height(_strip_emoji(p["texte"]), MAX_TXT_W,
                             pt_font, theme.WEIGHT["semibold"], line_sp)
            for p in points
        ]
        total = sum(heights) + GAP * max(0, len(heights) - 1)
        if total <= avail_h:
            break
        pt_font -= 2

    cursor_y = points_top
    for i, pt in enumerate(points):
        delay  = 0.55 + i * 0.20
        bar_p  = ease_out(max(0, (t - delay) / 0.32))
        text_p = ease_out(max(0, (t - delay - 0.10) / 0.36))
        txt    = _strip_emoji(pt["texte"])
        pt_h   = heights[i]

        if bar_p > 0.02:
            bar_drawn = int(pt_h * bar_p)
            draw.rectangle(
                [pad_l_local - 22, cursor_y,
                 pad_l_local - 22 + SIDE_W, cursor_y + bar_drawn],
                fill=_blend(theme.PRIMARY, bar_p),
            )

        if text_p > 0.02:
            off = int(interpolate(-90, 0, text_p, 1.0, ease_out))
            col = _blend(theme.TEXT_WHITE, text_p)
            draw_multiline(draw, txt,
                           pad_l_local + off, cursor_y,
                           max_width=MAX_TXT_W,
                           size=pt_font, weight=theme.WEIGHT["semibold"],
                           color=col, line_spacing=line_sp, shadow=False)

        cursor_y += pt_h + GAP

    # ── Bottom badge geometry (needed for bonne réponse anchoring) ──────────
    BADGE_H        = BADGE_H_FOR_RES
    badge_y0       = HEIGHT - BOTTOM_MARGIN - BADGE_H
    badge_card_pad = 28 if ORIENTATION != "landscape" else (content_x - 14)
    badge_card_w   = WIDTH - 56 if ORIENTATION != "landscape" else content_w + 28

    # ── Bonne réponse : pill + texte centré, anim slide-up bounce ────────────
    if br_block_h:
        block_top   = badge_y0 - BR_GAP_BELOW - br_block_h
        br_prog     = ease_out_back(max(0, (t - 1.05) / 0.50))
        if br_prog > 0.05:
            alpha    = min(1.0, br_prog)
            slide_y  = int(interpolate(40, 0, min(1.0, br_prog), 1.0, ease_out))
            block_top_anim = block_top + slide_y

            pill_cy = block_top_anim + BR_PILL_H // 2
            base = draw_pill(
                base, cat_cx, pill_cy, "BONNE RÉPONSE",
                theme.SUCCESS,
                font_size=22 if ORIENTATION == "landscape" else 24,
                font_weight="ExtraBold",
                pad_x=20 if ORIENTATION == "landscape" else 22,
                pad_y=9 if ORIENTATION == "landscape" else 10,
                text_color=theme.BG_DARK,
            )
            draw = ImageDraw.Draw(base)

            font_br = _get_font(br_text_size, "ExtraBold")
            d_dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            col_br  = _blend(theme.TEXT_WHITE, alpha)
            text_top = block_top_anim + BR_PILL_H + BR_GAP_INNER
            for li, ln in enumerate(br_lines):
                bb = d_dummy.textbbox((0, 0), ln, font=font_br)
                lw = bb[2] - bb[0]
                lx = cat_cx - lw // 2 - bb[0]
                ly = text_top + li * br_line_h
                draw.text((lx + 2, ly + 2), ln, font=font_br, fill=(0, 0, 0))
                draw.text((lx, ly), ln, font=font_br, fill=col_br)

    # ── Bottom badge : bounce + pulse glow ───────────────────────────────────
    badge_prog = ease_out_back(max(0, (t - 1.20) / 0.45))
    if badge_prog > 0.05:
        badge = expl.get("badge", {})
        btype = badge.get("type", "warning")
        BCOL  = {"danger": theme.DANGER, "warning": theme.WARNING, "success": theme.SUCCESS}
        bcol  = BCOL.get(btype, theme.WARNING)
        btxt  = _strip_emoji(badge.get("texte", ""))
        # Slide-up + slight overshoot
        by    = int(interpolate(HEIGHT, badge_y0, min(1.0, badge_prog), 1.0))

        # Continuous pulse glow under it
        if badge_prog > 0.7:
            glow_amp = pulse(t - 1.2, period=1.6, amplitude=0.15, base=1.0)
            gl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            gd = ImageDraw.Draw(gl)
            for i in range(20, 0, -1):
                ry = int(40 * i / 20 * glow_amp)
                rx = int((badge_card_w // 2 + 30) * (i / 20) * glow_amp)
                a  = int(40 * (1 - i / 20) ** 2)
                gd.ellipse([cat_cx - rx, by + BADGE_H // 2 - ry,
                            cat_cx + rx, by + BADGE_H // 2 + ry],
                           fill=bcol + (a,))
            base = Image.alpha_composite(base.convert("RGBA"), gl).convert("RGB")

        base = draw_card(base, badge_card_pad, by, badge_card_w, BADGE_H,
                         radius=24, fill=bcol, alpha=0.95)
        draw = ImageDraw.Draw(base)
        if btxt:
            font = _get_font(34 if ORIENTATION == "landscape" else 42, "ExtraBold")
            bb   = draw.textbbox((0, 0), btxt, font=font)
            bx   = cat_cx - (bb[2] - bb[0]) // 2 - bb[0]
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
    a = max(0.0, min(1.0, a))
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
