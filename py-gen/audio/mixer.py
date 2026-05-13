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
from moviepy import AudioFileClip, CompositeAudioClip, concatenate_audioclips
import moviepy.audio.fx as afx


def _vol(clip, factor):
    if factor == 1.0:
        return clip
    return clip.with_effects([afx.MultiplyVolume(factor)])


def _load(path, start=0.0, volume=1.0):
    """Return an AudioFileClip positioned at `start` with volume applied."""
    if not os.path.exists(path):
        return None
    clip = AudioFileClip(path).with_start(start)
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
    intro_vol    = float(s.get("introVolume", 1.0))
    outro_vol    = float(s.get("outroVolume", 1.0))

    q_path  = abs_path(video_data["question"]["audio"])
    e_path  = abs_path(video_data["explication"]["audio"])
    is_faux = video_data["reponse"].upper() == "FAUX"

    # Durées lues depuis les vrais MP3 — chaque écran s'arrête à la fin de son audio
    intro_max = float(video_data.get("timing", {}).get("introDuration", 4.0))
    intro_dur = min(duration_of(intro_path) or intro_max, intro_max)
    q_dur     = duration_of(q_path)
    e_dur     = duration_of(e_path)
    a_dur     = duration_of(correct_path if not is_faux else wrong_path) or 2.0

    # Question scene now contains the countdown ticks at its tail.
    # There is no dedicated countdown scene any more.
    t0       = 0.0
    t1       = t0 + intro_dur                   # question scene starts
    tick_t0  = t1 + q_dur                       # tick phase begins (still inside question scene)
    t_ans    = tick_t0 + countdown_dur          # answer scene starts
    t_expl   = t_ans + a_dur                    # explication starts
    outro_max = float(video_data.get("timing", {}).get("outroDuration", 4.0))
    outro_dur = min(duration_of(outro_path) or outro_max, outro_max)

    t_outro = t_expl + e_dur
    total   = t_outro + outro_dur

    clips = []

    # bg music — loop for full duration
    if os.path.exists(bg_path):
        bg = AudioFileClip(bg_path)
        loops = int(total / bg.duration) + 2
        bg_loop = concatenate_audioclips([bg] * loops).subclipped(0, total)
        clips.append(_vol(bg_loop, bg_vol))

    def add(path, start, vol=1.0):
        c = _load(path, start=start, volume=vol)
        if c:
            clips.append(c)

    if os.path.exists(intro_path):
        clips.append(_vol(
            AudioFileClip(intro_path).subclipped(0, intro_dur).with_start(t0),
            intro_vol,
        ))
    add(q_path, t1)

    if os.path.exists(tick_path):
        tick_dur = min(1.0, duration_of(tick_path))
        for i in range(int(countdown_dur)):
            clips.append(
                AudioFileClip(tick_path).subclipped(0, tick_dur).with_start(tick_t0 + i)
            )

    add(correct_path if not is_faux else wrong_path, t_ans)
    add(e_path,  t_expl)
    if os.path.exists(outro_path):
        clips.append(_vol(
            AudioFileClip(outro_path).subclipped(0, outro_dur).with_start(t_outro),
            outro_vol,
        ))

    composite = CompositeAudioClip(clips).with_duration(total)
    return composite, total, {
        "t_intro":        t0,
        "t_question":     t1,
        "t_tick":         tick_t0,        # countdown ticks start here (inside question scene)
        "t_answer":       t_ans,
        "t_explication":  t_expl,
        "t_outro":        t_outro,
        "q_dur":          q_dur,
        "countdown_dur":  countdown_dur,
        "e_dur":          e_dur,
        "a_dur":          a_dur,
        "total":          total,
    }
