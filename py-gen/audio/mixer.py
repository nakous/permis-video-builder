"""
Audio mixer — loads all MP3s, measures durations, builds a CompositeAudioClip.

Timeline:
  t=0                   intro.mp3  +  bg-music (vol 0.15, loop)
  t=intro_end           question.mp3
  t=question_end        tick.mp3 × 3  (at t+0, t+1, t+2)
  t=countdown_end       correct.mp3  OR  wrong.mp3
  t=answer_end          explication.mp3
  t=explication_end     outro.mp3
"""

import os
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip, concatenate_audioclips
import moviepy.audio.fx.all as afx


def _vol(clip, factor):
    if factor == 1.0:
        return clip
    return clip.fx(afx.volumex, factor)


def _load(path, start=0.0, volume=1.0):
    """Return an AudioFileClip positioned at `start` with volume applied."""
    if not os.path.exists(path):
        return None
    clip = AudioFileClip(path).set_start(start)
    return _vol(clip, volume)


def duration_of(path):
    """Return duration in seconds, or 0.0 if file missing."""
    if not path or not os.path.exists(path):
        return 0.0
    c = AudioFileClip(path)
    d = c.duration
    c.close()
    return d


def build_audio(video_data, settings, countdown_dur):
    """
    Assemble all audio tracks into a single CompositeAudioClip.
    Every screen duration is read from its real MP3 — nothing is hardcoded.

    Returns (composite_clip, total_duration, timings_dict).
    """
    s = settings["sounds"]
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def abs_path(p):
        return os.path.normpath(os.path.join(root, p.lstrip("./")))

    intro_path   = abs_path(s["intro"])
    tick_path    = abs_path(s["suspense"])
    correct_path = abs_path(s["correct"])
    wrong_path   = abs_path(s["wrong"])
    outro_path   = abs_path(s["outro"])
    bg_path      = abs_path(s["backgroundMusic"])
    bg_vol       = float(s.get("backgroundMusicVolume", 0.15))

    q_path  = abs_path(video_data["question"]["audio"])
    e_path  = abs_path(video_data["explication"]["audio"])
    is_faux = video_data["reponse"].upper() == "FAUX"

    # Durées lues depuis les vrais MP3 — chaque écran s'arrête à la fin de son audio
    intro_max = float(video_data.get("timing", {}).get("introDuration", 4.0))
    intro_dur = min(duration_of(intro_path) or intro_max, intro_max)
    q_dur     = duration_of(q_path)
    e_dur     = duration_of(e_path)
    a_dur     = duration_of(correct_path if not is_faux else wrong_path) or 2.0

    t0  = 0.0
    t1  = t0  + intro_dur            # question starts
    t2  = t1  + q_dur                # countdown starts
    t3  = t2  + countdown_dur        # answer starts
    t4  = t3  + a_dur                # explication starts
    outro_max = float(video_data.get("timing", {}).get("outroDuration", 4.0))
    outro_dur = min(duration_of(outro_path) or outro_max, outro_max)

    t5    = t4 + e_dur               # outro starts
    total = t5 + outro_dur

    clips = []

    # bg music — loop for full duration
    if os.path.exists(bg_path):
        bg = AudioFileClip(bg_path)
        loops = int(total / bg.duration) + 2
        bg_loop = concatenate_audioclips([bg] * loops).subclip(0, total)
        clips.append(_vol(bg_loop, bg_vol))

    def add(path, start, vol=1.0):
        c = _load(path, start=start, volume=vol)
        if c:
            clips.append(c)

    if os.path.exists(intro_path):
        clips.append(AudioFileClip(intro_path).subclip(0, intro_dur).set_start(t0))
    add(q_path,       t1)

    if os.path.exists(tick_path):
        tick_dur = min(1.0, duration_of(tick_path))
        for i in range(int(countdown_dur)):
            clips.append(
                AudioFileClip(tick_path).subclip(0, tick_dur).set_start(t2 + i)
            )

    add(correct_path if not is_faux else wrong_path, t3)
    add(e_path,  t4)
    if os.path.exists(outro_path):
        clips.append(AudioFileClip(outro_path).subclip(0, outro_dur).set_start(t5))

    composite = CompositeAudioClip(clips).set_duration(total)
    return composite, total, {
        "t_intro":       t0,
        "t_question":    t1,
        "t_countdown":   t2,
        "t_answer":      t3,
        "t_explication": t4,
        "t_outro":       t5,
        "q_dur":         q_dur,
        "e_dur":         e_dur,
        "a_dur":         a_dur,
        "total":         total,
    }
