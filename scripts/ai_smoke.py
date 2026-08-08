from __future__ import annotations

import argparse
import json
import sys

from backend.ai import AIManager, AIRequest, collect_stream


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an opt-in live AI provider smoke test.")
    parser.add_argument("--provider", choices=("ollama", "openai", "gemini"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", default="Reply with exactly: AI Content Studio OK")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--hindi-proof", action="store_true")
    return parser


def run(args, *, manager=None, stdout=None) -> int:
    manager = manager or AIManager()
    stdout = stdout or sys.stdout
    healthy, detail = manager.health_check(args.provider)
    if not healthy:
        print(json.dumps({"ok": False, "provider": args.provider, "error": detail}, ensure_ascii=False), file=stdout)
        return 2

    if args.hindi_proof:
        spelling = manager.execute_prompt(
            "hindi_spelling_correction",
            {"text": args.prompt},
            provider_id=args.provider,
            model=args.model,
        )
        response = manager.execute_prompt(
            "hindi_grammar_correction",
            {"text": spelling.text},
            provider_id=args.provider,
            model=args.model,
        )
        text = response.text
        usage = response.usage
    elif args.stream:
        request = AIRequest.from_prompt(args.prompt, model=args.model)
        chunks = list(manager.stream(request, provider_id=args.provider))
        text = collect_stream(chunks)
        usage = next((chunk.usage for chunk in reversed(chunks) if chunk.usage is not None), None)
    else:
        response = manager.generate(
            AIRequest.from_prompt(args.prompt, model=args.model),
            provider_id=args.provider,
        )
        text = response.text
        usage = response.usage

    if not text.strip():
        print(json.dumps({"ok": False, "provider": args.provider, "error": "empty response"}), file=stdout)
        return 3

    print(json.dumps({
        "ok": True,
        "provider": args.provider,
        "model": args.model,
        "text": text,
        "usage": {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        },
    }, ensure_ascii=False), file=stdout)
    return 0


def main(argv=None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
