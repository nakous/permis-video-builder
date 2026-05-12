from PIL import Image, ImageDraw, ImageFont
import theme
from renderer.animations import ease_out, ease_out_back, _clamp01


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

    lines = _wrap_lines(text, font, d, max_width)
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
    lines = _wrap_lines(text, font, d, max_width)
    return len(lines) * int(size * line_spacing)


def _wrap_lines(text, font, d, max_width):
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
    return lines


# ─────────────────────────── kinetic typography ─────────────────────────────

def draw_kinetic_text(draw, text, x, y, size=80, weight="ExtraBold",
                      color=None, anchor="mt", t=0.0,
                      char_stagger=0.04, char_duration=0.45,
                      slide_distance=24, base_delay=0.0,
                      easing=ease_out_back, shadow=True, shadow_offset=4):
    """
    Render `text` with each character animating in independently:
      • slides up `slide_distance` px
      • fades in
      • optional spring on offset (via easing)

    `anchor` supports "lt", "lm", "lb", "mt", "mm", "mb" for the BLOCK only;
    individual characters are placed sequentially (no per-char anchor).
    Returns the total width drawn.
    """
    color = color or theme.TEXT_WHITE
    font  = _get_font(size, weight)
    d     = _dummy_draw()

    # Compute total width to handle horizontal anchoring
    total_w = 0
    char_widths = []
    for ch in text:
        # textlength gives advance width including spacing; works on PIL >=8
        w = int(d.textlength(ch, font=font))
        char_widths.append(w)
        total_w += w
    bb_h = d.textbbox((0, 0), text, font=font)
    h = bb_h[3] - bb_h[1]

    # Anchor in X
    if anchor[0] == "m":
        cur_x = x - total_w // 2
    elif anchor[0] == "r":
        cur_x = x - total_w
    else:
        cur_x = x
    # Anchor in Y
    if len(anchor) > 1 and anchor[1] == "m":
        base_y = y - h // 2 - bb_h[1]
    elif len(anchor) > 1 and anchor[1] == "b":
        base_y = y - h - bb_h[1]
    else:
        base_y = y

    for i, ch in enumerate(text):
        if ch == " ":
            cur_x += char_widths[i]
            continue
        elapsed = t - base_delay - i * char_stagger
        if elapsed <= 0:
            cur_x += char_widths[i]
            continue
        prog = easing(min(1.0, elapsed / char_duration))
        # Slide up & fade in
        offset_y = int((1 - prog) * slide_distance)
        alpha    = _clamp01(prog)
        if alpha <= 0.01:
            cur_x += char_widths[i]
            continue
        # Blend color towards bg for fade
        col = _blend(color, alpha)
        if shadow:
            draw.text((cur_x + shadow_offset, base_y + offset_y + shadow_offset),
                      ch, font=font, fill=(0, 0, 0))
        draw.text((cur_x, base_y + offset_y), ch, font=font, fill=col)
        cur_x += char_widths[i]
    return total_w


def draw_word_kinetic(draw, text, x, y, max_width, size=44, weight="Bold",
                      color=None, line_spacing=1.35,
                      t=0.0, base_delay=0.0,
                      word_stagger=0.06, word_duration=0.35,
                      slide_distance=12, easing=ease_out_back,
                      shadow=True, shadow_offset=2):
    """
    Reveal text word-by-word with stagger. Each word slides up `slide_distance`
    px and fades in over `word_duration` seconds, starting at
    `base_delay + i * word_stagger`.

    Word-wraps within `max_width`. Returns total height consumed.
    """
    color = color or theme.TEXT_WHITE
    font  = _get_font(size, weight)
    d     = _dummy_draw()

    # Wrap into lines first (same algorithm as draw_multiline)
    words = text.split()
    lines = []
    current_words = []
    for w in words:
        trial = " ".join(current_words + [w])
        if d.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current_words.append(w)
        else:
            if current_words:
                lines.append(current_words)
            current_words = [w]
    if current_words:
        lines.append(current_words)

    line_h = int(size * line_spacing)
    space_w = int(d.textlength(" ", font=font))
    word_index = 0
    for li, line_words in enumerate(lines):
        cur_x = x
        iy    = y + li * line_h
        for word in line_words:
            elapsed = t - base_delay - word_index * word_stagger
            if elapsed <= 0:
                # Not yet visible — but still advance cursor (keeps subsequent words aligned)
                cur_x += int(d.textlength(word, font=font)) + space_w
                word_index += 1
                continue
            prog = easing(min(1.0, elapsed / word_duration))
            offset_y = int((1 - prog) * slide_distance)
            alpha    = _clamp01(prog)
            col = _blend(color, alpha)
            if shadow:
                draw.text((cur_x + shadow_offset, iy + offset_y + shadow_offset),
                          word, font=font, fill=(0, 0, 0))
            draw.text((cur_x, iy + offset_y), word, font=font, fill=col)
            cur_x += int(d.textlength(word, font=font)) + space_w
            word_index += 1
    return len(lines) * line_h


def draw_letter_spaced(draw, text, x, y, size=32, weight="SemiBold",
                       color=None, anchor="mt", tracking=10,
                       shadow=False, shadow_offset=2):
    """
    Draw text with real letter-spacing (extra px between chars).
    `tracking` = extra pixels between adjacent chars (positive widens).
    `anchor` supports x: l/m/r and y: t/m/b.
    """
    color = color or theme.TEXT_WHITE
    font  = _get_font(size, weight)
    d     = _dummy_draw()

    # Measure each char width
    widths = [int(d.textlength(ch, font=font)) for ch in text]
    total_w = sum(widths) + tracking * max(0, len(text) - 1)
    bb = d.textbbox((0, 0), text, font=font)
    h  = bb[3] - bb[1]

    # X anchor
    if anchor[0] == "m":
        cur_x = x - total_w // 2
    elif anchor[0] == "r":
        cur_x = x - total_w
    else:
        cur_x = x

    # Y anchor
    if len(anchor) > 1 and anchor[1] == "m":
        base_y = y - h // 2 - bb[1]
    elif len(anchor) > 1 and anchor[1] == "b":
        base_y = y - h - bb[1]
    else:
        base_y = y

    for i, ch in enumerate(text):
        if shadow:
            draw.text((cur_x + shadow_offset, base_y + shadow_offset),
                      ch, font=font, fill=(0, 0, 0))
        draw.text((cur_x, base_y), ch, font=font, fill=color)
        cur_x += widths[i] + tracking
    return total_w


def draw_typewriter(draw, text, x, y, max_width, size=44, weight="Bold",
                    color=None, line_spacing=1.3, anchor_x="left",
                    t=0.0, base_delay=0.0, char_per_sec=45,
                    shadow=True, shadow_offset=2, cursor=False):
    """
    Reveal text one character at a time at `char_per_sec`. Wraps on `max_width`.
    """
    color = color or theme.TEXT_WHITE
    font  = _get_font(size, weight)
    d     = _dummy_draw()

    elapsed = max(0.0, t - base_delay)
    n_visible = int(elapsed * char_per_sec)
    if n_visible <= 0:
        return 0
    visible = text[:n_visible]
    if cursor and n_visible < len(text):
        visible += "▍"

    lines = _wrap_lines(visible, font, d, max_width)
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


def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
