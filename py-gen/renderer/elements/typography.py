"""
Typography helpers — with transparent glyph fallback.

Roboto doesn't include arrows (→ ← ↑ ↓), check/cross marks (✓ ✗) and many
symbols. When a string contains such a glyph, we transparently switch to a
fallback font (Segoe UI Symbol on Windows, DejaVu/Helvetica elsewhere) for
JUST that char. Surrounding Roboto chars stay in Roboto.

Performance : we cache the cmap of every loaded font as a Python set, so the
per-char "is supported?" check is O(1).
"""
from PIL import Image, ImageDraw, ImageFont
import theme
from renderer.animations import ease_out, ease_out_back, _clamp01

try:
    from fontTools.ttLib import TTFont
    _HAS_FONTTOOLS = True
except Exception:
    _HAS_FONTTOOLS = False


# ─────────────────────────── font + cmap caches ────────────────────────────
_FONT_CACHE = {}     # (path, size) -> ImageFont
_CMAP_CACHE = {}     # path -> set[int]


def _get_font(size, weight="Regular"):
    return _font_at(theme.font_path(weight), size)


def _font_at(path, size):
    key = (path, size)
    f = _FONT_CACHE.get(key)
    if f is None:
        f = ImageFont.truetype(path, size)
        _FONT_CACHE[key] = f
    return f


def _supported_codepoints(path):
    """Set of unicode codepoints supported by the font at `path`."""
    if path in _CMAP_CACHE:
        return _CMAP_CACHE[path]
    if not _HAS_FONTTOOLS:
        # Without fontTools we can't introspect → assume everything is OK
        _CMAP_CACHE[path] = None
        return None
    try:
        tt = TTFont(path)
        cmap = set(tt.getBestCmap().keys())
    except Exception:
        cmap = None
    _CMAP_CACHE[path] = cmap
    return cmap


def _font_for_char(ch, size, weight):
    """Return the right ImageFont for a given char (primary or fallback)."""
    primary_path = theme.font_path(weight)
    cmap = _supported_codepoints(primary_path)
    if cmap is None or ord(ch) in cmap:
        return _font_at(primary_path, size)
    # fallback
    return _font_at(theme.fallback_font_path(), size)


def _needs_fallback(text, weight):
    """True if any char in `text` requires the fallback font."""
    primary_path = theme.font_path(weight)
    cmap = _supported_codepoints(primary_path)
    if cmap is None:
        return False
    for ch in text:
        if ord(ch) not in cmap:
            return True
    return False


def _dummy_draw():
    return ImageDraw.Draw(Image.new("RGB", (1, 1)))


# ─────────────────────────── mixed-font measurement ────────────────────────

def _text_length_mixed(text, size, weight):
    """Sum of advance widths using the right font per char."""
    if not text:
        return 0
    if not _needs_fallback(text, weight):
        # fast path : single font, native textlength
        return int(_dummy_draw().textlength(text, font=_get_font(size, weight)))
    d = _dummy_draw()
    total = 0
    for ch in text:
        f = _font_for_char(ch, size, weight)
        total += int(d.textlength(ch, font=f))
    return total


def _text_bbox_mixed(text, size, weight):
    """Approximate (x0, y0, x1, y1) bbox for mixed-font text starting at (0,0)."""
    if not _needs_fallback(text, weight):
        return _dummy_draw().textbbox((0, 0), text, font=_get_font(size, weight))
    d = _dummy_draw()
    cur_x = 0
    bb = [0, 10**9, 0, -10**9]
    for ch in text:
        f = _font_for_char(ch, size, weight)
        cb = d.textbbox((cur_x, 0), ch, font=f)
        bb[1] = min(bb[1], cb[1])
        bb[3] = max(bb[3], cb[3])
        cur_x += int(d.textlength(ch, font=f))
    bb[2] = cur_x
    if bb[1] > bb[3]:
        bb[1] = 0
        bb[3] = size
    return tuple(bb)


# ─────────────────────────── mixed-font drawing ────────────────────────────

