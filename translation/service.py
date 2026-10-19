"""
Azure AI Translator client.

Translates text between languages using the Azure AI Translator REST API.
Subscription key and endpoint come from env vars. Gracefully returns the
original text when credentials are not configured.
"""
import json
import os
import urllib.error
import urllib.request


class TranslatorService:
    def __init__(self, key=None, endpoint=None, region=None):
        self.key = key or os.getenv("AZURE_TRANSLATOR_KEY", "")
        self.endpoint = (endpoint or os.getenv("AZURE_TRANSLATOR_ENDPOINT", "")).rstrip("/")
        self.region = region or os.getenv("AZURE_TRANSLATOR_REGION", "")

    def translate(self, text, to_language, from_language=None):
        """Translate text to to_language. Returns original text if unconfigured or on error."""
        if not text:
            return ""
        if not self.key or not self.endpoint:
            return text
        params = f"?api-version=3.0&to={to_language}"
        if from_language:
            params += f"&from={from_language}"
        url = self.endpoint + "/translate" + params
        body = json.dumps([{"text": text}]).encode("utf-8")
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/json",
        }
        if self.region:
            headers["Ocp-Apim-Subscription-Region"] = self.region
        req = urllib.request.Request(
            url, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError):
            return text
        return result[0]["translations"][0]["text"]
