"""
Narrative models for match intelligence.

Stores AI-generated match narratives, tactical explainers, and auto recaps
per match, keyed by language. Cached in SQLite (no Redis).
"""
from django.db import models
from matches.models import Match


class MatchNarrative(models.Model):
    """AI-generated narrative content for a match."""

    class ContentType(models.TextChoices):
        NARRATIVE = "narrative", "Live Narrative"
        TACTICAL = "tactical", "Tactical Explainer"
        RECAP = "recap", "Auto Recap"

    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="narratives"
    )
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    language = models.CharField(max_length=10, default="en")  # BCP-47: en, es, fr, de, pt, zh
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-generated_at"]
        unique_together = [["match", "content_type", "language"]]

    def __str__(self):
        return f"{self.match} — {self.get_content_type_display()} ({self.language})"
