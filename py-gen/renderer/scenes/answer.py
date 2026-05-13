"""
ANSWER — climax scene.

Modern look :
  • initial whiteout flash (0.15s) for impact
  • rotating burst rays (12 rays) tinted SUCCESS/DANGER
  • confetti for SUCCESS, screen shake for DANGER
  • label : kinetic typography per-char + scale spring
  • icon : drawn with stroke animation
  • barred bad choices : line draws left-to-right (scribble)
  • continuous pulse glow behind label
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
import theme
from renderer.animations import (
    ease_spring, ease_out, ease_out_back, ease_in, ease_in_out,
    interpolate, pulse, shake,
)
from renderer.elements.background import radial_gradient
from renderer.elements.typography import (
    _get_font, draw_kinetic_text, _wrap_lines, _text_length_mixed,
)
from renderer.elements.progress_bar import draw_progress_bar
from renderer.elements import effects

CX       = WIDTH  // 2
GROUP_CY = int(HEIGHT * 0.42)


def make_frame(t, video_data, settings, progress=0.0):
    q       = video_data["question"]
    q_type  = q.get("type", "vrai_faux")
    choix   = q.get("choix", [])
    reponse = video_data["reponse"]

    if q_type == "vrai_faux":
        is_correct_color = reponse.upper() == "VRAI"
    else:
        is_correct_color = True

    accent = theme.SUCCESS if is_correct_color else theme.DANGER
    edge   = (5, 50, 40) if is_correct_color else (50, 5, 5)

    # Radial gradient background
    base = radial_gradient(
        center_color=tuple(int(c * 0.55) for c in accent),
        edge_color=edge,
        cx=CX, cy=GROUP_CY,
        radius=max(WIDTH, HEIGHT) * 0.95,
    )

    # ── Rotating burst rays (slow rotation) ──────────────────────────────────
    if t > 0.05:
        ray_rotation = t * 0.35   # rad/s
        rays_alpha   = int(min(1.0, (t - 0.05) / 0.4) * 110)
        base = effects.burst_rays(
            base, CX, GROUP_CY,
            radius=int(max(WIDTH, HEIGHT) * 0.7),
            n_rays=12, color=accent,
            alpha=rays_alpha, ray_width=80,
            rotation=ray_rotation,
        )

    # ── Glow particles around center (existing effect, kept) ─────────────────
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    glow_breath = pulse(t, period=1.2, amplitude=0.1, base=1.0)
    for cx2, cy2, r2, a2 in [
        (CX, GROUP_CY, int(360 * glow_breath), 45),
        (CX - 200, GROUP_CY + 200, 180, 18),
        (CX + 220, GROUP_CY - 150, 160, 15),
    ]:
        for i in range(r2, 0, -10):
            alpha = int(a2 * (1 - i / r2))
            gd.ellipse([cx2 - i, cy2 - i, cx2 + i, cy2 + i],
                       fill=accent + (alpha,))
    base = Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(base)

    # ── Draw the answer content ──────────────────────────────────────────────
    if q_type == "vrai_faux":
        base = _draw_vrai_faux(base, t, reponse, accent, is_correct_color)
    else:
        base = _draw_qcm(base, t, reponse, choix, accent)

    # ── Confetti burst for correct answers ───────────────────────────────────
    if is_correct_color and t > 0.25:
        base = effects.confetti_burst(
            base, t - 0.25, cx=CX, cy=GROUP_CY,
            n=46, gravity=1900, life=2.6, seed=11,
        )

    # ── Screen shake on wrong answer ─────────────────────────────────────────
    if not is_correct_color:
        dx, dy = shake(t, duration=0.45, amplitude=14, frequency=28)
        if dx or dy:
            base = effects.shift_image(base, dx, dy, fill=theme.BG_DARK)

    # ── Initial whiteout flash (peaks at t=0.06) ─────────────────────────────
    if t < 0.18:
        intensity = max(0, 1 - abs(t - 0.06) / 0.12) * 0.65
        base = effects.flash_overlay(base, intensity)

    draw_progress_bar(base, progress)
    return np.array(base)


def _draw_vrai_faux(base, t, reponse, accent, is_vrai):
    """Big VRAI/FAUX label + animated check/cross icon."""
    label = reponse.upper()
    draw  = ImageDraw.Draw(base)

    # ── Icon (check/cross) — stroke-draw progressively ───────────────────────
    icon_p   = ease_out(min(1.0, max(0, (t - 0.05) / 0.45)))
    icon_size = int(150 * ease_out_back(min(1.0, max(0, (t - 0.05) / 0.5))))
    icon_cy   = GROUP_CY - 130
    if icon_size > 8 and icon_p > 0.05:
        _draw_animated_icon(draw, CX, icon_cy, is_vrai, theme.TEXT_WHITE,
                            icon_size, progress=icon_p)

    # ── Label : kinetic typography + scale ───────────────────────────────────
    label_p = ease_out_back(min(1.0, max(0, (t - 0.18)) / 0.55))
    if label_p > 0.05:
        # The kinetic text already does fade+slide per char ; we can just call it
        size = int(180 * min(1.05, label_p))
        if size >= 12:
            label_y = GROUP_CY + 30
            # Glow background pulse behind label
            base = _label_glow(base, label_y + size // 2, accent, t)
            draw = ImageDraw.Draw(base)
            draw_kinetic_text(
                draw, label,
                x=CX, y=label_y,
                size=size, weight="ExtraBold",
                color=theme.TEXT_WHITE, anchor="mt",
                t=t, base_delay=0.18, char_stagger=0.06,
                char_duration=0.5, slide_distance=28,
                shadow=True, shadow_offset=6,
            )
    return base


def _draw_qcm(base, t, reponse, choix, accent):
    # ── "RÉPONSE" pill (UX E : pill PRIMARY plus gros) ───────────────────────
    label_a = ease_out_back(min(1.0, t / 0.4))
    if label_a > 0.05:
        from renderer.elements.card import draw_pill
        pad_x = int(36 * min(1.05, label_a))
        pad_y = int(16 * min(1.05, label_a))
        ly    = GROUP_CY - 260
        # Aura sous la pill (#3)
        if label_a > 0.3:
            aura_a = int(120 * min(1.0, (label_a - 0.3) / 0.7))
            base = effects.aura_behind(base,
                                       CX - 200, ly - 50, 400, 100,
                                       color=theme.PRIMARY, blur_radius=55,
                                       alpha=aura_a, padding=50)
        base = draw_pill(base, CX, ly, "RÉPONSE", theme.PRIMARY,
                          font_size=int(40 * min(1.05, label_a)),
                          font_weight="ExtraBold",
                          pad_x=pad_x, pad_y=pad_y,
                          text_color=theme.BG_DARK)
    draw = ImageDraw.Draw(base)

    # ── Big answer text : kinetic + glow ─────────────────────────────────────
    ans_p = ease_out_back(min(1.0, max(0, (t - 0.1)) / 0.55))
    ans_y = GROUP_CY - 180
    max_w = WIDTH - 80

    # Auto-shrink to fit one line; wrap to multi-line if even the smallest
    # size doesn't fit. Sizes are picked from a small ladder.
    chosen_size = None
    for sz in (100, 90, 80, 72, 64):
        if _text_length_mixed(reponse, sz, "ExtraBold") <= max_w:
            chosen_size = sz
            break
    if chosen_size is None:
        chosen_size = 64
        ans_lines = _wrap_lines(reponse, max_w, chosen_size, "ExtraBold")
    else:
        ans_lines = [reponse]

    asize = int(chosen_size * min(1.05, ans_p))
    line_h_ans = int(asize * 1.15)
    extra_ans_h = (len(ans_lines) - 1) * line_h_ans

    if asize >= 12:
        glow_y = ans_y + (len(ans_lines) * line_h_ans) // 2
        base = _label_glow(base, glow_y, accent, t)
        draw = ImageDraw.Draw(base)
        delay = 0.10
        for li, line in enumerate(ans_lines):
            line_y = ans_y + li * line_h_ans
            draw_kinetic_text(
                draw, line,
                x=CX, y=line_y,
                size=asize, weight="ExtraBold",
                color=theme.TEXT_WHITE, anchor="mt",
                t=t, base_delay=delay, char_stagger=0.045,
                char_duration=0.55, slide_distance=24,
                shadow=True, shadow_offset=5,
            )
            delay += len(line) * 0.045

    # ── Bad choices : strike-through that draws left→right ───────────────────
    bad_choix = [c for c in choix if not reponse.startswith(c["lettre"])]
    bad_size  = 40
    bad_line_h = 50
    bad_gap    = 40
    y_cursor   = GROUP_CY + 80 + extra_ans_h
    for i, c in enumerate(bad_choix):
        bp_card = ease_out(max(0, (t - 0.55 - i * 0.18) / 0.32))
        label   = f"{c['lettre']} - {c['texte']}"
        lines   = _wrap_lines(label, max_w, bad_size, "SemiBold")
        if bp_card < 0.02:
            y_cursor += len(lines) * bad_line_h + bad_gap
            continue
        font    = _get_font(bad_size, "SemiBold")
        d2      = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        col     = _blend(theme.TEXT_MEDIUM, bp_card * 0.6)
        bp_line = ease_in_out(max(0, (t - 0.55 - i * 0.18 - 0.15) / 0.35))

        for li, ln in enumerate(lines):
            bb = d2.textbbox((0, 0), ln, font=font)
            lw = bb[2] - bb[0]
            lh = bb[3] - bb[1]
            lx = CX - lw // 2 - bb[0]
            ly = y_cursor + li * bad_line_h
            draw.text((lx, ly), ln, font=font, fill=col)
            if bp_line > 0.02:
                mid_y  = ly + lh // 2
                line_w = int((lw + 8) * bp_line)
                draw.line([(lx - 4, mid_y), (lx - 4 + line_w, mid_y)],
                          fill=theme.DANGER, width=5)

        y_cursor += len(lines) * bad_line_h + bad_gap
    return base


def _label_glow(base, cy, color, t):
    """Pulsing horizontal glow behind a big label."""
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    breath_amp = pulse(t, period=1.2, amplitude=0.15, base=1.0)
    for i in range(40, 0, -2):
        ry = int(50 * i / 40)
        rx = int(380 * (i / 40) * breath_amp)
        a  = int(45 * (1 - i / 40) ** 2)
        gd.ellipse([CX - rx, cy - ry, CX + rx, cy + ry],
                   fill=color + (a,))
    base = Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")
    return base


def _draw_animated_icon(draw, cx, cy, is_vrai, color, size, progress=1.0):
    """
    Stroke-draw animation : the check/cross is drawn progressively
    (0 = nothing, 1 = complete).
    """
    h  = size // 2
    th = max(10, size // 8)
    if is_vrai:
        # Check mark : two segments drawn sequentially
        pts = [(cx - h * 0.55, cy + h * 0.05),
               (cx - h * 0.05, cy + h * 0.55),
               (cx + h * 0.60, cy - h * 0.55)]
        seg1_total = math.dist(pts[0], pts[1])
        seg2_total = math.dist(pts[1], pts[2])
        full_total = seg1_total + seg2_total
        drawn = full_total * progress
        if drawn > 0:
            if drawn <= seg1_total:
                # Partial segment 1
                ratio = drawn / seg1_total
                end_pt = (pts[0][0] + (pts[1][0] - pts[0][0]) * ratio,
                          pts[0][1] + (pts[1][1] - pts[0][1]) * ratio)
                draw.line([pts[0], end_pt], fill=color, width=th)
            else:
                # Full segment 1 + partial segment 2
                draw.line([pts[0], pts[1]], fill=color, width=th)
                ratio = (drawn - seg1_total) / seg2_total
                end_pt = (pts[1][0] + (pts[2][0] - pts[1][0]) * ratio,
                          pts[1][1] + (pts[2][1] - pts[1][1]) * ratio)
                draw.line([pts[1], end_pt], fill=color, width=th)
    else:
        # Cross : two diagonals drawn sequentially
        a1 = (cx - h * 0.62, cy - h * 0.62)
        a2 = (cx + h * 0.62, cy + h * 0.62)
        b1 = (cx + h * 0.62, cy - h * 0.62)
        b2 = (cx - h * 0.62, cy + h * 0.62)
        if progress < 0.5:
            # First diagonal partial
            ratio = progress / 0.5
            end = (a1[0] + (a2[0] - a1[0]) * ratio,
                   a1[1] + (a2[1] - a1[1]) * ratio)
            draw.line([a1, end], fill=color, width=th)
        else:
            draw.line([a1, a2], fill=color, width=th)
            ratio = (progress - 0.5) / 0.5
            end = (b1[0] + (b2[0] - b1[0]) * ratio,
                   b1[1] + (b2[1] - b1[1]) * ratio)
            draw.line([b1, end], fill=color, width=th)


def _blend(color, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
