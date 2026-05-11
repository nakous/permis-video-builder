from PIL import Image, ImageDraw
import os
import theme
from renderer.elements.card import rounded_rect_mask


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
