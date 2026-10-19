"""
TDD: match statistics tests.
"""
from django.test import TestCase

from matches.models import Match, MatchEvent
from matches.statistics import MatchStats


def _make_event(match, minute, event_type, team, player="P1", x=None, xg=None):
    return MatchEvent.objects.create(
        match=match, minute=minute, event_type=event_type, team=team,
        player=player, x=x, xg_value=xg,
    )


class MatchStatsTests(TestCase):
    def setUp(self):
        self.match = Match.objects.create(
            home_team="Arsenal", away_team="Chelsea",
            home_score=1, away_score=0, status=Match.Status.LIVE,
        )
        _make_event(self.match, 10, "pass", "Arsenal", x=50)
        _make_event(self.match, 11, "pass", "Arsenal", x=55)
        _make_event(self.match, 12, "pass", "Chelsea", x=40)
        _make_event(self.match, 20, "shot", "Arsenal", x=70, xg=0.25)
        _make_event(self.match, 21, "shot", "Chelsea", x=30, xg=0.05)
        _make_event(self.match, 22, "pressure", "Arsenal", x=80)
        _make_event(self.match, 23, "pressure", "Arsenal", x=85)
        _make_event(self.match, 24, "pressure", "Arsenal", x=90)

    def test_possession_share(self):
        stats = MatchStats(self.match, self.match.events.all())
        p = stats.possession()
        self.assertEqual(p["Arsenal"], 75)  # 6 of 8 events
        self.assertEqual(p["Chelsea"], 25)

    def test_shots(self):
        stats = MatchStats(self.match, self.match.events.all())
        s = stats.shots()
        self.assertEqual(s["Arsenal"], 1)
        self.assertEqual(s["Chelsea"], 1)

    def test_shots_on_target(self):
        stats = MatchStats(self.match, self.match.events.all())
        s = stats.shots_on_target()
        self.assertEqual(s["Arsenal"], 1)   # xG 0.25 >= 0.15
        self.assertEqual(s["Chelsea"], 0)   # xG 0.05 < 0.15

    def test_pressure_final_third(self):
        stats = MatchStats(self.match, self.match.events.all())
        p = stats.pressure_in_final_third()
        self.assertEqual(p["Arsenal"], 3)   # all x > 66
        self.assertEqual(p["Chelsea"], 0)

    def test_xg(self):
        stats = MatchStats(self.match, self.match.events.all())
        x = stats.xg()
        self.assertEqual(x["Arsenal"], 0.25)
        self.assertEqual(x["Chelsea"], 0.05)
