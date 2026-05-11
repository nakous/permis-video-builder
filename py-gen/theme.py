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
