import json
import os
import time


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
REQUEST_TIMEOUT = 60


def _ollama_url(path: str) -> str:
    return f"{OLLAMA_HOST}/api/{path}"


def _generate(prompt: str, model: str = None, system: str = None, **opts) -> str:
    model = model or DEFAULT_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        **opts,
    }
    if system:
        payload["system"] = system

    import urllib.request
    import urllib.error

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _ollama_url("generate"),
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except urllib.error.URLError as exc:
        raise ConnectionError(f"Ollama unavailable at {OLLAMA_HOST}: {exc}")
    except Exception as exc:
        raise RuntimeError(f"Ollama generation failed: {exc}")


def chat(messages: list[dict], model: str = None, **opts) -> str:
    """Send a chat request to Ollama.

    Args:
        messages: [{"role": "user"|"system"|"assistant", "content": "..."}]
        model: Model name (default: llama3.2:latest)
        **opts: Additional options (temperature, etc.)

    Returns:
        Assistant's response text
    """
    model = model or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        **opts,
    }

    import urllib.request

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _ollama_url("chat"),
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("message", {}).get("response", "").strip()
    except Exception as exc:
        raise RuntimeError(f"Ollama chat failed: {exc}")


def check_ollama_status() -> dict:
    """Check if Ollama is running and which models are available."""
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/tags",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "available": True,
                "models": [m.get("name") for m in data.get("models", [])],
                "default": DEFAULT_MODEL,
            }
    except Exception:
        return {
            "available": False,
            "models": [],
            "default": DEFAULT_MODEL,
        }


def pull_model(model: str = None, timeout: int = 300) -> bool:
    """Pull a model from Ollama registry."""
    model = model or DEFAULT_MODEL
    payload = {"name": model}

    import urllib.request

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _ollama_url("pull"),
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False