"""
Views for the matches app.

Serves the live match dashboard and HTMX partials for the event ticker,
scoreboard, and xG chart — real-time match intelligence for studio/broadcast
and fan scenarios.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Match, MatchEvent

def dashboard(request, match_id=None):
    """Main live match dashboard."""
    if match_id:
        match = get_object_or_404(Match, id=match_id)
    else:
        match = Match.objects.filter(status=Match.Status.LIVE).first()
        if not match:
            match = Match.objects.first()

    events = match.events.all()[:50] if match else []

    context = {
        "match": match,
        "events": events,
    }
    return render(request, "matches/dashboard.html", context)


@require_http_methods(["GET"])
def ticker_partial(request, match_id):
    """HTMX partial: recent match events ticker."""
    match = get_object_or_404(Match, id=match_id)
    events = match.events.all()[:20]
    return render(request, "matches/partials/_ticker.html", {"match": match, "events": events})


@require_http_methods(["GET"])
def scoreboard_partial(request, match_id):
    """HTMX partial: live scoreboard + match clock."""
    match = get_object_or_404(Match, id=match_id)
    return render(request, "matches/partials/_scoreboard.html", {"match": match})


@require_http_methods(["GET"])
def xg_partial(request, match_id):
    """HTMX partial: xG comparison display."""
    match = get_object_or_404(Match, id=match_id)
    return render(request, "matches/partials/_xg_chart.html", {"match": match})


def studio_view(request, match_id):
    """Clean broadcast overlay: score, clock, ticker, narrative banner."""
    match = get_object_or_404(Match, id=match_id)
    events = match.events.all()[:20]
    return render(
        request,
        "matches/studio.html",
        {"match": match, "events": events},
    )


def fan_view(request, match_id):
    """Fan personalized view: language toggle, narrative in chosen language."""
    match = get_object_or_404(Match, id=match_id)
    language = getattr(request, "language", "en")
    narratives = match.narratives.filter(language=language)
    return render(
        request,
        "matches/fan.html",
        {"match": match, "language": language, "narratives": narratives},
    )
