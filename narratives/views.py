from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from matches.models import Match
from narratives.models import MatchNarrative
from narratives.services import NarrativeService


@require_http_methods(["GET"])
def narrative_api(request, match_id):
    """Generate or fetch a live narrative for a match."""
    match = get_object_or_404(Match, id=match_id)
    language = request.GET.get("lang", "en")
    service = NarrativeService()
    narrative = service.generate(
        match, MatchNarrative.ContentType.NARRATIVE, language
    )
    return JsonResponse(
        {
            "match_id": match.id,
            "content_type": narrative.content_type,
            "language": narrative.language,
            "content": narrative.content,
            "generated_at": narrative.generated_at.isoformat(),
        }
    )


@require_http_methods(["GET"])
def recap_api(request, match_id):
    """Generate or fetch an auto recap for a match."""
    match = get_object_or_404(Match, id=match_id)
    language = request.GET.get("lang", "en")
    service = NarrativeService()
    narrative = service.generate(
        match, MatchNarrative.ContentType.RECAP, language
    )
    return JsonResponse(
        {
            "match_id": match.id,
            "content_type": narrative.content_type,
            "language": narrative.language,
            "content": narrative.content,
            "generated_at": narrative.generated_at.isoformat(),
        }
    )