def _draw_text_mixed(draw, text, x, y, size, weight, color,
                     shadow=False, shadow_offset=2):
    """
    Draw text with per-char fallback. Always positions chars left-to-right
    starting at (x, y). Returns total width drawn.
    """
    if not text:
        return 0
    if not _needs_fallback(text, weight):
        font = _get_font(size, weight)
        if shadow:
            draw.text((x + shadow_offset, y + shadow_offset), text,
                      font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=color)
        return int(draw.textlength(text, font=font))
    cur_x = x
    for ch in text:
        f = _font_for_char(ch, size, weight)
        w = int(draw.textlength(ch, font=f))
        if shadow:
            draw.text((cur_x + shadow_offset, y + shadow_offset), ch,
                      font=f, fill=(0, 0, 0))
        draw.text((cur_x, y), ch, font=f, fill=color)
        cur_x += w
    return cur_x - x


# ─────────────────────────── public API ────────────────────────────────────

def text_size(text, size, weight="Regular"):
    bb = _text_bbox_mixed(text, size, weight)
    return bb[2] - bb[0], bb[3] - bb[1]


def draw_text(draw, text, x, y, size=40, weight="Regular", color=None,
              anchor="lt", shadow=True, shadow_color=None, shadow_offset=3):
    color = color or theme.TEXT_WHITE
    if not _needs_fallback(text, weight):
        # Fast path — PIL handles anchor natively
        font = _get_font(size, weight)
        if shadow:
            sc = shadow_color or (0, 0, 0)
            draw.text((x + shadow_offset, y + shadow_offset), text,
                      font=font, fill=sc, anchor=anchor)
        draw.text((x, y), text, font=font, fill=color, anchor=anchor)
        return

    # Mixed font path : compute width manually then place at correct offset
    total_w = _text_length_mixed(text, size, weight)
    bb = _text_bbox_mixed(text, size, weight)
    h  = bb[3] - bb[1]
    if anchor[0] == "m":
        ox = x - total_w // 2
    elif anchor[0] == "r":
        ox = x - total_w
    else:
        ox = x
    if len(anchor) > 1 and anchor[1] == "m":
        oy = y - h // 2 - bb[1]
    elif len(anchor) > 1 and anchor[1] == "b":
        oy = y - h - bb[1]
    else:
        oy = y
    _draw_text_mixed(draw, text, ox, oy, size, weight, color,
                     shadow=shadow, shadow_offset=shadow_offset)


def draw_multiline(draw, text, x, y, max_width, size=36, weight="Regular",
                   color=None, line_spacing=1.3, anchor_x="left",
                   shadow=True, shadow_offset=2):
    """Word-wrap text and draw. Returns total height consumed."""
    color = color or theme.TEXT_WHITE
    lines = _wrap_lines(text, max_width, size, weight)
    line_h = int(size * line_spacing)
    for i, line in enumerate(lines):
        lx = x
        if anchor_x == "center":
            lw = _text_length_mixed(line, size, weight)
            lx = x - lw // 2
        iy = y + i * line_h
        _draw_text_mixed(draw, line, lx, iy, size, weight, color,
                         shadow=shadow, shadow_offset=shadow_offset)
    return len(lines) * line_h


def multiline_height(text, max_width, size, weight="Regular", line_spacing=1.3):
    lines = _wrap_lines(text, max_width, size, weight)
    return len(lines) * int(size * line_spacing)


