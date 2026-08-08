from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.tts.pipeline import TTSPipeline


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run an opt-in live F5-TTS narration smoke test."
    )
    parser.add_argument("--reference-audio", required=True)
    parser.add_argument("--reference-text", required=True)
    parser.add_argument("--text", default="नमस्ते, AI Content Studio तैयार है।")
    parser.add_argument("--output", default="output/tts-smoke")
    parser.add_argument("--language", default="hi")
    parser.add_argument("--keep-chunks", action="store_true")
    return parser


def run(args, *, pipeline=None, stdout=None):
    stdout = stdout or sys.stdout
    reference = Path(args.reference_audio)
    output = Path(args.output)
    if not reference.is_file():
        print(json.dumps({"ok": False, "error": "reference audio not found"}), file=stdout)
        return 2
    if not str(args.reference_text).strip() or not str(args.text).strip():
        print(json.dumps({"ok": False, "error": "reference and generation text are required"}), file=stdout)
        return 2

    pipeline = pipeline or TTSPipeline(output)
    session = pipeline.create_session(
        reference_audio=reference,
        reference_text=args.reference_text,
        text=args.text,
        output_directory=output,
        language=args.language,
    )
    try:
        result = pipeline.run(session)
        target = Path(result.output_file)
        if result.status != "Completed" or not target.is_file():
            raise RuntimeError("TTS pipeline did not produce an output file.")
        print(json.dumps({
            "ok": True,
            "session_id": result.id,
            "output": str(target),
            "duration_seconds": result.duration,
            "chunks": len(result.generated_chunks),
            "language": result.language,
        }, ensure_ascii=False), file=stdout)
        return 0
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "session_id": session.id,
            "status": session.status,
            "error": str(exc),
        }, ensure_ascii=False), file=stdout)
        return 3
    finally:
        if not args.keep_chunks:
            pipeline.cleanup_chunks(session)
        pipeline.shutdown()


def main(argv=None):
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
