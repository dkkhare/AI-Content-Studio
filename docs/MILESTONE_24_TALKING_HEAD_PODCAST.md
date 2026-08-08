# Milestone 24 — automatic long-form talking-head podcast

## Goal

Generate a resumable talking-head podcast from a book-derived script, a writer
portrait, and a consented reference-voice sample.

A 300-page book cannot be narrated completely in 15 minutes. The 15-minute mode
therefore creates a podcast summary/script; it does not represent the output as
a complete audiobook.

## Pipeline

1. Import/extract book text.
2. Create and review a target-length podcast script.
3. Generate short reference-voice narration segments with F5-TTS.
4. Generate a SadTalker MP4 for each 30–60 second narration segment.
5. Checkpoint every completed segment.
6. Resume after cancellation or failure without regenerating valid segments.
7. Concatenate segments with FFmpeg and register the final MP4 in the project.

## Runtime boundaries

SadTalker is an optional external runtime and is not imported into the desktop
Python process. The application invokes its `inference.py` with an argument list
and no shell. This avoids dependency conflicts between SadTalker's older stack,
PySide, F5-TTS, and the packaged application.

Recommended low-VRAM defaults for a 4 GB NVIDIA GPU:

- 256 model size
- crop preprocessing
- 30–45 second segments
- enhancer disabled
- one segment at a time

## Safety and rights

The UI must require confirmation that the user has permission to use the
portrait, book content, and voice sample. Generated videos must be presented as
synthetic media and must not be used for impersonation or deception.

## Current delivery

The backend foundation includes bounded SadTalker execution, automatic
sentence-boundary chunking, F5-TTS orchestration, per-segment manifests,
resumption, cancellation checks, atomic segment output, FFmpeg concatenation,
and model-free regression tests.

Remaining UI delivery:

- book/script selector and target-duration controls
- writer portrait, reference audio, and exact transcript inputs
- SadTalker installation/path preflight
- progress, cancel, resume, and failed-segment retry
- project output registration and final duration validation
- document summarization with provider/token-budget handling
