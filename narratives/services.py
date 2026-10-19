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
