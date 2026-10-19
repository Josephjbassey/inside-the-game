from django.contrib import admin

from .models import Match, MatchEvent


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["home_team", "home_score", "away_score", "away_team", "status", "match_clock", "kickoff_at"]
    list_filter = ["status", "kickoff_at"]
    search_fields = ["home_team", "away_team"]
    list_editable = ["home_score", "away_score", "status", "match_clock"]


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ["match", "minute", "event_type", "team", "player", "xg_value"]
    list_filter = ["event_type", "team", "match"]
    search_fields = ["player", "team", "description"]
    list_editable = ["minute", "event_type"]
