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

# Video format
WIDTH  = 1080
HEIGHT = 1920
FPS    = 30
CODEC  = "libx264"
AUDIO_CODEC = "aac"
BITRATE = "8000k"

# Default countdown duration — overridden by video_data["timing"]["countdownDuration"]
COUNTDOWN_DURATION = 3.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FONTS_DIR,  exist_ok=True)
