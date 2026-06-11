#!/usr/bin/env python3
"""Minimal client for a local Ollama server. Standard library only.

Connects to http://127.0.0.1:11434 by default; override with the
OLLAMA_HOST environment variable (same variable the ollama CLI uses).

Usage:
    python3 ollama_client.py --check              # verify connection
    python3 ollama_client.py "your prompt"        # chat (first model)
    python3 ollama_client.py "your prompt" MODEL  # chat with a model
"""

import json
import os
import sys
import urllib.error
import urllib.request


def base_url() -> str:
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    if "://" not in host:
        host = "http://" + host
    return host.rstrip("/")


def _request(path: str, payload: dict | None = None) -> dict:
    url = base_url() + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def version() -> str:
    return _request("/api/version")["version"]


def models() -> list[str]:
    return [m["model"] for m in _request("/api/tags")["models"]]


def chat(prompt: str, model: str, system: str | None = None) -> str:
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    resp = _request(
        "/api/chat", {"model": model, "messages": messages, "stream": False}
    )
    return resp["message"]["content"]


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    try:
        if args[0] == "--check":
            print(f"Connected to Ollama {version()} at {base_url()}")
            available = models()
            if available:
                print("Models:", ", ".join(available))
            else:
                print("Models: none installed (run `ollama pull <model>`)")
            return 0

        prompt = args[0]
        if len(args) > 1:
            model = args[1]
        else:
            available = models()
            if not available:
                print(
                    "No models installed. Run `ollama pull <model>` first.",
                    file=sys.stderr,
                )
                return 1
            model = available[0]
        print(chat(prompt, model))
        return 0
    except urllib.error.URLError as exc:
        print(
            f"Could not reach Ollama at {base_url()}: {exc.reason}\n"
            "Is the server running? Try: ollama serve "
            "(or ./scripts/ollama-up.sh)",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
