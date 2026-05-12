"""
python generate.py              — génère toutes les vidéos
python generate.py --id 1       — génère la vidéo n°1 uniquement
python generate.py --preview question --id 1  — sauvegarde un PNG de la scène
"""

import sys
import os
import json
import argparse
import time

sys.path.insert(0, os.path.dirname(__file__))

import theme
theme.load_fonts()

from config import DATA_FILE, OUTPUT_DIR, CODEC, AUDIO_CODEC, BITRATE, COUNTDOWN_DURATION
from audio.mixer import build_audio
from renderer.compositor import build_video


def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def generate_video(video_data, settings, out_path):
    print(f"\n  Building audio timeline…")
    countdown_dur = video_data.get("timing", {}).get("countdownDuration", COUNTDOWN_DURATION)
    audio_clip, total, timings = build_audio(
        video_data, settings,
        countdown_dur=countdown_dur,
    )

    print(f"  Total duration: {total:.1f}s")
    print(f"  Building video frames…")

    video_clip = build_video(video_data, settings, timings)
    video_clip = video_clip.set_audio(audio_clip)

    print(f"  Exporting -> {out_path}")
    t0 = time.time()
    video_clip.write_videofile(
        out_path,
        fps=30,
        codec=CODEC,
        audio_codec=AUDIO_CODEC,
        bitrate=BITRATE,
        threads=4,
        logger="bar",
    )
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s")


def preview_scene(scene_name, video_data, settings, out_path):
    """Render a single PNG from t=1.0 of the requested scene."""
    from PIL import Image
    import numpy as np
    import renderer.scenes.intro       as intro_scene
    import renderer.scenes.question    as question_scene
    import renderer.scenes.answer      as answer_scene
    import renderer.scenes.explanation as explanation_scene
    import renderer.scenes.outro       as outro_scene

    scenes = {
        "intro":       lambda: intro_scene.make_frame(1.0, video_data, settings),
        "question":    lambda: question_scene.make_frame(1.5, video_data, settings),
        # countdown widget is now embedded in the question scene at its tail
        "countdown":   lambda: question_scene.make_frame(
            6.0, video_data, settings, tick_local=1.5, countdown_dur=3.0,
        ),
        "answer":      lambda: answer_scene.make_frame(1.0, video_data, settings),
        "explanation": lambda: explanation_scene.make_frame(1.5, video_data, settings),
        "outro":       lambda: outro_scene.make_frame(2.0, video_data, settings),
    }

    if scene_name not in scenes:
        print(f"Unknown scene '{scene_name}'. Choose from: {', '.join(scenes)}")
        return

    frame = scenes[scene_name]()
    img = Image.fromarray(frame)
    img.save(out_path)
    print(f"  Preview saved -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="TestPermis.fr — Video generator")
    parser.add_argument("--id",      type=int,  default=None, help="Generate only video #ID")
    parser.add_argument("--preview", type=str,  default=None, help="Preview scene name (no MP4)")
    args = parser.parse_args()

    data     = load_data()
    settings = data["settings"]
    videos   = data["videos"]

    if args.id is not None:
        videos = [v for v in videos if v["id"] == args.id]
        if not videos:
            print(f"No video with id={args.id}")
            return

    for v in videos:
        slug = v["sujet"].lower().replace(" ", "-")
        print(f"\n{'='*60}")
        print(f"  Video {v['id']} — {v['sujet']} ({v['categorie']})")
        print(f"{'='*60}")

        if args.preview:
            png = os.path.join(OUTPUT_DIR, f"preview-{v['id']}-{args.preview}.png")
            preview_scene(args.preview, v, settings, png)
        else:
            mp4 = os.path.join(OUTPUT_DIR, f"video-{v['id']}-{slug}.mp4")
            generate_video(v, settings, mp4)

    print("\nAll done.")


if __name__ == "__main__":
    main()
