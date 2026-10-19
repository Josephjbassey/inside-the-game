from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from matches.models import Match, MatchEvent
from matches.statistics import MatchStats
from matches.turning_points import detect_turning_points
from narratives.agents import (
    AudienceAdapter,
    EvidenceVerifier,
    MatchState,
    NarrativeProducer,
)
from narratives.models import MatchNarrative
from narratives.services import NarrativeService


@require_http_methods(["GET"])
def narrative_api(request, match_id):
    """Generate or fetch a live narrative for a match via the agent pipeline."""
    match = get_object_or_404(Match, id=match_id)
    language = request.GET.get("lang", "en")
    state = MatchState.from_match(match)
    producer = NarrativeProducer()
    content = producer.produce_narrative(state, language)
    narrative, _ = MatchNarrative.objects.update_or_create(
        match=match,
        content_type=MatchNarrative.ContentType.NARRATIVE,
        language=language,
        defaults={"content": content},
    )
    return JsonResponse({
        "match_id": match.id,
        "content_type": narrative.content_type,
        "language": narrative.language,
        "content": narrative.content,
        "generated_at": narrative.generated_at.isoformat(),
    })


@require_http_methods(["GET"])
def recap_api(request, match_id):
    """Generate or fetch an auto recap for a match via the agent pipeline."""
    match = get_object_or_404(Match, id=match_id)
    language = request.GET.get("lang", "en")
    state = MatchState.from_match(match)
    producer = NarrativeProducer()
    content = producer.produce_recap(state, language)
    narrative, _ = MatchNarrative.objects.update_or_create(
        match=match,
        content_type=MatchNarrative.ContentType.RECAP,
        language=language,
        defaults={"content": content},
    )
    return JsonResponse({
        "match_id": match.id,
        "content_type": narrative.content_type,
        "language": narrative.language,
        "content": narrative.content,
        "generated_at": narrative.generated_at.isoformat(),
    })


@require_http_methods(["GET"])
def tactical_api(request, match_id):
    """Tactical explainer: turning points with evidence linkage."""
    match = get_object_or_404(Match, id=match_id)
    events = list(match.events.all().order_by("minute", "second", "created_at"))
    stats = MatchStats(match, events).as_dict()
    turning_points = detect_turning_points(match, events, stats)
    return JsonResponse({
        "match_id": match.id,
        "score": f"{match.home_team} {match.home_score} - {match.away_score} {match.away_team}",
        "minute": match.match_clock // 60,
        "status": match.status,
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
        "statistics": stats,
    })


@require_http_methods(["GET"])
def match_state_api(request, match_id):
    """Full structured match-state JSON (broadcast-ready graphics payload)."""
    match = get_object_or_404(Match, id=match_id)
    state = MatchState.from_match(match)
    return JsonResponse(state.to_dict())


@require_http_methods(["POST"])
def ask_why_api(request, match_id):
    """'Ask why' Q&A grounded in match events and statistics."""
    import json

    match = get_object_or_404(Match, id=match_id)
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}
    question = body.get("question", "")
    language = body.get("lang", "en")

    if not question:
        return JsonResponse({"error": "question is required"}, status=400)

    state = MatchState.from_match(match)
    verifier = EvidenceVerifier()
    result = verifier.verify(question, state)

    adapter = AudienceAdapter()
    adapted = adapter.adapt(
        result["reason"] or result["corrected_claim"] or "No answer available.",
        state,
        role="fan",
        language=language,
    )

    return JsonResponse({
        "match_id": match.id,
        "question": question,
        "language": language,
        "verified": result["verified"],
        "answer": adapted["content"],
        "evidence": result["evidence"],
        "reason": result["reason"],
        "match_state": adapted["json_ready"],
    })
