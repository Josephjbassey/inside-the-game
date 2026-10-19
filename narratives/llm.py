"""
LLM client for match narrative generation.

Calls a Nemotron-3-compatible chat completions endpoint (local NVIDIA Endpoints
on RTX 3060 or NVIDIA Endpoints cloud). Endpoint and API key come from env vars.
"""
import json
import os
import urllib.error
import urllib.request


class LLMClient:
    """Thin OpenAI-compatible chat completion client."""

    def __init__(self, base_url=None, api_key=None, model=None):
        self.base_url = (base_url or os.getenv("NVIDIA_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.model = model or os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
        if not self.base_url:
            raise ValueError("NVIDIA_API_BASE must be set (e.g. http://localhost:8080/v1)")

    def chat_completion(self, messages, temperature=0.7, max_tokens=500):
        """Send a chat completion request and return the assistant message text."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        choices = body.get("choices", [])
        if not choices:
            raise RuntimeError(f"LLM returned no choices: {body}")
        return choices[0]["message"]["content"]
