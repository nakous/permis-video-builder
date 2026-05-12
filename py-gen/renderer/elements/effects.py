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


# ─────────────────────────── colored aura (soft blob shadow) ───────────────

_AURA_CACHE = {}


def _aura_blob(width, height, color, blur_radius=40, alpha=70, downsample=2):
    """
    Pre-render a soft colored blob the size of (width, height) with the given
    blur. Cached by parameters → repeated paste is virtually free.

    Trick : render at width/downsample then upscale → 4× faster blur for
    near-identical visual result.
    """
    key = (width, height, color, blur_radius, alpha, downsample)
    cached = _AURA_CACHE.get(key)
    if cached is not None:
        return cached

    dw, dh = max(8, width // downsample), max(8, height // downsample)
    db     = max(2, blur_radius // downsample)

    # Draw an ellipse slightly inset; the blur will spread it out
    blob = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
    d    = ImageDraw.Draw(blob)
    inset = 6
    d.ellipse([inset, inset, dw - inset, dh - inset],
              fill=color + (alpha,))
    blob = blob.filter(ImageFilter.GaussianBlur(db))

    # Upscale back
    if downsample > 1:
        blob = blob.resize((width, height), Image.LANCZOS)

    _AURA_CACHE[key] = blob
    return blob


def aura_behind(base, x, y, w, h, color=None, blur_radius=40,
                alpha=70, padding=30, downsample=2):
    """
    Composite a soft colored aura behind the rectangle (x, y, w, h).
    Useful to give cards/pills a halo of their accent color.

    `padding` extends the aura beyond the rect on all sides.
    """
    color = color or theme.PRIMARY
    aw = w + padding * 2
    ah = h + padding * 2
    blob = _aura_blob(aw, ah, color, blur_radius, alpha, downsample)
    bx = x - padding
    by = y - padding
    base = base.convert("RGBA")
    base.paste(blob, (bx, by), blob)
    return base.convert("RGB")


# ─────────────────────────── animated bg overlay (hue-shift fake) ──────────

_HUE_OVERLAY_CACHE = {}


def _radial_overlay_layer(size, color, radius_frac=0.7, alpha=42):
    """Pre-render a soft radial gradient layer (centered)."""
    key = (size, color, radius_frac, alpha)
    cached = _HUE_OVERLAY_CACHE.get(key)
    if cached is not None:
        return cached
    w, h = size
    # Render at quarter resolution then upscale — much faster
    sw, sh = w // 4, h // 4
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    arr = np.zeros((sh, sw, 4), dtype=np.uint8)
    cx, cy = sw / 2, sh / 2
    R = max(sw, sh) * radius_frac
    Y, X = np.ogrid[:sh, :sw]
    d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / R
    a = np.clip(1 - d, 0, 1) ** 1.6 * alpha
    arr[:, :, 0] = color[0]
    arr[:, :, 1] = color[1]
    arr[:, :, 2] = color[2]
    arr[:, :, 3] = a.astype(np.uint8)
    layer = Image.fromarray(arr, "RGBA").resize((w, h), Image.LANCZOS)
    _HUE_OVERLAY_CACHE[key] = layer
    return layer


def animated_bg_overlay(base, t, period=8.0, amplitude_x=0.15, amplitude_y=0.10,
                        color=None, alpha=38, radius_frac=0.65):
    """
    Drift a soft coloured radial overlay across the bg in a slow Lissajous loop.
    Cheap : the gradient is precomputed and just translated each frame.
    """
    color = color or theme.PRIMARY
    layer = _radial_overlay_layer(base.size, color, radius_frac=radius_frac, alpha=alpha)
    w, h  = base.size
    dx = int(amplitude_x * w * math.sin(2 * math.pi * t / period))
    dy = int(amplitude_y * h * math.cos(2 * math.pi * t / (period * 1.4)))
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay.paste(layer, (dx, dy), layer)
    base_rgba = base.convert("RGBA")
    return Image.alpha_composite(base_rgba, overlay).convert("RGB")


# ─────────────────────────── logo "draw-on" reveal ─────────────────────────

def logo_reveal(logo_img, t, dur=0.9, scribble_color=None):
    """
    "Draw-on" alternative for logos that aren't SVG.

    Two phases :
      0 → 0.55*dur  : circular wipe mask reveals the logo from the centre out,
                      with two scribble lines that scan diagonally over the
                      hidden portion (motion-design feel)
      0.55*dur → dur: scribble lines fade out, logo fully visible

    `logo_img` is RGBA. Returns RGBA same size.
    """
    scribble_color = scribble_color or theme.PRIMARY
    if dur <= 0:
        return logo_img

    w, h = logo_img.size
    progress = max(0.0, min(1.0, t / dur))

    # ── Wipe mask : circle that grows from the centre ───────────────────────
    cx, cy = w // 2, h // 2
    max_r  = int(math.sqrt(cx * cx + cy * cy)) + 4
    if progress < 0.55:
        wipe_p = progress / 0.55
        # ease_out_cubic for a snappier reveal
        wipe_p = 1 - (1 - wipe_p) ** 3
        r = int(max_r * wipe_p)
    else:
        r = max_r

    mask = Image.new("L", (w, h), 0)
    md   = ImageDraw.Draw(mask)
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

    # Soft edge on the wipe front
    if progress < 0.55:
        mask = mask.filter(ImageFilter.GaussianBlur(6))

    revealed = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    revealed.paste(logo_img, (0, 0), mask)

    # ── Scribble lines : two diagonals that scan over the reveal front ──────
    if progress < 0.85:
        scrib_alpha = 1.0 if progress < 0.55 else 1.0 - (progress - 0.55) / 0.30
        scrib_alpha = max(0.0, min(1.0, scrib_alpha))
        scrib_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(scrib_overlay)

        # Two scan lines whose position oscillates around the wipe radius
        period = 0.45
        scan_t = (t % period) / period
        for base_offset in [0.0, 0.5]:
            phase = (scan_t + base_offset) % 1.0
            line_y = int(h * phase)
            # Diagonal slash
            slope = 0.7
            x1 = -50
            y1 = line_y - int(slope * (x1 - cx))
            x2 = w + 50
            y2 = line_y - int(slope * (x2 - cx))
            sd.line([(x1, y1), (x2, y2)],
                    fill=scribble_color + (int(140 * scrib_alpha),), width=4)
            # Faint trailing line
            sd.line([(x1, y1 + 14), (x2, y2 + 14)],
                    fill=scribble_color + (int(60 * scrib_alpha),), width=2)

        # Mask scribbles to only the still-hidden portion (outside the wipe r)
        if progress < 0.55:
            inv_mask = Image.eval(mask, lambda v: 255 - v)
            scrib_overlay.putalpha(
                Image.eval(scrib_overlay.getchannel("A"),
                           lambda v: v).point(lambda v: v)
            )
            # Apply inverse mask so scribbles only show outside the revealed area
            tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            tmp.paste(scrib_overlay, (0, 0), inv_mask)
            scrib_overlay = tmp

        revealed = Image.alpha_composite(revealed, scrib_overlay)

    return revealed


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
