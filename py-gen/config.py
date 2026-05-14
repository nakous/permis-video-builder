import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Assets
ASSETS_DIR   = os.path.join(ROOT, "assets")
BRAND_DIR    = os.path.join(ASSETS_DIR, "brand")
SOUNDS_DIR   = os.path.join(ASSETS_DIR, "sounds")
VIDEOS_DIR   = os.path.join(ASSETS_DIR, "videos")
FONTS_DIR    = os.path.join(os.path.dirname(__file__), "fonts")
OUTPUT_DIR   = os.path.join(ROOT, "output")
DATA_FILE    = os.path.join(ROOT, "data", "videos-data.json")

# Video format — controlled via VIDEO_FORMAT env var (set by generate.py from --format).
#   "9:16" (default) → 1080×1920 portrait
#   "16:9"           → 1920×1080 landscape
VIDEO_FORMAT = os.environ.get("VIDEO_FORMAT", "9:16")
if VIDEO_FORMAT == "16:9":
    WIDTH, HEIGHT = 1920, 1080
    ORIENTATION   = "landscape"
else:
    WIDTH, HEIGHT = 1080, 1920
    ORIENTATION   = "portrait"
FPS    = 30
CODEC  = "libx264"
AUDIO_CODEC = "aac"
BITRATE = "8000k"

# Default countdown duration — overridden by video_data["timing"]["countdownDuration"]
COUNTDOWN_DURATION = 3.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FONTS_DIR,  exist_ok=True)
