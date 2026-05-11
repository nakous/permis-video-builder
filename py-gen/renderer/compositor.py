"""
Compositor — builds a single VideoClip from scene make_frame functions.

Each scene receives:
  t            — local elapsed time within the scene (seconds)
  video_data   — the video dict from JSON
  settings     — the settings dict from JSON
  progress     — 0→1 overall video progress (for progress bar)
"""

import numpy as np
from moviepy.video.VideoClip import VideoClip
from config import WIDTH, HEIGHT, FPS
import renderer.scenes.intro       as intro_scene
import renderer.scenes.question    as question_scene
import renderer.scenes.countdown   as countdown_scene
import renderer.scenes.answer      as answer_scene
import renderer.scenes.explanation as explanation_scene
import renderer.scenes.outro       as outro_scene


def build_video(video_data, settings, timings):
    """
    timings — dict from audio.mixer.build_audio:
      t_intro, t_question, t_countdown, t_answer, t_explication, t_outro,
      q_dur, e_dur, a_dur, total
    """
    total = timings["total"]

    t_intro  = timings["t_intro"]
    t_q      = timings["t_question"]
    t_cd     = timings["t_countdown"]
    t_ans    = timings["t_answer"]
    t_expl   = timings["t_explication"]
    t_outro  = timings["t_outro"]

    def make_frame(t):
        progress = t / total if total > 0 else 0

        if t < t_q:
            local = t - t_intro
            return intro_scene.make_frame(local, video_data, settings)

        if t < t_cd:
            local = t - t_q
            return question_scene.make_frame(local, video_data, settings, progress)

        if t < t_ans:
            local = t - t_cd
            return countdown_scene.make_frame(local, video_data, settings, progress)

        if t < t_expl:
            local = t - t_ans
            return answer_scene.make_frame(local, video_data, settings, progress)

        if t < t_outro:
            local = t - t_expl
            return explanation_scene.make_frame(local, video_data, settings, progress)

        local = t - t_outro
        return outro_scene.make_frame(local, video_data, settings, progress)

    clip = VideoClip(make_frame, duration=total)
    clip = clip.set_fps(FPS)
    return clip
