"""
Views for the matches app.

Serves the live match dashboard and HTMX partials for the event ticker,
scoreboard, and xG chart — real-time match intelligence for studio/broadcast
and fan scenarios.
"""
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Match, MatchEvent
from matches.statistics import MatchStats
from matches.turning_points import detect_turning_points


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


@require_http_methods(["GET"])
def match_stats_api(request, match_id):
    """Computed match statistics JSON."""
    match = get_object_or_404(Match, id=match_id)
    events = list(match.events.all())
    stats = MatchStats(match, events).as_dict()
    return JsonResponse({"match_id": match.id, "statistics": stats})


@require_http_methods(["GET"])
def turning_points_api(request, match_id):
    """Detected turning points with evidence linkage."""
    match = get_object_or_404(Match, id=match_id)
    events = list(match.events.all().order_by("minute", "second", "created_at"))
    stats = MatchStats(match, events).as_dict()
    turning_points = detect_turning_points(match, events, stats)
    return JsonResponse({
        "match_id": match.id,
        "turning_points": [
            {
                "minute": tp.minute,
                "title": tp.title,
                "description": tp.description,
                "impact": tp.impact,
                "confidence": tp.confidence,
                "evidence": tp.evidence,
            }
            for tp in turning_points
        ],
    })


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
