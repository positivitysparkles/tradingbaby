#!/usr/bin/env python3
"""
make_video.py — W118 Flashcard Training Video Generator

Reads card_stories.md + card_NN_*.png images, generates TTS narration
for each card, and outputs a single MP4 video.

Usage:
    pip install moviepy gtts pillow
    python training/flashcards/make_video.py

Output: training/flashcards/w118_training_video.mp4
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path


# ── Parse card_stories.md ─────────────────────────────────────────────────────

def parse_cards(md_path: Path) -> list[dict]:
    text = md_path.read_text()
    cards = []

    # Split on "## Card NN" headers, capturing the number
    parts = re.split(r'\n## Card (\d+)', text)
    # parts[0] = preamble, then pairs: (num, content)

    i = 1
    while i < len(parts) - 1:
        num = parts[i].zfill(2)
        content = parts[i + 1]
        i += 2

        # Topic: first line looks like " — The 6 Entry Conditions"
        first_line = content.split('\n')[0]
        topic = first_line.split('—', 1)[-1].strip() if '—' in first_line else first_line.strip()

        # Story title: **bold text**
        title_match = re.search(r'\*\*(.+?)\*\*', content)
        story_title = title_match.group(1) if title_match else ''

        # Story body: strip markdown, cut at --- (separator/footer)
        body = content
        body = re.sub(r'^[^\n]*—[^\n]*\n', '', body)          # remove topic line
        body = re.sub(r'\*\*.*?\*\*', '', body)                # remove bold markers
        body = re.sub(r'\n---.*', '', body, flags=re.DOTALL)   # cut at separator
        body = re.sub(r'\*[^*]+\*', '', body)                  # remove italics
        body = re.sub(r'\s+', ' ', body).strip()               # collapse whitespace

        narration = f"Card {int(num)}. {topic}. {story_title}. {body}"

        cards.append({
            'num': num,
            'topic': topic,
            'story_title': story_title,
            'narration': narration,
        })

    return cards


# ── Find card image ───────────────────────────────────────────────────────────

def find_image(cards_dir: Path, num: str) -> Path | None:
    matches = list(cards_dir.glob(f"card_{num}_*.png"))
    return matches[0] if matches else None


# ── Build video ───────────────────────────────────────────────────────────────

def make_video(cards: list[dict], cards_dir: Path, output_path: Path):
    from moviepy import (
        ImageClip, AudioFileClip, ColorClip,
        CompositeVideoClip, concatenate_videoclips, vfx
    )

    VIDEO_W, VIDEO_H = 1280, 720
    PAUSE_AFTER = 1.5   # seconds of silence after each card's narration
    FADE       = 0.5    # fade in/out duration

    tmp = Path(tempfile.mkdtemp())
    clips = []

    for card in cards:
        num = card['num']
        print(f"  Card {num} — {card['topic']}")

        img_path = find_image(cards_dir, num)
        if not img_path:
            print(f"    ⚠  No image found, skipping")
            continue

        # Text-to-speech via espeak-ng (offline, no internet needed)
        audio_path = tmp / f"card_{num}.wav"
        subprocess.run([
            'espeak-ng',
            '-w', str(audio_path),
            '-s', '145',   # speed (words per minute)
            '-p', '52',    # pitch
            '-a', '180',   # amplitude
            card['narration']
        ], check=True, capture_output=True)

        audio    = AudioFileClip(str(audio_path))
        duration = audio.duration + PAUSE_AFTER

        # Image — fit inside VIDEO_W × VIDEO_H, centred on dark background
        img = ImageClip(str(img_path)).with_duration(duration)
        if img.w / img.h > VIDEO_W / VIDEO_H:
            img = img.resized(width=VIDEO_W)
        else:
            img = img.resized(height=VIDEO_H)

        bg   = ColorClip((VIDEO_W, VIDEO_H), color=(13, 17, 23)).with_duration(duration)
        comp = CompositeVideoClip([bg, img.with_position('center')])
        comp = comp.with_audio(audio)
        comp = comp.with_effects([vfx.FadeIn(FADE), vfx.FadeOut(FADE)])

        clips.append(comp)

    if not clips:
        print("No clips were generated — check that card images exist.")
        return

    print(f"\nConcatenating {len(clips)} clips…")
    final = concatenate_videoclips(clips, method='compose')

    print(f"Writing {output_path.name}…")
    final.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile=str(tmp / 'tmp_audio.m4a'),
        remove_temp=True,
        logger='bar',
    )

    # Clean up temp audio files
    for f in tmp.glob('*.mp3'):
        f.unlink(missing_ok=True)

    print(f"\n✅  Done!  →  {output_path}")
    print(f"    Duration: ~{int(final.duration // 60)}m {int(final.duration % 60)}s")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    here        = Path(__file__).parent
    md_path     = here / 'card_stories.md'
    output_path = here / 'w118_training_video.mp4'

    print("W118 Flashcard Video Generator")
    print("=" * 40)

    print("Parsing card stories…")
    cards = parse_cards(md_path)
    print(f"Found {len(cards)} cards\n")
    for c in cards:
        print(f"  {c['num']} — {c['topic']} ({c['story_title']})")

    print("\nGenerating video clips (this takes a few minutes)…")
    make_video(cards, here, output_path)


if __name__ == '__main__':
    main()
