"""
TDD: turning-point detection tests.
"""
from django.test import TestCase

from matches.models import Match, MatchEvent
from matches.turning_points import detect_turning_points


def _make_event(match, minute, event_type, team, player="P1", x=None, xg=None):
    return MatchEvent.objects.create(
        match=match, minute=minute, event_type=event_type, team=team,
        player=player, x=x, xg_value=xg,
    )


class TurningPointTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=0, away_score=0, status=Match.Status.LIVE,
        )

    def test_goal_is_turning_point(self):
        _make_event(self.match, 23, "goal", "Arsenal", "Saka", x=75, xg=0.45)
        points = detect_turning_points(
            self.match, self.match.events.all(),
            self.match.events.all(),
        )
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].minute, 23)
        self.assertEqual(points[0].impact, "Arsenal_advantage")
        self.assertEqual(points[0].confidence, "high")
        self.assertEqual(len(points[0].evidence), 1)
        self.assertEqual(points[0].evidence[0]["player"], "Saka")

    def test_pressure_surge_detected(self):
        for i in range(5):
            _make_event(self.match, 40 + i, "pressure", "Arsenal", x=80)
        points = detect_turning_points(
            self.match, self.match.events.all(),
            self.match.events.all(),
        )
        pressure_points = [p for p in points if "Pressure" in p.title]
        self.assertTrue(len(pressure_points) >= 1)
        self.assertEqual(pressure_points[0].impact, "Arsenal_advantage")
        self.assertEqual(len(pressure_points[0].evidence), 5)

    def test_shot_volume_shift_home(self):
        for i in range(4):
            _make_event(self.match, 76 + i, "shot", "Arsenal", x=70, xg=0.12)
        _make_event(self.match, 80, "shot", "Chelsea", x=30, xg=0.08)
        points = detect_turning_points(
            self.match, self.match.events.all(),
            self.match.events.all(),
        )
        shift = [p for p in points if "Shot volume" in p.title]
        self.assertTrue(len(shift) >= 1)
        self.assertEqual(shift[0].impact, "home_advantage")

    def test_substitution_impact(self):
        _make_event(self.match, 60, "substitution", "Arsenal", "Sub A")
        _make_event(self.match, 67, "goal", "Arsenal", "Saka", x=70, xg=0.5)
        points = detect_turning_points(
            self.match, self.match.events.all(),
            self.match.events.all(),
        )
        sub_points = [p for p in points if "Substitution" in p.title]
        self.assertTrue(len(sub_points) >= 1)
        self.assertEqual(len(sub_points[0].evidence), 2)

    def test_empty_match_no_points(self):
        points = detect_turning_points(
            self.match, self.match.events.all(),
            self.match.events.all(),
        )
        self.assertEqual(len(points), 0)