def _wrap_lines(text, max_width, size, weight):
    """Word-wrap using mixed-font measurement so fallback chars are sized right."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if _text_length_mixed(trial, size, weight) <= max_width:
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
    """Per-char animated draw with transparent fallback."""
    color = color or theme.TEXT_WHITE
    d     = _dummy_draw()

    # Width per char (using right font per char)
    char_widths = []
    for ch in text:
        f = _font_for_char(ch, size, weight)
        char_widths.append(int(d.textlength(ch, font=f)))
    total_w = sum(char_widths)

    bb_h = _text_bbox_mixed(text, size, weight)
    h = bb_h[3] - bb_h[1]

    # Anchor
    if anchor[0] == "m":
        cur_x = x - total_w // 2
    elif anchor[0] == "r":
        cur_x = x - total_w
    else:
        cur_x = x
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
        offset_y = int((1 - prog) * slide_distance)
        alpha    = _clamp01(prog)
        if alpha <= 0.01:
            cur_x += char_widths[i]
            continue
        col = _blend(color, alpha)
        f = _font_for_char(ch, size, weight)
        if shadow:
            draw.text((cur_x + shadow_offset, base_y + offset_y + shadow_offset),
                      ch, font=f, fill=(0, 0, 0))
        draw.text((cur_x, base_y + offset_y), ch, font=f, fill=col)
        cur_x += char_widths[i]
    return total_w


def draw_word_kinetic(draw, text, x, y, max_width, size=44, weight="Bold",
                      color=None, line_spacing=1.35,
                      t=0.0, base_delay=0.0,
                      word_stagger=0.06, word_duration=0.35,
                      slide_distance=12, easing=ease_out_back,
                      shadow=True, shadow_offset=2):
    """Word-by-word reveal with transparent fallback."""
    color = color or theme.TEXT_WHITE

    words = text.split()
    lines = []
    current_words = []
    for w in words:
        trial = " ".join(current_words + [w])
        if _text_length_mixed(trial, size, weight) <= max_width:
            current_words.append(w)
        else:
            if current_words:
                lines.append(current_words)
            current_words = [w]
    if current_words:
        lines.append(current_words)

    line_h = int(size * line_spacing)
    space_w = _text_length_mixed(" ", size, weight)
    word_index = 0
    for li, line_words in enumerate(lines):
        cur_x = x
        iy    = y + li * line_h
        for word in line_words:
            elapsed = t - base_delay - word_index * word_stagger
            word_w  = _text_length_mixed(word, size, weight)
            if elapsed <= 0:
                cur_x += word_w + space_w
                word_index += 1
                continue
            prog = easing(min(1.0, elapsed / word_duration))
            offset_y = int((1 - prog) * slide_distance)
            alpha    = _clamp01(prog)
            col = _blend(color, alpha)
            _draw_text_mixed(draw, word, cur_x, iy + offset_y,
                             size, weight, col,
                             shadow=shadow, shadow_offset=shadow_offset)
            cur_x += word_w + space_w
            word_index += 1
    return len(lines) * line_h


def draw_letter_spaced(draw, text, x, y, size=32, weight="SemiBold",
                       color=None, anchor="mt", tracking=10,
                       shadow=False, shadow_offset=2):
    """Letter-spaced draw with fallback per char."""
    color = color or theme.TEXT_WHITE
    d     = _dummy_draw()

    widths = []
    for ch in text:
        f = _font_for_char(ch, size, weight)
        widths.append(int(d.textlength(ch, font=f)))
    total_w = sum(widths) + tracking * max(0, len(text) - 1)

    bb = _text_bbox_mixed(text, size, weight)
    h  = bb[3] - bb[1]

    if anchor[0] == "m":
        cur_x = x - total_w // 2
    elif anchor[0] == "r":
        cur_x = x - total_w
    else:
        cur_x = x
    if len(anchor) > 1 and anchor[1] == "m":
        base_y = y - h // 2 - bb[1]
    elif len(anchor) > 1 and anchor[1] == "b":
        base_y = y - h - bb[1]
    else:
        base_y = y

    for i, ch in enumerate(text):
        f = _font_for_char(ch, size, weight)
        if shadow:
            draw.text((cur_x + shadow_offset, base_y + shadow_offset),
                      ch, font=f, fill=(0, 0, 0))
        draw.text((cur_x, base_y), ch, font=f, fill=color)
        cur_x += widths[i] + tracking
    return total_w


def draw_typewriter(draw, text, x, y, max_width, size=44, weight="Bold",
                    color=None, line_spacing=1.3, anchor_x="left",
                    t=0.0, base_delay=0.0, char_per_sec=45,
                    shadow=True, shadow_offset=2, cursor=False):
    """Typewriter reveal with transparent fallback."""
    color = color or theme.TEXT_WHITE

    elapsed = max(0.0, t - base_delay)
    n_visible = int(elapsed * char_per_sec)
    if n_visible <= 0:
        return 0
    visible = text[:n_visible]
    if cursor and n_visible < len(text):
        visible += "▍"

    lines = _wrap_lines(visible, max_width, size, weight)
    line_h = int(size * line_spacing)
    for i, line in enumerate(lines):
        lx = x
        if anchor_x == "center":
            lw = _text_length_mixed(line, size, weight)
            lx = x - lw // 2
        iy = y + i * line_h
        _draw_text_mixed(draw, line, lx, iy, size, weight, color,
                         shadow=shadow, shadow_offset=shadow_offset)
    return len(lines) * line_h


def _blend(color, a):
    return tuple(int(color[i] * a + theme.BG_DARK[i] * (1 - a)) for i in range(3))
