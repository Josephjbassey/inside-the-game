from django.contrib import admin

from .models import MatchNarrative


@admin.register(MatchNarrative)
class MatchNarrativeAdmin(admin.ModelAdmin):
    list_display = ["match", "content_type", "language", "generated_at"]
    list_filter = ["content_type", "language", "match"]
    search_fields = ["content", "match__home_team", "match__away_team"]
