"""
TDD: LLM client tests.
"""
import json
from unittest.mock import patch

from django.test import SimpleTestCase

from narratives.llm import LLMClient


FAKE_BODY = {"choices": [{"message": {"content": "Arsenal presses high."}}]}


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(FAKE_BODY).encode("utf-8")


class LLMClientTests(SimpleTestCase):
    @patch("narratives.llm.urllib.request.urlopen")
    def test_chat_completion_returns_content(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse()
        client = LLMClient(
            base_url="http://localhost:8080/v1",
            api_key="test-key",
            model="test-model",
        )
        result = client.chat_completion([{"role": "user", "content": "say hi"}])
        self.assertEqual(result, "Arsenal presses high.")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.method, "POST")
        headers = {k.lower(): v for k, v in req.header_items()}
        self.assertEqual(headers["authorization"], "Bearer test-key")

    def test_chat_completion_falls_back_when_unconfigured(self):
        client = LLMClient(base_url="", api_key="")
        result = client.chat_completion([{"role": "user", "content": "narrative"}])
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_chat_completion_falls_back_when_endpoint_down(self):
        with patch(
            "narratives.llm.urllib.request.urlopen", side_effect=Exception("connection refused")
        ):
            client = LLMClient(
                base_url="http://localhost:8080/v1", api_key="test-key"
            )
            result = client.chat_completion([{"role": "user", "content": "tactical"}])
            self.assertIn("pressing", result.lower())

    def test_azure_url_uses_deployment_and_api_key_header(self):
        client = LLMClient(
            base_url="https://myresource.openai.azure.com",
            api_key="azure-key",
            model="my-deployment",
            api_version="2024-02-01",
        )
        self.assertTrue(client.is_azure)
        url = client._build_url()
        self.assertIn("/openai/deployments/my-deployment/chat/completions", url)
        self.assertIn("api-version=2024-02-01", url)
        headers = client._build_headers()
        self.assertEqual(headers["api-key"], "azure-key")

    def test_azure_url_uses_env_deployment(self):
        import os

        os.environ["AZURE_OPENAI_DEPLOYMENT"] = "env-deployment"
        try:
            client = LLMClient(
                base_url="https://myresource.openai.azure.com",
                api_key="azure-key",
            )
            self.assertTrue(client.is_azure)
            url = client._build_url()
            self.assertIn("/openai/deployments/env-deployment/chat/completions", url)
        finally:
            del os.environ["AZURE_OPENAI_DEPLOYMENT"]
