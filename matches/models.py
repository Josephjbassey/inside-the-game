"""
Match models for the Inside the Game hackathon project.

Defines the Premier League synthetic match-event schema:
- Match: fixture metadata (teams, score, clock, status)
- MatchEvent: atomic match events (goals, shots, passes, xG, pressure, subs)
"""
from django.db import models


class Match(models.Model):
    """A Premier League match fixture."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        PAUSED = "paused", "Paused"
        HALFTIME = "halftime", "Halftime"
        FULLTIME = "fulltime", "Fulltime"
        CANCELLED = "cancelled", "Cancelled"

    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    match_clock = models.PositiveIntegerField(default=0)  # seconds
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    kickoff_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-kickoff_at"]

    def __str__(self):
        return f"{self.home_team} {self.home_score} - {self.away_score} {self.away_team}"

    @property
    def xg_home(self):
        return sum(e.xg_value for e in self.events.filter(team=self.home_team, event_type="shot"))

    @property
    def xg_away(self):
        return sum(e.xg_value for e in self.events.filter(team=self.away_team, event_type="shot"))


class MatchEvent(models.Model):
    """An atomic event recorded during a match."""

    class EventType(models.TextChoices):
        GOAL = "goal", "Goal"
        SHOT = "shot", "Shot"
        PASS = "pass", "Pass"
        PRESSURE = "pressure", "Pressure"
        SUBSTITUTION = "substitution", "Substitution"
        CARD = "card", "Card"
        OFFSIDE = "offside", "Offside"
        FOUL = "foul", "Foul"
        CORNER = "corner", "Corner"
        SAVE = "save", "Save"

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="events")
    minute = models.PositiveIntegerField()
    second = models.PositiveIntegerField(default=0)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    team = models.CharField(max_length=100)
    player = models.CharField(max_length=100, blank=True)
    x = models.FloatField(null=True, blank=True)  # pitch x-coordinate (0-100)
    y = models.FloatField(null=True, blank=True)  # pitch y-coordinate (0-100)
    xg_value = models.FloatField(null=True, blank=True)  # expected goals for shots
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["minute", "second", "created_at"]

    def __str__(self):
        return f"{self.match} {self.minute}' {self.event_type} by {self.player or self.team}"
