"""
Generate synthetic Premier League match data for the hackathon demo.

Creates a Match and a sequence of MatchEvents (goals, shots, passes, pressure,
substitutions, cards, corners, saves, offsides, fouls) with realistic xG values
and pitch coordinates.
"""
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from matches.models import Match, MatchEvent

TEAMS = [
    "Arsenal", "Aston Villa", "Brentford", "Brighton", "Chelsea",
    "Crystal Palace", "Everton", "Fulham", "Ipswich", "Leicester",
    "Liverpool", "Manchester City", "Manchester United", "Newcastle",
    "Nottingham Forest", "Southampton", "Tottenham", "West Ham",
    "Wolves", "Bournemouth",
]

EVENT_WEIGHTS = {
    "pass": 40,
    "pressure": 20,
    "shot": 10,
    "foul": 8,
    "corner": 6,
    "offside": 4,
    "card": 3,
    "save": 3,
    "substitution": 3,
    "goal": 2,
}

XG_BY_TYPE = {
    "shot": (0.02, 0.35),
    "goal": (0.45, 0.95),
    "save": (0.05, 0.40),
}


class Command(BaseCommand):
    help = "Generate a synthetic Premier League match with events."

    def add_arguments(self, parser):
        parser.add_argument("--home", type=str, help="Home team name")
        parser.add_argument("--away", type=str, help="Away team name")
        parser.add_argument("--events", type=int, default=120, help="Number of events to generate")

    def handle(self, *args, **options):
        home = options["home"] or random.choice(TEAMS)
        away = options["away"] or random.choice([t for t in TEAMS if t != home])
        n_events = options["events"]

        match = Match.objects.create(
            home_team=home,
            away_team=away,
            kickoff_at=timezone.now() - timedelta(minutes=5),
            status=Match.Status.LIVE,
            match_clock=0,
        )

        minute = 0
        for i in range(n_events):
            minute += random.randint(1, 4)
            if minute > 90:
                break
            second = random.randint(0, 59)
            event_type = random.choices(
                list(EVENT_WEIGHTS.keys()), weights=list(EVENT_WEIGHTS.values())
            )[0]

            team = random.choice([home, away])
            player = f"Player {random.randint(1, 11)}"

            x, y = None, None
            xg_value = None
            if event_type in ("shot", "goal", "save"):
                x = round(random.uniform(10, 95), 1)
                y = round(random.uniform(10, 90), 1)
                lo, hi = XG_BY_TYPE[event_type]
                xg_value = round(random.uniform(lo, hi), 3)
                if event_type == "goal":
                    if team == home:
                        match.home_score += 1
                    else:
                        match.away_score += 1
                    match.save()

            description = f"{event_type} by {player} for {team} in the {minute}'"

            MatchEvent.objects.create(
                match=match,
                minute=minute,
                second=second,
                event_type=event_type,
                team=team,
                player=player,
                x=x,
                y=y,
                xg_value=xg_value,
                description=description,
            )

        match.match_clock = minute * 60 + second
        match.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created match {match.id}: {home} {match.home_score} - {match.away_score} {away} "
                f"with {n_events} events"
            )
        )
