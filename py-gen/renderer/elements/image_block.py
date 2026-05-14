from PIL import Image, ImageDraw, ImageFilter
import os
import theme
from renderer.elements.card import rounded_rect_mask


_BLUR_BACKDROP_CACHE = {}   # keyed by (path, target_w, target_h, blur_radius, scrim_alpha)


def blur_backdrop(path, target_w, target_h, blur_radius=42, scrim_alpha=0.22):
    """
    Cover-scaled + heavily-blurred backdrop derived from the source image.
    Cached per (path, dims, params). Returns an RGB PIL Image.
    Used as a fill behind a `contain`-scaled foreground so no part of the
    source image gets cropped while the area stays visually populated.
    """
    key = (path, target_w, target_h, blur_radius, scrim_alpha)
    cached = _BLUR_BACKDROP_CACHE.get(key)
    if cached is not None:
        return cached.copy()

    try:
        raw = Image.open(path).convert("RGB")
    except Exception:
        bg = Image.new("RGB", (target_w, target_h), theme.BG_CARD2)
        _BLUR_BACKDROP_CACHE[key] = bg
        return bg.copy()

    sw, sh = raw.size
    scale  = max(target_w / sw, target_h / sh)
    rw, rh = int(sw * scale), int(sh * scale)
    cover  = raw.resize((rw, rh), Image.LANCZOS)
    left, top = (rw - target_w) // 2, (rh - target_h) // 2
    cover  = cover.crop((left, top, left + target_w, top + target_h))

    blurred = cover.filter(ImageFilter.GaussianBlur(blur_radius))
    if scrim_alpha > 0:
        scrim   = Image.new("RGB", (target_w, target_h), theme.BG_DARK)
        blurred = Image.blend(blurred, scrim, scrim_alpha)

    _BLUR_BACKDROP_CACHE[key] = blurred
    return blurred.copy()


def contain_dims(path, max_w, max_h):
    """Return (w, h) sized to fit fully inside (max_w, max_h) preserving ratio."""
    try:
        with Image.open(path) as im:
            sw, sh = im.size
    except Exception:
        return max_w, max_h
    scale = min(max_w / sw, max_h / sh)
    return max(1, int(sw * scale)), max(1, int(sh * scale))


def load_image(path, width, height, radius=20, fade_alpha=1.0, fit="cover"):
    """
    Load and resize image. fit="cover" crops to fill; fit="contain" letterboxes.
    Returns an RGBA image.
    """
    if not path or not os.path.exists(path):
        placeholder = Image.new("RGB", (width, height), theme.BG_CARD2)
        draw = ImageDraw.Draw(placeholder)
        draw.line([0, 0, width, height], fill=theme.BG_CARD, width=4)
        draw.line([0, height, width, 0], fill=theme.BG_CARD, width=4)
        return placeholder.convert("RGBA")

    img = Image.open(path).convert("RGB")
    src_w, src_h = img.size

    if fit == "contain":
        scale = min(width / src_w, height / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGB", (width, height), theme.BG_DARK)
        paste_x = (width  - new_w) // 2
        paste_y = (height - new_h) // 2
        canvas.paste(img, (paste_x, paste_y))
        img = canvas
    else:
        # cover: scale so image fills, then crop centre
        scale = max(width / src_w, height / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - width)  // 2
        top  = (new_h - height) // 2
        img  = img.crop((left, top, left + width, top + height))

    img = img.convert("RGBA")

    if radius > 0:
        mask = rounded_rect_mask(width, height, radius)
        full = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        full.paste(img, (0, 0), mask)
        img = full

    if fade_alpha < 1.0:
        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * fade_alpha))
        img = Image.merge("RGBA", (r, g, b, a))

    return img


def paste_image(base, path, x, y, width, height, radius=20, fade_alpha=1.0, fit="cover"):
    """Load and paste image block onto base (RGB)."""
    block = load_image(path, width, height, radius=radius, fade_alpha=fade_alpha, fit=fit)
    result = base.convert("RGBA")
    result.paste(block, (x, y), block)
    return result.convert("RGB")
