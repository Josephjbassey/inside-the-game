# Inside the Game — StudioLens

Premier League match-intelligence dashboard that turns synthetic match-event
data into live narratives, tactical explainers, and auto recaps for studio,
broadcast, and streaming scenarios.

**Hackathon:** Microsoft + Premier League "Inside the Game: Developer Hackathon"
**Submission deadline:** October 27, 2026, 11:59 PM Pacific Time

## What it does

- Analyzes match events in real time (goals, shots, passes, pressure, xG)
- Generates live match narratives and "why this moment mattered" tactical explainers
- Auto-generates post-match match recaps
- Delivers multi-language fan experiences via Azure AI Translator (EN, ES, FR, DE, PT, ZH)
- Studio broadcast overlay (clean, OBS-ready) and fan personalized view (language toggle)

## Stack

- Django 6.1.2 + HTMX + Django templates (no React, no CDN)
- Geist font, dark mode default, Crimson #DC143C accent
- SQLite (no Redis), self-hosted assets
- Azure AI Foundry / Foundry Agents (OpenAI-compatible chat completions) for narrative generation
- Azure AI Translator for multi-language output
- GitHub (public repository)

## Azure services used

- Azure AI Translator (multi-language narratives)
- Azure AI Foundry (agentic workflow and narrative reasoning)
- GitHub (public repository)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install django
python manage.py generate_match --home "Arsenal" --away "Manchester City" --events 80
python manage.py runserver
```

Required env vars:

- `NVIDIA_API_BASE` — Azure AI Foundry chat completions endpoint (OpenAI-compatible)
- `NVIDIA_API_KEY` — Azure AI Foundry API key
- `NVIDIA_MODEL` — your Foundry model deployment name
- `AZURE_TRANSLATOR_KEY`, `AZURE_TRANSLATOR_ENDPOINT`, `AZURE_TRANSLATOR_REGION` — Azure AI Translator

## Demo

Demo video under 2 minutes (120 seconds): [record and link here]

## Repository

https://github.com/Josephjbassey/inside-the-game
