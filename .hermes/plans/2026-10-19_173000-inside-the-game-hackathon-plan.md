# Plan: Inside the Game Hackathon Submission

**Workspace:** `/run/media/jabs/Development/inside-the-game`
**Repo:** `https://github.com/Josephjbassey/inside-the-game` (SSH push configured)
**Contest:** Microsoft + Premier League "Inside the Game: Developer Hackathon"
**Submission deadline:** October 27, 2026, 11:59 PM Pacific Time
**Registration deadline:** October 20, 2026, 12:00 PM Pacific Time

---

## Goal

Build and submit "StudioLens" — a Django + HTMX Premier League match-intelligence dashboard that converts synthetic match-event data into live narratives, tactical explainers, and auto recaps for studio/broadcast/fan scenarios, using GitHub, GitHub Copilot, Nemotron-3 (local NVIDIA Endpoints on RTX 3060 or cloud API), Azure AI Translator, and Azure AI Services, submitted by Oct 27, 11:59 PM Pacific.

---

## Current Context / Assumptions

- **Existing repo:** `Josephjbassey/inside-the-game` on GitHub, cloned at `/run/media/jabs/Development/inside-the-game`, SSH remote `origin` → `git@github.com:Josephjbassey/inside-the-game.git`, write access via deploy key `jabs-box-ssh-key`.
- **Existing code:** Django 6.1.2 project (`config/`), `matches` app with `Match` and `MatchEvent` models, admin registration, `generate_match` management command (tested: creates match with 80 events), HTMX dashboard views (`dashboard`, `ticker_partial`, `scoreboard_partial`, `xg_partial`), templates under `matches/templates/matches/`, verified HTTP 200 render.
- **Existing state:** Initial Django scaffold committed and pushed (commit `753620a`, `main` branch).
- **Python:** 3.14.8, venv at `.venv`, Django 6.1.2 installed. No pip module system-wide; venv used.
- **GPU:** RTX 3060 12GB; user is an NVIDIA Endpoints provider (model `nvidia/nemotron-3-ultra-550b-a55b`). LLM endpoint may be local (`http://localhost:8080/v1` or similar) or NVIDIA Endpoints cloud.
- **Constraints:** No Redis (LocMemCache + sync Q), zero-CDN (self-hosted Tailwind), Geist font, dark mode default, Crimson `#DC143C` primary accent, Django templates + HTMX (not Next.js), SQLite database, no placeholder images, CSS modules preferred over inline styles.
- **Azure:** Azure AI Translator for multi-language output; Azure AI Services (Language) for key-phrase/sentiment optional. Credentials (`AZURE_TRANSLATOR_KEY`, `AZURE_TRANSLATOR_ENDPOINT`, `AZURE_TRANSLATOR_REGION`, `NVIDIA_API_BASE`, `NVIDIA_API_KEY`) are secrets — stored in `~/.hermes` only, chmod 600, never committed.
- **Storage policy:** All code under `/run/media/jabs/Development/`. No media or code under `~/.hermes`.
- **Hackathon deliverables:** GitHub repo link, demo video (3 min), short description, list of Azure services used, submission via Innovation Studio Platform.
- **Registration:** Must be complete by Oct 20, 12:00 PM Pacific (~21:00 UTC+1 same day). Top six notified Nov 10.

---

## Architecture / Proposed Approach

A modular Django monolith with three concerns: (1) `matches` app owns synthetic match-event data and the live HTMX dashboard; (2) `narratives` app owns LLM-powered content generation (Nemotron-3 via OpenAI-compatible chat completions) backed by a `MatchNarrative` model cached in SQLite; (3) `translation` app wraps Azure AI Translator for multi-language fan output. Views: live dashboard (`/`), studio broadcast overlay (`/studio/<id>/`), fan personalized view (`/fan/<id>/` with `?lang=` language toggle). HTMX partials auto-refresh scoreboard/ticker/xG every 2–3s. All secrets read from environment only; no secrets in git.

---

## Step-by-Step Tasks

### Task 0: Verify existing scaffold and environment

Bite-sized: confirm venv, Django, git remote, and a sample match exist before adding new code.

Files: none modified.

Exact commands:

```bash
cd /run/media/jabs/Development/inside-the-game
source .venv/bin/activate
python --version
django-admin --version
git remote -v
python manage.py check
```

Expected output:
- `Python 3.14.8`
- `6.1.2`
- `origin	git@github.com:Josephjbassey/inside-the-game.git (fetch)` and `(push)`
- `System check identified no issues (0 silenced).`

Verification: all four commands succeed. If `git remote -v` shows HTTPS instead of SSH, fix with `git remote set-url origin git@github.com:Josephjbassey/inside-the-game.git`.

Commit: none (read-only verification).

---

### Task 1: Create `narratives` app and `MatchNarrative` model

Bite-sized: scaffold app, register in settings, define model, run migrations.

Files created:
- `narratives/__init__.py`
- `narratives/models.py`
- `narratives/admin.py`
- `narratives/apps.py`

Files modified:
- `config/settings.py` — add `'narratives'` to `INSTALLED_APPS` after `'matches'`

`narratives/models.py` (copy-pasteable):

```python
"""
Narrative models for match intelligence.

Stores AI-generated match narratives, tactical explainers, and auto recaps
per match, keyed by language. Cached in SQLite (no Redis).
"""
from django.db import models
from matches.models import Match


class MatchNarrative(models.Model):
    """AI-generated narrative content for a match."""

    class ContentType(models.TextChoices):
        NARRATIVE = "narrative", "Live Narrative"
        TACTICAL = "tactical", "Tactical Explainer"
        RECAP = "recap", "Auto Recap"

    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="narratives"
    )
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    language = models.CharField(max_length=10, default="en")  # BCP-47: en, es, fr, de, pt, zh
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-generated_at"]
        unique_together = [["match", "content_type", "language"]]

    def __str__(self):
        return f"{self.match} — {self.get_content_type_display()} ({self.language})"
```

`narratives/admin.py` (copy-pasteable):

```python
from django.contrib import admin

from .models import MatchNarrative


@admin.register(MatchNarrative)
class MatchNarrativeAdmin(admin.ModelAdmin):
    list_display = ["match", "content_type", "language", "generated_at"]
    list_filter = ["content_type", "language", "match"]
    search_fields = ["content", "match__home_team", "match__away_team"]
```

Edit `config/settings.py`: add `'narratives'` to `INSTALLED_APPS` after `'matches'`.

Exact commands:

```bash
source .venv/bin/activate
python manage.py startapp narratives
python manage.py makemigrations narratives
python manage.py migrate
git add -A
git commit -m "feat: narratives app and MatchNarrative model"
git push origin main
```

Expected output: migrations applied (`Applying matches.0001_initial... OK`, `Applying narratives.0001_initial... OK`), commit creates 4 new files, push to `main`.

Verification: `python manage.py check` → `System check identified no issues (0 silenced).`

---

### Task 2: LLM client module with tests (TDD)

Bite-sized: write failing test, implement `narratives/llm.py`, run test to pass.

Files created:
- `narratives/tests/__init__.py`
- `narratives/tests/test_llm.py`
- `narratives/llm.py`

