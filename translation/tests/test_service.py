import json
from unittest.mock import patch

from django.test import SimpleTestCase

from translation.service import TranslatorService


FAKE_BODY = [{"translations": [{"text": "Arsenal presiona alto."}]}]


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(FAKE_BODY).encode("utf-8")


class TranslatorServiceTests(SimpleTestCase):
    @patch("translation.service.urllib.request.urlopen")
    def test_translate_returns_translated_text(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse()
        svc = TranslatorService(
            key="fake-key",
            endpoint="https://api.cognitive.microsofttranslator.com",
            region="westus2",
        )
        result = svc.translate("Arsenal presses high.", "es")
        self.assertEqual(result, "Arsenal presiona alto.")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.method, "POST")
        headers = {k.lower(): v for k, v in req.header_items()}
        self.assertEqual(headers["ocp-apim-subscription-key"], "fake-key")

    def test_translate_returns_original_when_unconfigured(self):
        svc = TranslatorService(key="", endpoint="")
        result = svc.translate("Arsenal presses high.", "es")
        self.assertEqual(result, "Arsenal presses high.")
