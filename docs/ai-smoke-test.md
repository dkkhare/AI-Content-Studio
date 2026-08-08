# Milestone 13 live AI smoke test

The automated test suite uses fake HTTP transports and never spends provider credits.
Use this command manually to verify a real provider after installing/configuring it.

## Ollama

```powershell
ollama serve
ollama pull qwen2.5:3b
python scripts/ai_smoke.py --provider ollama --model qwen2.5:3b
```

Hindi spelling and grammar:

```powershell
python scripts/ai_smoke.py --provider ollama --model qwen2.5:3b --hindi-proof --prompt "मुझे किताब पढ़ना हैं।"
```

## OpenAI

Set `OPENAI_API_KEY` in the process environment, then run:

```powershell
python scripts/ai_smoke.py --provider openai --model YOUR_MODEL
```

## Gemini

Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), then run:

```powershell
python scripts/ai_smoke.py --provider gemini --model YOUR_MODEL
```

Add `--stream` to exercise streaming. The command prints one JSON result and exits
with code 0 on success, 2 when the provider health check fails, or 3 for an empty response.
It never prints configured API keys.