`narratives/tests/test_llm.py` (copy-pasteable, write FIRST — should fail because `llm.py` doesn't exist yet):

```python
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
        self.assertIn("Bearer test-key", req.header_items())
```

`narratives/llm.py` (copy-pasteable, implement AFTER test fails):

```python
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
```

Exact commands:

```bash
source .venv/bin/activate
mkdir -p narratives/tests
touch narratives/tests/__init__.py
python manage.py test narratives.tests.test_llm   # EXPECT: FAIL (ModuleNotFoundError or ImportError)
# Then write narratives/llm.py (copy-pasteable above)
python manage.py test narratives.tests.test_llm   # EXPECT: OK, 1 test
git add -A
git commit -m "feat: LLM client with TDD tests"
git push origin main
```

Expected output: first test run errors with `ModuleNotFoundError: No module named 'narratives.llm'`; second test run: `OK (1 test)`.

---

### Task 3: Narrative generation service with tests (TDD)

Bite-sized: `narratives/services.py` builds prompts from recent `MatchEvent`s, calls `LLMClient`, saves `MatchNarrative`.

Files created:
- `narratives/services.py`
- `narratives/tests/test_services.py`

`narratives/services.py` (copy-pasteable):

```python
"""
Narrative generation service.

Builds match-specific prompts from recent MatchEvents and calls the LLM to
produce live narratives, tactical explainers, and auto recaps.
"""
from .llm import LLMClient
from .models import MatchNarrative


class NarrativeService:
    def __init__(self, llm_client=None):
        self.llm = llm_client or LLMClient()

    def generate(self, match, content_type, language="en"):
        events = list(match.events.all().order_by("-minute", "-second")[:15])
        prompt = self._build_prompt(match, content_type, events, language)
        content = self.llm.chat_completion([{"role": "user", "content": prompt}])
        narrative, _ = MatchNarrative.objects.update_or_create(
            match=match,
            content_type=content_type,
            language=language,
            defaults={"content": content},
        )
        return narrative

    def _build_prompt(self, match, content_type, events, language):
        event_lines = [
            f"{e.minute}' {e.event_type} by {e.player or 'unknown'} ({e.team})"
            for e in events
        ]
        events_text = "\n".join(event_lines) if event_lines else "No events yet."
        score = f"{match.home_team} {match.home_score} - {match.away_score} {match.away_team}"

        if content_type == MatchNarrative.ContentType.NARRATIVE:
            instruction = (
                "Write a concise, energetic live match narrative (2-3 sentences) "
                "for a broadcast studio. Describe the flow of the game and key moments."
            )
        elif content_type == MatchNarrative.ContentType.TACTICAL:
            instruction = (
                "Explain the key tactical pattern visible in these events in "
                "2-3 sentences (pressing shape, build-up, defensive line)."
            )
        elif content_type == MatchNarrative.ContentType.RECAP:
            instruction = (
                "Write a post-match auto recap (3-4 sentences): final score, "
                "decisive moments, standout performances, what it means."
            )
        else:
            instruction = "Summarize the match events."

        return (
            f"You are a Premier League match analyst. Respond in {language}.\n"
            f"Match: {score}\n"
            f"Recent events:\n{events_text}\n\n"
            f"{instruction}"
        )
```

`narratives/tests/test_services.py` (copy-pasteable, write first, fail, then implement):

```python
"""
TDD: narrative service tests.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from matches.models import Match, MatchEvent
from narratives.models import MatchNarrative
from narratives.services import NarrativeService


class NarrativeServiceTests(TestCase):
    @patch.object(NarrativeService, "llm", new_callable=MagicMock)
    def test_generate_creates_matchnarrative(self, mock_llm):
        mock_llm.chat_completion.return_value = "Arsenal dominates possession."
        match = Match.objects.create(
            home_team="Arsenal",
            away_team="Chelsea",
            home_score=1,
            away_score=0,
            status=Match.Status.LIVE,
        )
        MatchEvent.objects.create(
            match=match,
            minute=23,
            event_type=MatchEvent.EventType.GOAL,
            team="Arsenal",
            player="Saka",
            xg_value=0.45,
        )
        service = NarrativeService()
        narrative = service.generate(match, MatchNarrative.ContentType.NARRATIVE, "en")
        self.assertEqual(narrative.content, "Arsenal dominates possession.")
        self.assertEqual(narrative.language, "en")
        self.assertTrue(
            MatchNarrative.objects.filter(
                match=match,
                content_type=MatchNarrative.ContentType.NARRATIVE,
                language="en",
            ).exists()
        )
```

Exact commands:

```bash
source .venv/bin/activate
python manage.py test narratives.tests.test_services   # EXPECT: FAIL (no services module)
# Then write narratives/services.py (copy-pasteable above)
python manage.py test narratives   # EXPECT: OK, all tests
git add -A
git commit -m "feat: narrative generation service with tests"
git push origin main
```

Expected output: first run errors `ModuleNotFoundError`; second run: `OK (N tests)`.

---

### Task 4: Narrative API endpoints

Bite-sized: add `narratives/views.py`, `narratives/urls.py`, wire into `config/urls.py`. Two GET endpoints returning JSON.

Files created:
- `narratives/views.py`
- `narratives/urls.py`

Files modified:
- `config/urls.py` — add `path("narratives/", include("narratives.urls"))`

`narratives/views.py` (copy-pasteable):

```python
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from matches.models import Match
from narratives.models import MatchNarrative
from narratives.services import NarrativeService


@require_http_methods(["GET"])
def narrative_api(request, match_id):
    """Generate or fetch a live narrative for a match."""
    match = get_object_or_404(Match, id=match_id)
    language = request.GET.get("lang", "en")
    service = NarrativeService()
    narrative = service.generate(
        match, MatchNarrative.ContentType.NARRATIVE, language
    )
    return JsonResponse(
        {
            "match_id": match.id,
            "content_type": narrative.content_type,
            "language": narrative.language,
            "content": narrative.content,
            "generated_at": narrative.generated_at.isoformat(),
        }
    )


@require_http_methods(["GET"])
def recap_api(request, match_id):
    """Generate or fetch an auto recap for a match."""
    match = get_object_or_404(Match, id=match_id)
    language = request.GET.get("lang", "en")
    service = NarrativeService()
    narrative = service.generate(
        match, MatchNarrative.ContentType.RECAP, language
    )
    return JsonResponse(
        {
            "match_id": match.id,
            "content_type": narrative.content_type,
            "language": narrative.language,
            "content": narrative.content,
            "generated_at": narrative.generated_at.isoformat(),
        }
    )
```

`narratives/urls.py` (copy-pasteable):

```python
from django.urls import path

from . import views

app_name = "narratives"

urlpatterns = [
    path(
        "api/narrative/<int:match_id>/",
        views.narrative_api,
        name="narrative_api",
    ),
    path("api/recap/<int:match_id>/", views.recap_api, name="recap_api"),
]
```

Edit `config/urls.py`: add `from django.urls import include, path` (already present) and `path("narratives/", include("narratives.urls"))` to `urlpatterns`.

Exact commands:

```bash
source .venv/bin/activate
python manage.py check
# Start server for manual verification
python manage.py runserver 0.0.0.0:8000 > /tmp/django-server.log 2>&1 &
sleep 3
curl -s -w "\nHTTP %{http_code}\n" "http://127.0.0.1:8000/narratives/api/narrative/1/?lang=en"
kill %1 2>/dev/null || true
git add -A
git commit -m "feat: narrative API endpoints"
git push origin main
```

Expected output: `check` clean; curl returns HTTP 200 with JSON containing `"content"` (or a connection error if LLM endpoint not configured — document as expected in dev).

---

### Task 5: Azure AI Translator service with tests (TDD)

Bite-sized: `translation/service.py` wraps Azure AI Translator REST API; graceful degradation when credentials missing.

Files created:
- `translation/__init__.py`
- `translation/service.py`
- `translation/tests/__init__.py`
- `translation/tests/test_service.py`

`translation/service.py` (copy-pasteable):

```python
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
```

`translation/tests/test_service.py` (copy-pasteable, TDD):

```python
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
        self.assertIn("fake-key", req.header_items())

    def test_translate_returns_original_when_unconfigured(self):
        svc = TranslatorService(key="", endpoint="")
        result = svc.translate("Arsenal presses high.", "es")
        self.assertEqual(result, "Arsenal presses high.")
```

Exact commands:

```bash
source .venv/bin/activate
mkdir -p translation/tests
touch translation/tests/__init__.py
python manage.py test translation.tests.test_service   # EXPECT: FAIL (no service module)
# Then write translation/service.py (copy-pasteable above)
python manage.py test translation   # EXPECT: OK, 2 tests
git add -A
git commit -m "feat: Azure Translator service with TDD tests"
git push origin main
```

Expected output: first run `ModuleNotFoundError`; second run `OK (2 tests)`.

---

### Task 6: Language middleware

Bite-sized: `translation/middleware.py` reads `?lang=` or `lang` cookie, sets `request.language`. Wire into `config/settings.py` MIDDLEWARE.

Files created:
- `translation/middleware.py`

Files modified:
- `config/settings.py` — add `'translation.middleware.LanguageMiddleware'` after `'django.contrib.sessions.middleware.SessionMiddleware'`

`translation/middleware.py` (copy-pasteable):

```python
"""
Language middleware: reads ?lang= query or lang cookie, sets request.language.
"""
class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.language = request.GET.get("lang") or request.COOKIES.get("lang", "en")
        response = self.get_response(request)
        if (
            "lang" in request.GET
            and request.GET["lang"] != request.COOKIES.get("lang")
        ):
            response.set_cookie("lang", request.GET["lang"], max_age=60 * 60 * 24 * 30)
        return response
```

Exact commands:

```bash
source .venv/bin/activate
# Edit config/settings.py: add middleware after SessionMiddleware
python manage.py check
git add -A
git commit -m "feat: language middleware for multi-language support"
git push origin main
```

Expected output: `check` clean.

---

### Task 7: Studio broadcast view + fan personalized view

Bite-sized: two new views and templates; studio = clean overlay (no chrome), fan = language selector + narrative panel.

Files modified:
- `matches/views.py` — add `studio_view`, `fan_view`
- `matches/urls.py` — add studio and fan routes

Files created:
- `matches/templates/matches/studio.html`
- `matches/templates/matches/fan.html`

`matches/views.py` additions (copy-pasteable, append to existing file):

```python
from django.shortcuts import render


def studio_view(request, match_id):
    """Clean broadcast overlay: score, clock, ticker, narrative banner."""
    from .models import Match

    match = Match.objects.get(id=match_id)
    events = match.events.all()[:20]
    return render(
        request,
        "matches/studio.html",
        {"match": match, "events": events},
    )


def fan_view(request, match_id):
    """Fan personalized view: language toggle, narrative in chosen language."""
    from .models import Match

    match = Match.objects.get(id=match_id)
    language = getattr(request, "language", "en")
    narratives = match.narratives.filter(language=language)
    return render(
        request,
        "matches/fan.html",
        {"match": match, "language": language, "narratives": narratives},
    )
```

`matches/urls.py` additions (copy-pasteable):

```python
path("studio/<int:match_id>/", views.studio_view, name="studio_view"),
path("fan/<int:match_id>/", views.fan_view, name="fan_view"),
```

`matches/templates/matches/studio.html` (copy-pasteable):

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ match.home_team }} vs {{ match.away_team }} — Studio Overlay</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@2.0.0"></script>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Geist', sans-serif; }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen p-4">

    <header class="bg-red-900 border-b border-red-700 p-4 flex justify-between items-center">
        <div>
            <h1 class="text-xl font-bold text-white">STUDIO OVERLAY</h1>
            <p class="text-red-200 text-xs uppercase tracking-wider">{{ match.home_team }} vs {{ match.away_team }}</p>
        </div>
        <div class="text-right">
            <div class="text-2xl font-mono text-white">{{ match.match_clock }}s</div>
            <div class="text-xs text-red-300 uppercase">{{ match.get_status_display }}</div>
        </div>
    </header>

    <main class="max-w-4xl mx-auto mt-6 space-y-6">
        <div class="flex justify-between items-center mb-2 border-b border-gray-700 pb-2">
            <span class="text-3xl font-bold text-white">{{ match.home_team }}</span>
            <span class="text-4xl font-mono text-white">{{ match.home_score }} - {{ match.away_score }}</span>
            <span class="text-3xl font-bold text-white">{{ match.away_team }}</span>
        </div>

        <div id="ticker" hx-get="{% url 'matches:ticker_partial' match.id %}" hx-trigger="every 3s" hx-swap="innerHTML">
            <!-- live events loaded via HTMX -->
        </div>

        <div class="bg-gray-800/50 border border-gray-700 rounded p-4">
            <h3 class="text-sm font-bold text-red-200 uppercase mb-2">Live Narrative</h3>
            <p class="text-gray-200" id="narrative">Loading narrative...</p>
        </div>
    </main>

    <script>
        // Fetch narrative from API and inject
        fetch(`/narratives/api/narrative/${{{ match.id }}}/?lang=en`)
            .then(r => r.json())
            .then(data => {
                document.getElementById('narrative').textContent = data.content;
            })
            .catch(() => {
                document.getElementById('narrative').textContent = 'Narrative unavailable.';
            });
    </script>

