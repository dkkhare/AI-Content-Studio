# Milestone 24 — automatic long-form talking-head podcast series

## Goal

Generate a resumable series of talking-head podcast videos from the complete
book, a writer portrait, and a consented reference-voice sample.

A 300-page book must **not** be summarized into one 15-minute video. The complete
book content is preserved and divided into as many approximately 15-minute
episodes as necessary. Logical chapter, section, scene, paragraph, and sentence
boundaries take priority over hitting exactly 15:00.

## Required outputs

The project produces a series directory such as:

- `episode-001-chapter-title.mp4`
- `episode-002-next-section.mp4`
- `episode-003-continuation.mp4`
- `series.json` with order, title, source range, duration, status, and checksums
- optional `playlist.m3u8`, subtitles, narration WAV files, and thumbnails

No imported chapter may silently disappear. The series manifest records source
coverage so the application can detect omissions, duplicates, and ordering
errors.

## Pipeline

1. Import and extract the complete book text while retaining chapter/section
   structure.
2. Normalize only formatting noise; do not summarize or rewrite the work unless
   the user explicitly selects an adaptation mode.
3. Estimate spoken duration and group the source into approximately 15-minute
   episodes at logical boundaries.
4. Divide each episode into GPU-safe 30–60 second render segments.
5. Generate reference-voice narration for each segment with F5-TTS.
6. Generate a SadTalker MP4 for each narration segment.
7. Checkpoint every completed segment and episode.
8. Resume after cancellation or failure without regenerating valid outputs.
9. Concatenate segments into each numbered episode with FFmpeg.
10. Validate source coverage, media duration, ordering, and output files before
    registering the complete series in the project.

## Episode splitting rules

- Default target: 15 minutes.
- Configurable target range: 5–60 minutes.
- Prefer a chapter boundary near the target.
- Otherwise prefer section, scene, paragraph, then sentence boundaries.
- Never split a word or sentence solely to reach an exact duration.
- Permit shorter episodes at chapter ends.
- Permit modestly longer episodes when that preserves a logical passage.
- Long chapters continue across numbered episodes with clear continuation
  titles.
- Front matter, notes, footnotes, references, and appendices remain selectable;
  the UI records any content the user intentionally excludes.

## Runtime boundaries

SadTalker is an optional external runtime and is not imported into the desktop
Python process. The application invokes its `inference.py` with an argument list
and no shell. This avoids dependency conflicts between SadTalker's older stack,
PySide, F5-TTS, and the packaged application.

Recommended low-VRAM defaults for a 4 GB NVIDIA GPU:

- 256 model size
- crop preprocessing
- 30–45 second render segments
- enhancer disabled
- one segment at a time

## Recovery and validation

The application maintains two checkpoint levels:

- render segment: narration WAV and SadTalker MP4
- episode: ordered segments and assembled episode MP4

Restarting resumes at the first missing or invalid segment. Changing the book,
voice sample, transcript, portrait, episode plan, or generation settings
invalidates only affected outputs. A final coverage report must prove that every
selected source block appears exactly once in the episode plan.

## Safety and rights

The UI must require confirmation that the user has permission to use the
portrait, book content, and voice sample. Generated videos must be presented as
synthetic media and must not be used for impersonation or deception.

## Current delivery

The backend foundation includes bounded SadTalker execution, automatic
sentence-boundary render segmentation, F5-TTS orchestration, segment manifests,
resumption, cancellation checks, atomic segment output, FFmpeg concatenation,
and model-free regression tests.

Remaining delivery:

- structure-preserving PDF/book extraction
- logical multi-episode planner and complete-source coverage validation
- one MP4 per approximately 15-minute episode plus series manifest
- writer portrait, reference audio, and exact transcript inputs
- SadTalker installation/path preflight
- progress, cancel, resume, and failed-segment/episode retry
- project series registration and final duration/media validation
- Talking Head Series desktop tab
