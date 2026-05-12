import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import theme
from config import WIDTH, HEIGHT


def solid(color=None):
    return Image.new("RGB", (WIDTH, HEIGHT), color or theme.BG_DARK)


def linear_gradient(top_color, bottom_color):
    arr = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    tc, bc = np.array(top_color), np.array(bottom_color)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        arr[y] = (tc * (1 - t) + bc * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def radial_gradient(center_color, edge_color=None, cx=None, cy=None, radius=None):
    edge_color = edge_color or theme.BG_DARK
    cx = cx or WIDTH // 2
    cy = cy or HEIGHT // 2
    radius = radius or max(WIDTH, HEIGHT) * 0.75
    arr = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    Y, X = np.ogrid[:HEIGHT, :WIDTH]
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    t = np.clip(dist / radius, 0, 1)
    for c in range(3):
        arr[:, :, c] = (center_color[c] * (1 - t) + edge_color[c] * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


_BRAND_BG_CACHE = None


def brand_bg():
    """Standard brand background — dark top, slightly warmer bottom. Cached."""
    global _BRAND_BG_CACHE
    if _BRAND_BG_CACHE is None:
        _BRAND_BG_CACHE = linear_gradient(theme.BG_DARK, (22, 32, 50))
    return _BRAND_BG_CACHE.copy()


def brand_bg_animated(t):
    """Brand bg with a slow drifting colored overlay → fond qui respire."""
    from renderer.elements import effects as fx
    bg = brand_bg()
    bg = fx.animated_bg_overlay(bg, t, period=9.0,
                                 amplitude_x=0.18, amplitude_y=0.12,
                                 color=theme.PRIMARY, alpha=34, radius_frac=0.55)
    bg = fx.animated_bg_overlay(bg, t + 4.5, period=11.0,
                                 amplitude_x=0.20, amplitude_y=0.14,
                                 color=theme.ACCENT, alpha=24, radius_frac=0.50)
    return bg


def dark_overlay(img, alpha=0.7):
    overlay = Image.new("RGB", img.size, theme.BG_DARK)
    return Image.blend(img.convert("RGB"), overlay, alpha)


def gradient_overlay_bottom(img, start_y, color=None):
    """Apply a bottom-up gradient overlay starting at start_y."""
    color = color or theme.BG_DARK
    result = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    h = img.height - start_y
    for dy in range(h):
        alpha = int(255 * (dy / h) ** 0.6)
        y = start_y + dy
        draw.line([(0, y), (img.width, y)],
                  fill=color + (alpha,))
    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")


def draw_glow(draw, cx, cy, radius, color, steps=40):
    """Draw a radial glow using layered semi-transparent circles."""
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        alpha = int(60 * (1 - i / steps) ** 2)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=color + (alpha,))


def draw_decorative_lines(img, color=None, alpha=18):
    """Subtle diagonal lines in the background corners."""
    color = color or theme.PRIMARY
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(0, 400, 40):
        draw.line([(0, i), (i, 0)], fill=color + (alpha,), width=1)
        draw.line([(WIDTH, HEIGHT - i), (WIDTH - i, HEIGHT)],
                  fill=color + (alpha,), width=1)
    result = img.convert("RGBA")
    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")
