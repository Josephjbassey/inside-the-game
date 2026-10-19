"""
TDD: narrative service tests.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from matches.models import Match, MatchEvent
from narratives.models import MatchNarrative
from narratives.services import NarrativeService


class NarrativeServiceTests(TestCase):
    @patch("narratives.services.LLMClient")
    def test_generate_creates_matchnarrative(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = "Arsenal dominates possession."
        mock_llm_class.return_value = mock_llm
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
        narrative = service.generate(
            match, MatchNarrative.ContentType.NARRATIVE, "en"
        )
        self.assertEqual(narrative.content, "Arsenal dominates possession.")
        self.assertEqual(narrative.language, "en")
        self.assertTrue(
            MatchNarrative.objects.filter(
                match=match,
                content_type=MatchNarrative.ContentType.NARRATIVE,
                language="en",
            ).exists()
        )
