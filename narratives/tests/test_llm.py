"""
TDD: LLM client tests.

These tests fail before narratives/llm.py exists, then pass after import.
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
        headers = dict(req.header_items())
        self.assertEqual(headers["Authorization"], "Bearer test-key")