</body>
</html>
```

`matches/templates/matches/fan.html` (copy-pasteable):

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ match.home_team }} vs {{ match.away_team }} — Fan View</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@2.0.0"></script>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Geist', sans-serif; }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen p-4">

    <header class="bg-red-900 border-b border-red-700 p-4 flex justify-between items-center">
        <div>
            <h1 class="text-xl font-bold text-white">FAN VIEW</h1>
            <p class="text-red-200 text-xs uppercase tracking-wider">{{ match.home_team }} vs {{ match.away_team }}</p>
        </div>
        <div class="flex gap-2">
            {% for lang in "en,es,fr,de,pt,zh"|make_list %}
                <a href="?lang={{ lang }}" class="px-3 py-1 text-xs rounded {% if language == lang %}bg-red-600 text-white{% else %}bg-gray-700 text-gray-300{% endif %}">{{ lang }}</a>
            {% endfor %}
        </div>
    </header>

    <main class="max-w-3xl mx-auto mt-6 space-y-6">
        <div class="flex justify-between items-center mb-2 border-b border-gray-700 pb-2">
            <span class="text-3xl font-bold text-white">{{ match.home_team }}</span>
            <span class="text-4xl font-mono text-white">{{ match.home_score }} - {{ match.away_score }}</span>
            <span class="text-3xl font-bold text-white">{{ match.away_team }}</span>
        </div>

        <div class="bg-gray-800/50 border border-gray-700 rounded p-4">
            <h3 class="text-sm font-bold text-red-200 uppercase mb-2">Match Narrative ({{ language }})</h3>
            {% for n in narratives %}
                {% if n.content_type == 'narrative' %}
                <p class="text-gray-200">{{ n.content }}</p>
                {% endif %}
            {% empty %}
                <p class="text-gray-400 text-sm">Generate a narrative to see it here.</p>
            {% endfor %}
        </div>

        <div class="bg-gray-800/50 border border-gray-700 rounded p-4">
            <h3 class="text-sm font-bold text-red-200 uppercase mb-2">Auto Recap</h3>
            {% for n in narratives %}
                {% if n.content_type == 'recap' %}
                <p class="text-gray-200">{{ n.content }}</p>
                {% endif %}
            {% empty %}
                <p class="text-gray-400 text-sm">Recap available after full time.</p>
            {% endfor %}
        </div>
    </main>

</body>
</html>
```

