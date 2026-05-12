"""
Visual effects — modern look additions.

  • glassmorphism     — frosted glass card with blur + tinted overlay
  • grain_overlay     — film grain noise over a frame
  • vignette          — corner darkening
  • burst_rays        — radial light rays from a point
  • confetti_particles — gravity-driven coloured squares
  • floating_particles — slow-drift dots upwards (intro/outro)
  • flash_overlay     — full-frame white flash
  • scale_image       — scale a PIL image around its center
  • shake_offset      — wrapper around animations.shake (kept here for cohesion)
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

import theme
from config import WIDTH, HEIGHT


# ─────────────────────────── glassmorphism ──────────────────────────────────

def glass_card(base_img, x, y, w, h, radius=24,
               tint=None, tint_alpha=0.45, blur_radius=22,
               border_alpha=70, border_width=2):
    """
    Composite a frosted-glass card onto base_img:
      1. crop the region
      2. blur it
      3. overlay a tinted translucent rectangle
      4. add a thin highlight border
    Returns a new PIL RGB Image.
    """
    tint = tint or theme.BG_CARD
    base = base_img.convert("RGBA")
    region = base.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(blur_radius))

    # Tint layer
    overlay = Image.new("RGBA", (w, h), tint + (int(tint_alpha * 255),))
    blurred = Image.alpha_composite(region.convert("RGBA"), overlay)

    # Rounded mask
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)

    # Highlight border
    bd = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(bd).rounded_rectangle(
        [border_width // 2, border_width // 2,
         w - 1 - border_width // 2, h - 1 - border_width // 2],
        radius=radius, outline=(255, 255, 255, border_alpha), width=border_width)
    blurred = Image.alpha_composite(blurred, bd)

    # Punch through rounded mask
    final = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    final.paste(blurred, (0, 0), mask)

    base.paste(final, (x, y), final)
    return base.convert("RGB")


# ─────────────────────────── grain (cinema feel) ────────────────────────────

_GRAIN_CACHE = None


def _grain_tile(size=512, strength=14, seed=42):
    rng = np.random.default_rng(seed)
    noise = rng.integers(-strength, strength + 1, size=(size, size), dtype=np.int16)
    return noise


def grain_overlay(img, strength=8, seed=None):
    """
    Add film grain to the frame. Cheap: tiles a single noise pattern.
    seed=None → varies per call (animated grain).
    """
    arr = np.asarray(img, dtype=np.int16)
    h, w = arr.shape[:2]
    seed_val = seed if seed is not None else random.randint(0, 1_000_000)
    tile = _grain_tile(size=512, strength=strength, seed=seed_val)
    # Tile to full size
    reps_y = (h + tile.shape[0] - 1) // tile.shape[0]
    reps_x = (w + tile.shape[1] - 1) // tile.shape[1]
    big = np.tile(tile, (reps_y, reps_x))[:h, :w]
    arr[:, :, 0] = np.clip(arr[:, :, 0] + big, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + big, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] + big, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


# ─────────────────────────── vignette ───────────────────────────────────────

_VIGNETTE_CACHE = None


def vignette(img, strength=0.55, falloff=1.4):
    """
    Darken corners. strength = max darkness factor at corners (0 = none).
    """
    global _VIGNETTE_CACHE
    h, w = img.size[1], img.size[0]
    key = (w, h, strength, falloff)
    if _VIGNETTE_CACHE is None or _VIGNETTE_CACHE[0] != key:
        Y, X = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        max_d = math.sqrt(cx * cx + cy * cy)
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / max_d
        mask = 1.0 - strength * np.clip(d ** falloff, 0, 1)
        _VIGNETTE_CACHE = (key, mask.astype(np.float32))
    mask = _VIGNETTE_CACHE[1]
    arr = np.asarray(img, dtype=np.float32)
    arr[:, :, 0] *= mask
    arr[:, :, 1] *= mask
    arr[:, :, 2] *= mask
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# ─────────────────────────── burst rays ─────────────────────────────────────

def burst_rays(img, cx, cy, radius, n_rays=12, color=None,
               alpha=120, ray_width=22, rotation=0.0):
    """
    Draw radial light rays from (cx, cy). Returns RGB image.
    `rotation` in radians — animate this to spin the rays.
    """
    color = color or theme.PRIMARY
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    inner_r = int(radius * 0.18)
    for i in range(n_rays):
        ang = rotation + 2 * math.pi * i / n_rays
        # Triangle ray
        tip_x = cx + radius * math.cos(ang)
        tip_y = cy + radius * math.sin(ang)
        # Base of triangle perpendicular to ray
        perp = ang + math.pi / 2
        bx1 = cx + inner_r * math.cos(ang) + (ray_width / 2) * math.cos(perp)
        by1 = cy + inner_r * math.sin(ang) + (ray_width / 2) * math.sin(perp)
        bx2 = cx + inner_r * math.cos(ang) - (ray_width / 2) * math.cos(perp)
        by2 = cy + inner_r * math.sin(ang) - (ray_width / 2) * math.sin(perp)
        d.polygon([(tip_x, tip_y), (bx1, by1), (bx2, by2)],
                  fill=color + (alpha,))
    overlay = overlay.filter(ImageFilter.GaussianBlur(2))
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    return base.convert("RGB")


# ─────────────────────────── confetti / particles ───────────────────────────

def _seeded_confetti(n, cx, cy, seed=7):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        ang = rng.uniform(-math.pi, 0)        # upward burst
        spd = rng.uniform(550, 1100)
        vx  = math.cos(ang) * spd
        vy  = math.sin(ang) * spd
        size = rng.randint(10, 22)
        rot_speed = rng.uniform(-720, 720)    # deg/s
        rot0 = rng.uniform(0, 360)
        col_choice = rng.choice([
            theme.PRIMARY, theme.PRIMARY_LIGHT, theme.WARNING,
            theme.SUCCESS, (255, 255, 255), theme.ACCENT,
        ])
        parts.append({
            "x0": cx, "y0": cy, "vx": vx, "vy": vy,
            "size": size, "rot_speed": rot_speed, "rot0": rot0,
            "color": col_choice,
        })
    return parts


def confetti_burst(img, t, cx, cy, n=44, gravity=1800, life=2.5, seed=7):
    """
    Draw confetti at time `t` (seconds since burst).
    Particles launch upward from (cx, cy) with random velocities.
    """
    if t <= 0 or t >= life:
        return img
    parts = _seeded_confetti(n, cx, cy, seed=seed)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    fade = max(0.0, 1 - (t / life) ** 1.5)
    alpha = int(255 * fade)
    for p in parts:
        x = p["x0"] + p["vx"] * t
        y = p["y0"] + p["vy"] * t + 0.5 * gravity * t * t
        if y > img.size[1] + 80 or x < -80 or x > img.size[0] + 80:
            continue
        rot = math.radians(p["rot0"] + p["rot_speed"] * t)
        s = p["size"] / 2
        cos_r, sin_r = math.cos(rot), math.sin(rot)
        pts = [(-s, -s), (s, -s), (s, s), (-s, s)]
        rotated = [(x + px * cos_r - py * sin_r,
                    y + px * sin_r + py * cos_r) for px, py in pts]
        d.polygon(rotated, fill=p["color"] + (alpha,))
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    return base.convert("RGB")


def floating_particles(img, t, n=18, color=None, seed=13,
                       speed=22, size_range=(3, 7), alpha=70):
    """
    Slow-drifting upward particles for ambient backgrounds (intro/outro).
    """
    color = color or theme.PRIMARY_LIGHT
    rng = random.Random(seed)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    h, w = img.size[1], img.size[0]
    for i in range(n):
        x0 = rng.uniform(0, w)
        y0 = rng.uniform(0, h)
        spd = speed * rng.uniform(0.6, 1.4)
        amp = rng.uniform(15, 50)
        period = rng.uniform(2.5, 5.0)
        sz = rng.randint(size_range[0], size_range[1])
        # Loop within frame
        y = (y0 - spd * t) % h
        x = x0 + amp * math.sin(2 * math.pi * t / period + i)
        a = int(alpha * (0.4 + 0.6 * math.sin(t * 1.5 + i)))
        a = max(0, min(255, a))
        d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=color + (a,))
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    return base.convert("RGB")


# ─────────────────────────── flash ──────────────────────────────────────────

def flash_overlay(img, intensity, color=(255, 255, 255)):
    """Overlay a full-frame colour flash. intensity in [0, 1]."""
    if intensity <= 0:
        return img
    intensity = max(0.0, min(1.0, intensity))
    overlay = Image.new("RGBA", img.size, color + (int(255 * intensity),))
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    return base.convert("RGB")


# ─────────────────────────── scale around center ────────────────────────────

def scale_image_centered(pil_img, scale, target_size=None):
    """
    Scale a PIL image around its centre. If target_size is given, the result is
    placed on a transparent canvas of that size (centred). Otherwise the canvas
    matches the new size.
    """
    if scale == 1.0 and target_size is None:
        return pil_img
    w, h = pil_img.size
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    scaled = pil_img.resize((new_w, new_h), Image.LANCZOS)
    if target_size is None:
        return scaled
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    px = (target_size[0] - new_w) // 2
    py = (target_size[1] - new_h) // 2
    canvas.paste(scaled, (px, py), scaled if scaled.mode == "RGBA" else None)
    return canvas


def shift_image(img, dx, dy, fill=None):
    """Shift the whole frame by (dx, dy) pixels — used for screen shake."""
    if dx == 0 and dy == 0:
        return img
    fill = fill or theme.BG_DARK
    canvas = Image.new("RGB", img.size, fill)
    canvas.paste(img, (dx, dy))
    return canvas


# ─────────────────────────── ken burns ──────────────────────────────────────

def ken_burns(pil_img, t, total_dur, target_w, target_h,
              start_scale=1.0, end_scale=1.08, pan_x=0.0, pan_y=0.0):
    """
    Slow zoom + pan for an image — gives life to static photos.
    `pan_x`, `pan_y` are normalized (-1..1) — final pixel offset = pan * (scaled - target).
    Returns a PIL RGB image of size (target_w, target_h).
    """
    if total_dur <= 0:
        prog = 1.0
    else:
        prog = max(0.0, min(1.0, t / total_dur))
    scale = start_scale + (end_scale - start_scale) * prog

    sw, sh = pil_img.size
    # First fit to target (cover)
    fit = max(target_w / sw, target_h / sh)
    base_w = int(sw * fit)
    base_h = int(sh * fit)
    final_w = int(base_w * scale)
    final_h = int(base_h * scale)
    img = pil_img.resize((final_w, final_h), Image.LANCZOS)
    # Centre + pan
    cx = (final_w - target_w) // 2 + int(pan_x * (final_w - target_w) / 2)
    cy = (final_h - target_h) // 2 + int(pan_y * (final_h - target_h) / 2)
    cx = max(0, min(final_w - target_w, cx))
    cy = max(0, min(final_h - target_h, cy))
    return img.crop((cx, cy, cx + target_w, cy + target_h))
