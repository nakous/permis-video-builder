from PIL import Image, ImageDraw
import numpy as np
import theme


def rounded_rect_mask(width, height, radius):
    """Return an L-mode mask with rounded corners."""
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=255)
    return mask


def draw_card(
    img,
    x, y, w, h,
    radius=24,
    fill=None,
    border_color=None,
    border_width=2,
    alpha=0.88,
):
    """
    Composite a semi-transparent rounded card onto `img`.
    `fill` is an RGB tuple; transparency comes from `alpha`.
    """
    fill = fill or theme.BG_CARD

    card = Image.new("RGBA", (w, h), fill + (int(alpha * 255),))
    mask = rounded_rect_mask(w, h, radius)
    card.putalpha(mask)

    if border_color:
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle(
            [border_width // 2, border_width // 2,
             w - 1 - border_width // 2, h - 1 - border_width // 2],
            radius=radius,
            outline=border_color + (180,),
            width=border_width,
        )
        card = Image.alpha_composite(card, overlay)

    # Composite onto img
    img = img.convert("RGBA")
    img.paste(card, (x, y), card)
    return img.convert("RGB")


def draw_pill(
    img,
    cx, cy,
    text,
    bg_color,
    text_color=None,
    font_size=28,
    font_weight="Bold",
    pad_x=28,
    pad_y=14,
):
    """Draw a pill-shaped badge centred at (cx, cy)."""
    from renderer.elements.typography import _get_font, text_size
    text_color = text_color or theme.TEXT_WHITE
    tw, th = text_size(text, font_size, font_weight)
    pw = tw + pad_x * 2
    ph = th + pad_y * 2

    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    mask = rounded_rect_mask(pw, ph, ph // 2)
    bg   = Image.new("RGBA", (pw, ph), bg_color + (230,))
    bg.putalpha(mask)
    pill = Image.alpha_composite(pill, bg)

    draw = ImageDraw.Draw(pill)
    font = _get_font(font_size, font_weight)
    bb   = draw.textbbox((0, 0), text, font=font)
    tx   = (pw - (bb[2] - bb[0])) // 2 - bb[0]
    ty   = (ph - (bb[3] - bb[1])) // 2 - bb[1]
    draw.text((tx, ty), text, font=font, fill=text_color)

    img = img.convert("RGBA")
    img.paste(pill, (cx - pw // 2, cy - ph // 2), pill)
    return img.convert("RGB")