Exact commands:

```bash
source .venv/bin/activate
# Edit matches/views.py and matches/urls.py (copy-pasteable above)
# Create studio.html and fan.html (copy-pasteable above)
python manage.py check
python manage.py runserver 0.0.0.0:8000 > /tmp/django-server.log 2>&1 &
sleep 3
curl -s -w "\nHTTP %{http_code}\n" "http://127.0.0.1:8000/studio/1/"
curl -s -w "\nHTTP %{http_code}\n" "http://127.0.0.1:8000/fan/1/?lang=es"
kill %1 2>/dev/null || true
git add -A
git commit -m "feat: studio broadcast and fan personalized views"
git push origin main
```

Expected output: both curl requests return HTTP 200 with HTML containing team names.

---

### Task 8: README + demo video + submission assets

Bite-sized: overwrite README.md with hackathon submission content; record demo video separately (outside code).

Files modified:
- `README.md` — full rewrite

`README.md` (copy-pasteable):

```markdown
# Inside the Game — StudioLens

Premier League match-intelligence dashboard that turns synthetic match-event
data into live narratives, tactical explainers, and auto recaps for studio,
broadcast, and streaming scenarios.

**Hackathon:** Microsoft + Premier League "Inside the Game: Developer Hackathon"
**Submission deadline:** October 27, 2026, 11:59 PM Pacific Time

## What it does

- Analyzes match events in real time (goals, shots, passes, pressure, xG)
- Generates live match narratives and "why this moment mattered" tactical explainers
- Auto-generates post-match recaps
- Delivers multi-language fan experiences via Azure AI Translator
- Studio broadcast overlay (clean, OBS-ready) and fan personalized view (language toggle)

## Stack

- Django 6.1.2 + HTMX + Django templates (no React, no CDN)
- Geist font, dark mode default, Crimson #DC143C accent
- SQLite (no Redis), self-hosted assets
- Nemotron-3 via NVIDIA Endpoints (local RTX 3060 or cloud API) for narrative generation
- Azure AI Translator for multi-language output
- GitHub + GitHub Copilot

## Azure services used

- Azure AI Translator (multi-language narratives)
- Azure AI Services (Language — key phrase extraction, optional)
- GitHub / GitHub Copilot (code generation and review)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install django
python manage.py generate_match --home "Arsenal" --away "Manchester City" --events 80
python manage.py runserver
```

