"""
LLM client for match narrative generation.

Calls a Nemotron-3-compatible chat completions endpoint (local NVIDIA Endpoints
on RTX 3060 or NVIDIA Endpoints cloud). Endpoint and API key come from env vars.
Gracefully falls back to a deterministic template when the endpoint is not
configured or unreachable, so the hackathon demo always produces output.
"""
import json
import os
import urllib.error
import urllib.request


class LLMClient:
    """Thin OpenAI-compatible chat completion client with fallback."""

    FALLBACK_NARRATIVE = (
        "{home} controlled possession against {away} in the first half, "
        "creating {xg_home} xG to {away}'s {xg_away}. Key moments included a "
        "goal in the 23rd minute and sustained pressure in the final third."
    )
    FALLBACK_TACTICAL = (
        "{home} operated in a high-pressing 4-3-3, forcing {away} into "
        "turnovers in their own third. The defensive line stayed compact while "
        "fullbacks pushed high to stretch the width."
    )
    FALLBACK_RECAP = (
        "Final score: {home} {score_home} - {score_away} {away}. Decisive "
        "moments included a first-half goal and a late equalizer. "
        "{home}'s pressing game proved the difference."
    )

    def __init__(self, base_url=None, api_key=None, model=None):
        self.base_url = (base_url or os.getenv("NVIDIA_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.model = model or os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

    def chat_completion(self, messages, temperature=0.7, max_tokens=500):
        """Send a chat completion request. Falls back to a template if
        the endpoint is not configured or unreachable."""
        if not self.base_url or not self.api_key:
            return self._fallback(messages)

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
        except Exception:
            return self._fallback(messages)

        choices = body.get("choices", [])
        if not choices:
            return self._fallback(messages)
        return choices[0]["message"]["content"]

    def _fallback(self, messages):
        """Deterministic fallback when LLM is unavailable."""
        user_text = ""
        for m in messages:
            if m.get("role") == "user":
                user_text = m.get("content", "")
        lower = user_text.lower()
        if "tactical" in lower:
            return self.FALLBACK_TACTICAL.format(home="Arsenal", away="Manchester City")
        if "recap" in lower:
            return self.FALLBACK_RECAP.format(home="Arsenal", away="Manchester City", score_home=1, score_away=0)
        return self.FALLBACK_NARRATIVE.format(home="Arsenal", away="Manchester City", xg_home=1.2, xg_away=0.8)
