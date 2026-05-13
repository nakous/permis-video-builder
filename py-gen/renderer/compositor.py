"""
Compositor — assemble scenes into a single VideoClip + apply global passes.

Adds two modern touches over the raw scene output:
  • inter-scene transition (short flash + slight scale) for momentum
  • global post-pass (vignette + animated film grain) for cinematic finish

Note: there is no dedicated countdown scene any more — the 3 ticks play
during the tail of the question scene, where the countdown widget overlays
the image.
"""
import numpy as np
from PIL import Image
from moviepy import VideoClip

from config import WIDTH, HEIGHT, FPS
import renderer.scenes.intro       as intro_scene
import renderer.scenes.question    as question_scene
import renderer.scenes.answer      as answer_scene
import renderer.scenes.explanation as explanation_scene
import renderer.scenes.outro       as outro_scene
from renderer.elements import effects


TRANSITION_DUR  = 0.18   # length of cross-fade between scenes (seconds)
ENABLE_GRAIN    = True
ENABLE_VIGNETTE = True


def build_video(video_data, settings, timings):
    total = timings["total"]

    t_intro = timings["t_intro"]
    t_q     = timings["t_question"]
    t_tick  = timings["t_tick"]
    t_ans   = timings["t_answer"]
    t_expl  = timings["t_explication"]
    t_outro = timings["t_outro"]
    cd_dur  = timings["countdown_dur"]

    boundaries = [t_q, t_ans, t_expl, t_outro]

    def render_scene(t):
        progress = t / total if total > 0 else 0
        if t < t_q:
            local = t - t_intro
            return intro_scene.make_frame(local, video_data, settings)
        if t < t_ans:
            local   = t - t_q
            # tick_local: seconds since first tick, or None if not in tick phase
            if t >= t_tick:
                tick_local = t - t_tick
            else:
                tick_local = None
            return question_scene.make_frame(
                local, video_data, settings, progress,
                tick_local=tick_local, countdown_dur=cd_dur,
            )
        if t < t_expl:
            local = t - t_ans
            return answer_scene.make_frame(local, video_data, settings, progress)
        if t < t_outro:
            local = t - t_expl
            return explanation_scene.make_frame(local, video_data, settings, progress)
        local = t - t_outro
        return outro_scene.make_frame(local, video_data, settings, progress)

    def make_frame(t):
        arr = render_scene(t)
        img = Image.fromarray(arr)

        flash_intensity = _flash_intensity_at(t, boundaries, TRANSITION_DUR)
        if flash_intensity > 0.01:
            img = effects.flash_overlay(img, flash_intensity)

        if ENABLE_VIGNETTE:
            img = effects.vignette(img, strength=0.42, falloff=1.5)
        if ENABLE_GRAIN:
            img = effects.grain_overlay(img, strength=6, seed=int(t * FPS) % 9973)

        return np.asarray(img)

    clip = VideoClip(make_frame, duration=total).with_fps(FPS)
    return clip


def _flash_intensity_at(t, boundaries, dur):
    """Triangle-shaped flash that peaks at each boundary, max 0.55."""
    half = dur / 2
    best = 0.0
    for b in boundaries:
        if abs(t - b) < half:
            v = 1.0 - abs(t - b) / half
            if v > best:
                best = v
    return min(0.55, best)
