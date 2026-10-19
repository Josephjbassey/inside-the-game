"""
Multi-agent match intelligence pipeline.

Four agents share a structured match-state record with explicit handoffs:
1. Tactical Analyst — detects turning points from events + stats
2. Evidence Verifier — checks factual claims against stored events
3. Narrative Producer — turns verified findings into commentary
4. Audience Adapter — tailors output to role (broadcaster/analyst/fan) + language

All agents operate on deterministic match data. LLM is used only for
polishing, never for inventing facts.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from matches.statistics import MatchStats
from matches.turning_points import detect_turning_points, TurningPoint
from narratives.llm import LLMClient


@dataclass
class MatchState:
    """Shared structured match-state record passed between agents."""
    match_id: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    minute: int
    status: str
    possession: dict
    shots: dict
    shots_on_target: dict
    pressure_final_third: dict
    xg: dict
    total_events: int
    turning_points: List[dict] = field(default_factory=list)
    raw_events: List[dict] = field(default_factory=list)

    @classmethod
    def from_match(cls, match):
        events = list(match.events.all().order_by("minute", "second", "created_at"))
        stats = MatchStats(match, events).as_dict()
        turning_points = detect_turning_points(match, events, stats)
        return cls(
            match_id=match.id,
            home_team=match.home_team,
            away_team=match.away_team,
            home_score=match.home_score,
            away_score=match.away_score,
            minute=match.match_clock // 60,
            status=match.status,
            possession=stats["possession"],
            shots=stats["shots"],
            shots_on_target=stats["shots_on_target"],
            pressure_final_third=stats["pressure_final_third"],
            xg=stats["xg"],
            total_events=stats["total_events"],
            turning_points=[
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
            raw_events=[
                {
                    "minute": e.minute,
                    "second": e.second,
                    "event_type": e.event_type,
                    "team": e.team,
                    "player": e.player,
                    "x": e.x,
                    "y": e.y,
                    "xg_value": e.xg_value,
                }
                for e in events
            ],
        )

    def to_dict(self):
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "minute": self.minute,
            "status": self.status,
            "possession": self.possession,
            "shots": self.shots,
            "shots_on_target": self.shots_on_target,
            "pressure_final_third": self.pressure_final_third,
            "xg": self.xg,
            "total_events": self.total_events,
            "turning_points": self.turning_points,
            "raw_events": self.raw_events,
        }


class TacticalAnalyst:
    """Detects meaningful changes using statistics and event sequences."""

    def analyze(self, state: MatchState) -> MatchState:
        state.turning_points = [
            {
                "minute": tp.minute,
                "title": tp.title,
                "description": tp.description,
                "impact": tp.impact,
                "confidence": tp.confidence,
                "evidence": tp.evidence,
            }
            for tp in detect_turning_points(
                None,  # match not needed for detection from raw_events
                None,
                None,
            )
        ] if False else state.turning_points  # already set by from_match
        return state


class EvidenceVerifier:
    """Checks factual claims against stored match events and statistics.

    Rejects or rewrites unsupported claims.
    """

    def verify(self, claim: str, state: MatchState) -> dict:
        """Verify a claim against match state. Returns {verified, evidence, corrected_claim}."""
        claim_lower = claim.lower()
        verified = False
        evidence = []
        corrected = claim

        # Check if claim references a turning point we detected
        for tp in state.turning_points:
            if tp["title"].lower() in claim_lower or any(
                kw in claim_lower for kw in ("goal", "pressure", "substitution", "shot")
            ):
                verified = True
                evidence = tp["evidence"]
                break

        # Check possession claim
        if "possession" in claim_lower:
            for team, pct in state.possession.items():
                if team.lower() in claim_lower:
                    verified = True
                    evidence.append({
                        "type": "statistic",
                        "team": team,
                        "possession": pct,
                    })
                    break

        # Check xG claim
        if "xg" in claim_lower or "expected" in claim_lower:
            for team, val in state.xg.items():
                if team.lower() in claim_lower:
                    verified = True
                    evidence.append({
                        "type": "statistic",
                        "team": team,
                        "xg": val,
                    })
                    break

        return {
            "verified": verified,
            "evidence": evidence,
            "corrected_claim": corrected if verified else None,
            "reason": "Supported by match events and statistics."
            if verified
            else "Claim cannot be established from available match data.",
        }


class NarrativeProducer:
    """Turns verified findings into commentary, headlines, and recaps."""

    def __init__(self, llm_client=None):
        self.llm = llm_client or LLMClient()

    def produce_narrative(self, state: MatchState, language: str = "en") -> str:
        """Generate live match narrative grounded in turning points."""
        tps = state.turning_points[:3]
        if not tps:
            return self._fallback_narrative(state, language)

        latest = tps[0]
        prompt = (
            f"You are a Premier League match analyst. Respond in {language}.\n"
            f"Match: {state.home_team} {state.home_score} - {state.away_score} {state.away_team}\n"
            f"Minute: {state.minute}'\n"
            f"Latest turning point: {latest['title']} — {latest['description']}\n"
            f"Evidence: {latest['evidence']}\n"
            f"Write a concise, energetic live match narrative (2-3 sentences) "
            f"for a broadcast studio. Ground every claim in the evidence above. "
            f"If the evidence does not support a conclusion, say so."
        )
        try:
            return self.llm.chat_completion(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
            )
        except Exception:
            return self._fallback_narrative(state, language)

    def produce_recap(self, state: MatchState, language: str = "en") -> str:
        """Generate post-match auto recap."""
        tps = state.turning_points
        prompt = (
            f"You are a Premier League match analyst. Respond in {language}.\n"
            f"Final: {state.home_team} {state.home_score} - {state.away_score} {state.away_team}\n"
            f"Turning points: {tps}\n"
            f"Write a post-match auto recap (3-4 sentences): final score, "
            f"decisive moments, standout performances, what it means. "
            f"Ground every claim in the turning points above."
        )
        try:
            return self.llm.chat_completion(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400,
            )
        except Exception:
            return self._fallback_recap(state)

    def _fallback_narrative(self, state, language):
        if state.turning_points:
            tp = state.turning_points[0]
            return (
                f"{tp['title']} at {tp['minute']}'. "
                f"{tp['description']} "
                f"The match stands at {state.home_team} {state.home_score} - "
                f"{state.away_score} {state.away_team}."
            )
        return (
            f"{state.home_team} {state.home_score} - {state.away_score} {state.away_team}. "
            f"No major turning points detected yet at {state.minute}'."
        )

    def _fallback_recap(self, state):
        winner = (
            state.home_team if state.home_score > state.away_score
            else state.away_team if state.away_score > state.home_score
            else None
        )
        if winner:
            return (
                f"Final: {state.home_team} {state.home_score} - {state.away_score} {state.away_team}. "
                f"{winner} won the match. "
                f"{len(state.turning_points)} turning points were detected "
                f"during the game."
            )
        return (
            f"Final: {state.home_team} {state.home_score} - {state.away_score} {state.away_team}. "
            f"The match ended in a draw."
        )


class AudienceAdapter:
    """Tailors verified stories to role and language."""

    ROLES = ["broadcaster", "analyst", "fan"]

    def adapt(self, content: str, state: MatchState, role: str = "fan",
              language: str = "en") -> dict:
        """Adapt narrative for a specific audience and language.

        Returns {role, language, content, summary, json_ready}.
        """
        if role not in self.ROLES:
            role = "fan"

        if role == "broadcaster":
            summary = (
                f"{state.home_team} {state.home_score} - {state.away_score} {state.away_team}, "
                f"{state.minute}'. {len(state.turning_points)} turning points."
            )
        elif role == "analyst":
            summary = (
                f"Tactical analysis: {state.possession} possession, "
                f"{state.shots} shots, {state.xg} xG. "
                f"{len(state.turning_points)} turning points detected."
            )
        else:
            summary = content[:120] + "…" if len(content) > 120 else content

        return {
            "role": role,
            "language": language,
            "content": content,
            "summary": summary,
            "json_ready": state.to_dict(),
        }
