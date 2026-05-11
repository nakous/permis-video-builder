from PIL import ImageDraw
import theme
from config import WIDTH


BAR_HEIGHT = 6
BAR_Y_OFFSET = 0  # from bottom


def draw_progress_bar(img, progress, y=None):
    """
    Draw a thin progress bar at the bottom of `img`.
    `progress` in [0, 1].
    """
    if y is None:
        y = img.height - BAR_HEIGHT

    draw = ImageDraw.Draw(img)

    # Background track
    draw.rectangle([0, y, WIDTH, y + BAR_HEIGHT], fill=theme.BG_CARD2)

    # Fill
    fill_w = int(WIDTH * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        draw.rectangle([0, y, fill_w, y + BAR_HEIGHT], fill=theme.PRIMARY)

    return img
