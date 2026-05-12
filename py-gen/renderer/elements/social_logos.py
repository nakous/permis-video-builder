"""
Social platform logos — rendered from the official SVG assets.

`get_logo(name, size)` returns an RGBA PIL Image of size×size with the SVG
rasterised at that resolution and tinted with the platform's brand colour.

SVG files live in `assets/social/{name}.svg` and use a 32×32 viewBox.
Tinting works because the SVG fills are black by default (`<path>` with no
fill attribute) — we replace the result's RGB with the brand colour while
keeping the alpha mask.

Implemented :
  • instagram → magenta/pink gradient (we use a flat magenta for simplicity)
  • youtube   → YouTube red
  • x         → black on a transparent bg (no card)
"""
import os
from io import BytesIO
from PIL import Image, ImageDraw

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM


_ROOT       = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                            "..", "..", ".."))
_SOCIAL_DIR = os.path.join(_ROOT, "assets", "social")


# ── brand colours (single-tone tint for simplicity & clarity on dark bg) ────
BRAND_COLORS = {
    "instagram": (228, 64, 95),    # Insta pink — replaces the gradient (works on dark)
    "youtube":   (255, 0, 0),
    "x":         (255, 255, 255),  # X is monochrome — use white on dark bg
    "tiktok":    (255, 255, 255),
}


_RASTER_CACHE = {}


def _rasterise_svg(svg_path, size):
    """
    SVG → tinted RGBA PIL Image at (size, size).

    reportlab renders on a white bg with no alpha channel. We rasterise at
    2× the target size for AA, then use inverted luminance as the alpha
    channel (black logo pixels → opaque, white bg → transparent).
    """
    drawing = svg2rlg(svg_path)
    if drawing is None:
        return None
    src_w = drawing.width  or 32
    src_h = drawing.height or 32
    # Render at 2× for cleaner antialiasing then downscale
    render_size = size * 2
    scale = render_size / max(src_w, src_h)
    drawing.width  = render_size
    drawing.height = render_size
    drawing.scale(scale, scale)

    buf = BytesIO()
    renderPM.drawToFile(drawing, buf, fmt="PNG")
    buf.seek(0)
    rgb = Image.open(buf).convert("RGB")
    if rgb.size != (render_size, render_size):
        rgb = rgb.resize((render_size, render_size), Image.LANCZOS)

    # Build alpha from inverted luminance (white bg → 0, black → 255)
    grey  = rgb.convert("L")
    alpha = grey.point(lambda p: 255 - p)

    rgba = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    rgba.putalpha(alpha)
    # Downscale to target with LANCZOS for crispness
    if render_size != size:
        rgba = rgba.resize((size, size), Image.LANCZOS)
    return rgba


def _tint_rgba(img, color):
    """Recolour with `color`, keeping original alpha (the mask)."""
    a = img.getchannel("A")
    return Image.merge("RGBA", (
        Image.new("L", img.size, color[0]),
        Image.new("L", img.size, color[1]),
        Image.new("L", img.size, color[2]),
        a,
    ))


def get_logo(name, size):
    """Cached lookup. Returns an RGBA PIL Image (size × size)."""
    key = (name, size)
    cached = _RASTER_CACHE.get(key)
    if cached is not None:
        return cached

    svg_path = os.path.join(_SOCIAL_DIR, f"{name}.svg")
    if not os.path.exists(svg_path):
        return None

    raw = _rasterise_svg(svg_path, size)
    if raw is None:
        return None

    # Tint with brand colour (keeps alpha)
    color = BRAND_COLORS.get(name, (255, 255, 255))
    logo  = _tint_rgba(raw, color)

    _RASTER_CACHE[key] = logo
    return logo
