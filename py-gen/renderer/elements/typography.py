from PIL import Image, ImageDraw, ImageFont
import theme


def _get_font(size, weight="Regular"):
    return ImageFont.truetype(theme.font_path(weight), size)


def _dummy_draw():
    return ImageDraw.Draw(Image.new("RGB", (1, 1)))


def text_size(text, size, weight="Regular"):
    font = _get_font(size, weight)
    bb = _dummy_draw().textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def draw_text(draw, text, x, y, size=40, weight="Regular", color=None,
              anchor="lt", shadow=True, shadow_color=None, shadow_offset=3):
    color = color or theme.TEXT_WHITE
    font  = _get_font(size, weight)
    if shadow:
        sc = shadow_color or (0, 0, 0)
        draw.text((x + shadow_offset, y + shadow_offset), text,
                  font=font, fill=sc, anchor=anchor)
    draw.text((x, y), text, font=font, fill=color, anchor=anchor)


def draw_multiline(draw, text, x, y, max_width, size=36, weight="Regular",
                   color=None, line_spacing=1.3, anchor_x="left",
                   shadow=True, shadow_offset=2):
    """Word-wrap text and draw. Returns total height consumed."""
    color = color or theme.TEXT_WHITE
    font  = _get_font(size, weight)
    d     = _dummy_draw()

    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if d.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = int(size * line_spacing)
    for i, line in enumerate(lines):
        lx = x
        if anchor_x == "center":
            lw = d.textbbox((0, 0), line, font=font)[2]
            lx = x - lw // 2
        iy = y + i * line_h
        if shadow:
            draw.text((lx + shadow_offset, iy + shadow_offset), line,
                      font=font, fill=(0, 0, 0))
        draw.text((lx, iy), line, font=font, fill=color)
    return len(lines) * line_h


def multiline_height(text, max_width, size, weight="Regular", line_spacing=1.3):
    font = _get_font(size, weight)
    d    = _dummy_draw()
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if d.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return len(lines) * int(size * line_spacing)
