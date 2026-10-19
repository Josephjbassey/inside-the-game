"""
LLM client for match narrative generation.

Calls a Nemotron-3-compatible chat completions endpoint (local NVIDIA Endpoints
on RTX 3060 or NVIDIA Endpoints cloud) OR an Azure OpenAI endpoint.
Endpoint and API key come from env vars. Gracefully falls back to a
deterministic template when the endpoint is not configured or unreachable, so
the hackathon demo always produces output.
"""
import json
import os
import urllib.error
import urllib.request


class LLMClient:
    """Thin OpenAI-compatible chat completion client with fallback.

    Supports both generic OpenAI-compatible endpoints and Azure OpenAI.
    For Azure OpenAI, set base_url to your Azure OpenAI resource endpoint
    (e.g. https://<resource>.openai.azure.com) and provide the deployment
    name via model or the AZURE_OPENAI_DEPLOYMENT env var.
    Authentication uses the ``api-key`` header for Azure, ``Bearer``
    otherwise.
    """

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

    def __init__(self, base_url=None, api_key=None, model=None, api_version=None):
        # Support Azure-specific env var names as aliases.
        env_base = base_url or os.getenv("NVIDIA_API_BASE", "") or os.getenv(
            "AZURE_OPENAI_ENDPOINT", ""
        )
        env_key = api_key or os.getenv("NVIDIA_API_KEY", "") or os.getenv(
            "AZURE_OPENAI_API_KEY", ""
        )
        env_model = model or os.getenv("NVIDIA_MODEL", "") or os.getenv(
            "AZURE_OPENAI_DEPLOYMENT", ""
        )
        self.base_url = env_base.rstrip("/")
        self.api_key = env_key
        self.model = env_model
        self.api_version = api_version or os.getenv(
            "AZURE_OPENAI_API_VERSION", "2024-02-01"
        )
        self.is_azure = "openai.azure.com" in self.base_url

    def _build_url(self):
        if self.is_azure:
            if not self.model:
                raise ValueError(
                    "Azure OpenAI requires a model deployment name "
                    "(set NVIDIA_MODEL or AZURE_OPENAI_DEPLOYMENT)"
                )
            return (
                f"{self.base_url}/openai/deployments/{self.model}"
                f"/chat/completions?api-version={self.api_version}"
            )
        return f"{self.base_url}/chat/completions"

    def _build_headers(self):
        if self.is_azure:
            return {
                "Content-Type": "application/json",
                "api-key": self.api_key,
            }
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def chat_completion(self, messages, temperature=0.7, max_tokens=500):
        """Send a chat completion request. Falls back to a template if
        the endpoint is not configured or unreachable."""
        if not self.base_url or not self.api_key:
            return self._fallback(messages)

        url = self._build_url()
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
            headers=self._build_headers(),
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
            return self.FALLBACK_RECAP.format(
                home="Arsenal", away="Manchester City", score_home=1, score_away=0
            )
        return self.FALLBACK_NARRATIVE.format(
            home="Arsenal", away="Manchester City", xg_home=1.2, xg_away=0.8
        )
