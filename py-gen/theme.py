import os
import requests
from config import FONTS_DIR

# ── Brand colours (exact testpermis.fr CSS variables) ────────────────────────
PRIMARY        = (45,  212, 191)   # #2DD4BF
PRIMARY_DARK   = (20,  184, 166)   # #14B8A6
PRIMARY_LIGHT  = (94,  234, 212)   # #5EEAD4
ACCENT         = (13,  148, 136)   # #0D9488

BG_DARK        = (17,  24,  39)    # #111827
BG_CARD        = (31,  41,  55)    # #1F2937
BG_CARD2       = (55,  65,  81)    # #374151

TEXT_WHITE     = (255, 255, 255)
TEXT_MEDIUM    = (156, 163, 175)   # #9CA3AF
TEXT_DARK      = (31,  41,  55)

SUCCESS        = (16,  185, 129)   # #10B981
WARNING        = (245, 158, 11)    # #F59E0B
DANGER         = (239, 68,  68)    # #EF4444


# ── Design tokens ────────────────────────────────────────────────────────────
# 8-pt grid spacing scale
SPACE = {
    "0":   0,
    "xs":  4,
    "sm":  8,
    "md":  16,
    "lg":  24,
    "xl":  32,
    "2xl": 48,
    "3xl": 64,
    "4xl": 96,
    "5xl": 128,
}

# Border radius scale
RADIUS = {
    "none":   0,
    "xs":     4,
    "sm":     8,
    "md":     16,
    "lg":     24,
    "xl":     32,
    "2xl":    48,
    "pill":   9999,   # use ph // 2 in code
}

# Stroke widths
STROKE = {
    "thin":  2,
    "base":  3,
    "thick": 4,
    "bold":  6,
    "heavy": 8,
}

# Typography size scale (consistent ratio)
TEXT_SIZE = {
    "xs":     22,
    "sm":     26,
    "base":   32,
    "md":     38,
    "lg":     44,
    "xl":     52,
    "2xl":    64,
    "3xl":    80,
    "4xl":    96,
    "display": 140,
    "hero":   190,
}

# Font weight aliases (mapped to file names)
WEIGHT = {
    "regular":  "Regular",
    "medium":   "SemiBold",
    "semibold": "SemiBold",
    "bold":     "Bold",
    "black":    "ExtraBold",
}

# Animation durations in seconds
DURATION = {
    "instant":  0.10,
    "fast":     0.18,
    "base":     0.30,
    "slow":     0.45,
    "slower":   0.60,
    "slowest":  1.00,
}

# Shadow / aura definitions
SHADOW = {
    "sm":  {"offset": (2, 2),  "blur": 4,  "alpha": 80,  "spread": 0},
    "md":  {"offset": (3, 5),  "blur": 8,  "alpha": 100, "spread": 2},
    "lg":  {"offset": (4, 8),  "blur": 16, "alpha": 120, "spread": 4},
    "aura":{"offset": (0, 0),  "blur": 40, "alpha": 70,  "spread": 12},
}

# Difficulty mapping (semantic, used everywhere)
DIFFICULTY = {
    "facile":    {"color": SUCCESS, "label": "FACILE"},
    "moyen":     {"color": WARNING, "label": "MOYEN"},
    "difficile": {"color": DANGER,  "label": "DIFFICILE"},
}

# Badge/state semantic colors
BADGE = {
    "success": SUCCESS,
    "warning": WARNING,
    "danger":  DANGER,
    "info":    PRIMARY,
}

# Layer alpha presets
ALPHA = {
    "veil":      0.25,
    "scrim":     0.50,
    "overlay":   0.70,
    "card":      0.92,
    "card_soft": 0.55,
    "pill":      0.90,
}

# Layout constants for the 9:16 TikTok format
LAYOUT = {
    "pad_x":         48,
    "pad_y":         48,
    "img_h_ratio":   0.44,    # max image area as fraction of HEIGHT
    "choice_h":      96,
    "badge_h":       56,
    "card_radius":   24,
    "pill_pad_x":    22,
    "pill_pad_y":    12,
}

# ── Font setup — Roboto variable font + fontTools extraction ─────────────────
_WEIGHTS  = {"Regular": 400, "SemiBold": 600, "Bold": 700, "ExtraBold": 800}
_VAR_URL  = "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf"

_SYSTEM_FALLBACKS = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

FONTS = {}


def _system_font():
    for p in _SYSTEM_FALLBACKS:
        if os.path.exists(p):
            return p
    return None


def _is_valid_ttf(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1")
    except Exception:
        return False


def _download_variable():
    vpath = os.path.join(FONTS_DIR, "Roboto-variable.ttf")
    if os.path.exists(vpath) and _is_valid_ttf(vpath):
        return vpath
    print("  Downloading Roboto variable font...")
    r = requests.get(_VAR_URL, timeout=60, allow_redirects=True)
    r.raise_for_status()
    with open(vpath, "wb") as f:
        f.write(r.content)
    return vpath


def _extract_weights(vpath):
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.ttLib import TTFont
    for name, w in _WEIGHTS.items():
        dest = os.path.join(FONTS_DIR, f"Roboto-{name}.ttf")
        if os.path.exists(dest) and _is_valid_ttf(dest):
            FONTS[name] = dest
            continue
        print(f"  Extracting Roboto-{name} (w{w})...")
        tt = TTFont(vpath)
        instantiateVariableFont(tt, {"wght": w, "wdth": 100})
        tt.save(dest)
        FONTS[name] = dest


def load_fonts():
    global FONTS
    all_ok = all(
        os.path.exists(os.path.join(FONTS_DIR, f"Roboto-{n}.ttf")) and
        _is_valid_ttf(os.path.join(FONTS_DIR, f"Roboto-{n}.ttf"))
        for n in _WEIGHTS
    )
    if all_ok:
        for n in _WEIGHTS:
            FONTS[n] = os.path.join(FONTS_DIR, f"Roboto-{n}.ttf")
        return FONTS

    try:
        vpath = _download_variable()
        _extract_weights(vpath)
    except Exception as e:
        print(f"  Warning: Roboto setup failed ({e}). Using system font.")
        fallback = _system_font()
        if not fallback:
            raise RuntimeError("No font available.")
        for n in _WEIGHTS:
            FONTS[n] = fallback
    return FONTS


def font_path(weight="Regular"):
    if not FONTS:
        load_fonts()
    return FONTS.get(weight, FONTS.get("Regular"))


# ── Fallback font for glyphs missing in Roboto (arrows, ✓, ✗, etc.) ─────────
_FALLBACK_CANDIDATES = [
    r"C:\Windows\Fonts\seguisym.ttf",   # Segoe UI Symbol — best coverage on Win
    r"C:\Windows\Fonts\seguiemj.ttf",   # Segoe UI Emoji — fallback of fallback
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

_FALLBACK_PATH = None


def fallback_font_path():
    """Path to a font with broad symbol coverage (arrows, checkmarks, …)."""
    global _FALLBACK_PATH
    if _FALLBACK_PATH is not None:
        return _FALLBACK_PATH
    for p in _FALLBACK_CANDIDATES:
        if os.path.exists(p):
            _FALLBACK_PATH = p
            return p
    _FALLBACK_PATH = font_path("Regular")  # last resort
    return _FALLBACK_PATH
