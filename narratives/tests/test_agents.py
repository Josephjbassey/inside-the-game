"""
TDD: multi-agent narrative pipeline tests.
"""
from unittest.mock import patch

from django.test import TestCase

from matches.models import Match, MatchEvent
from matches.turning_points import detect_turning_points
from narratives.agents import (
    MatchState,
    TacticalAnalyst,
    EvidenceVerifier,
    NarrativeProducer,
    AudienceAdapter,
)


def _make_event(match, minute, event_type, team, player="P1", x=None, xg=None):
    return MatchEvent.objects.create(
        match=match, minute=minute, event_type=event_type, team=team,
        player=player, x=x, xg_value=xg,
    )


def _build_state(match):
    events = list(match.events.all().order_by("minute", "second", "created_at"))
    from matches.statistics import MatchStats
    stats = MatchStats(match, events).as_dict()
    tps = detect_turning_points(match, events, stats)
    return MatchState.from_match(match)


class MatchStateTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=1, away_score=0, status=Match.Status.LIVE,
            match_clock=1500,
        )
        _make_event(self.match, 10, "pass", "Arsenal", x=50)
        _make_event(self.match, 11, "pass", "Chelsea", x=40)

    def test_from_match_creates_state(self):
        state = MatchState.from_match(self.match)
        self.assertEqual(state.match_id, self.match.id)
        self.assertEqual(state.home_team, "Arsenal")
        self.assertEqual(state.away_team, "Chelsea")
        self.assertEqual(state.home_score, 1)
        self.assertEqual(state.away_score, 0)
        self.assertEqual(state.minute, 25)  # 1500 // 60
        self.assertIn("possession", state.to_dict())
        self.assertIn("turning_points", state.to_dict())


class TacticalAnalystTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=0, away_score=0, status=Match.Status.LIVE,
        )
        _make_event(self.match, 23, "goal", "Arsenal", "Saka")

    def test_analyst_preserves_turning_points(self):
        state = MatchState.from_match(self.match)
        analyst = TacticalAnalyst()
        result = analyst.analyze(state)
        self.assertEqual(len(result.turning_points), 1)
        self.assertEqual(result.turning_points[0]["title"], "Goal — Arsenal")


class EvidenceVerifierTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=1, away_score=0, status=Match.Status.LIVE,
            match_clock=1500,
        )
        _make_event(self.match, 23, "goal", "Arsenal", "Saka", x=75, xg=0.45)
        self.state = MatchState.from_match(self.match)

    def test_verified_claim_returns_evidence(self):
        verifier = EvidenceVerifier()
        result = verifier.verify("Arsenal scored a goal", self.state)
        self.assertTrue(result["verified"])
        self.assertTrue(len(result["evidence"]) > 0)

    def test_unverified_claim_returns_reason(self):
        verifier = EvidenceVerifier()
        result = verifier.verify("The referee was biased", self.state)
        self.assertFalse(result["verified"])
        self.assertIsNotNone(result["reason"])


class NarrativeProducerTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=1, away_score=0, status=Match.Status.LIVE,
            match_clock=1500,
        )
        _make_event(self.match, 23, "goal", "Arsenal", "Saka", x=75, xg=0.45)
        self.state = MatchState.from_match(self.match)

    def test_produce_narrative_returns_string(self):
        producer = NarrativeProducer()
        result = producer.produce_narrative(self.state, "en")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_produce_recap_returns_string(self):
        producer = NarrativeProducer()
        result = producer.produce_recap(self.state, "en")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_fallback_when_no_turning_points(self):
        match2 = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=0, away_score=0, status=Match.Status.LIVE,
            match_clock=100,
        )
        state2 = MatchState.from_match(match2)
        producer = NarrativeProducer()
        result = producer.produce_narrative(state2, "en")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class AudienceAdapterTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=1, away_score=0, status=Match.Status.LIVE,
            match_clock=1500,
        )
        self.state = MatchState.from_match(self.match)

    def test_adapt_broadcaster_role(self):
        adapter = AudienceAdapter()
        result = adapter.adapt("Test narrative", self.state, "broadcaster", "en")
        self.assertEqual(result["role"], "broadcaster")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["content"], "Test narrative")
        self.assertIn("json_ready", result)

    def test_adapt_analyst_role(self):
        adapter = AudienceAdapter()
        result = adapter.adapt("Test narrative", self.state, "analyst", "en")
        self.assertEqual(result["role"], "analyst")
        self.assertIn("possession", result["summary"].lower())

    def test_adapt_fan_role(self):
        adapter = AudienceAdapter()
        result = adapter.adapt("Test narrative", self.state, "fan", "en")
        self.assertEqual(result["role"], "fan")

    def test_adapt_invalid_role_defaults_to_fan(self):
        adapter = AudienceAdapter()
        result = adapter.adapt("Test narrative", self.state, "invalid", "en")
        self.assertEqual(result["role"], "fan")

    def test_adapt_spanish_language(self):
        adapter = AudienceAdapter()
        result = adapter.adapt("Test narrative", self.state, "fan", "es")
        self.assertEqual(result["language"], "es")