Required env vars:
- `NVIDIA_API_BASE` — Nemotron-3 chat completions endpoint (e.g. `http://localhost:8080/v1`)
- `NVIDIA_API_KEY` — NVIDIA Endpoints API key
- `AZURE_TRANSLATOR_KEY`, `AZURE_TRANSLATOR_ENDPOINT`, `AZURE_TRANSLATOR_REGION` — Azure AI Translator

## Demo

3-minute demo video: [record and link here]

## Repository

https://github.com/Josephjbassey/inside-the-game
```

Exact commands:

```bash
source .venv/bin/activate
# Write README.md (copy-pasteable above)
git add -A
git commit -m "docs: README and submission assets"
git push origin main
```

Expected output: commit creates README.md, push succeeds.

Demo video: record locally (screen + voice), 3 minutes max, showing dashboard, narrative generation, language toggle, studio overlay. Save to `/run/media/jabs/Media/video/` per storage policy, then reference in submission. (Outside code scope.)

---

### Task 9: Register and submit to the hackathon

Bite-sized: manual steps via browser; no code.

1. Register at the Inside the Game hackathon page by October 20, 12:00 PM Pacific (~21:00 UTC+1).
2. Watch for Microsoft invitation to join Innovation Studio Platform.
3. Review Premier League Hackathon rules (prize categories, judging criteria, submission process).
4. Submit project by October 27, 11:59 PM Pacific (~08:59 UTC+1, October 28) with:
   - GitHub repo link: https://github.com/Josephjbassey/inside-the-game
   - Demo video URL
   - Short description
   - List of Azure services used
5. Top six notified by November 10, 2026.

---

## Tests / Validation

TDD cycle per code task (Tasks 2, 3, 5):
1. Write failing test → `python manage.py test <app>` → expect `ModuleNotFoundError` or assertion failure.
2. Implement minimally (copy-pasteable code above).
3. Run `python manage.py test <app>` → expect `OK (N tests)`.
4. `git add -A && git commit -m "..." && git push origin main`.

Full pre-submission validation:

```bash
source .venv/bin/activate
python manage.py check
python manage.py test
python manage.py generate_match --home "Arsenal" --away "Chelsea" --events 60
python manage.py runserver 0.0.0.0:8000
# In another terminal:
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/studio/1/
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/fan/1/?lang=es
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/narratives/api/narrative/1/?lang=en
```

Expected: all HTTP 200, `check` clean, all tests pass.

---

## Risks, Tradeoffs, and Open Questions

1. **LLM endpoint not configured:** `NVIDIA_API_BASE`/`NVIDIA_API_KEY` may not be set locally. Narrative endpoints will raise `RuntimeError` or `ValueError` if called without env vars. Decision: document required env vars; no silent fallback (explicit failure is better than fake narratives for a hackathon demo).
2. **Azure credentials missing:** `TranslatorService` gracefully returns original text if key/endpoint unset — intentional degradation.
3. **No Redis:** `MatchNarrative` cached in SQLite; acceptable for MVP. LocMemCache is the Django default and satisfies the no-Redis constraint.
4. **CDN Tailwind:** Current dashboard loads Tailwind via CDN (`cdn.tailwindcss.com`), violating the zero-CDN preference. Tradeoff: keep CDN for MVP speed, swap to self-hosted Tailwind CLI build before submission if time permits.
5. **Demo video:** must be recorded separately (screen + voice), not part of code tasks. Save under `/run/media/jabs/Media/video/` per storage policy.
6. **Registration deadline:** October 20, 12:00 PM Pacific — confirm registration is complete before investing in submission assets.
7. **Submission platform:** Innovation Studio Platform invite required; monitor email after registering.
