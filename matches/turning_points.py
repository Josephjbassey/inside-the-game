"""
Turning-point detection.

Analyzes event sequences and computed statistics to identify meaningful
changes in match momentum. Each detected turning point is linked to the
specific events that support it — no LLM-invented explanations.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TurningPoint:
    minute: int
    title: str
    description: str
    evidence: List[dict]  # matching events
    impact: str  # 'home_advantage', 'away_advantage', 'neutral'
    confidence: str  # 'high', 'medium', 'low'


def detect_turning_points(match, events, stats):
    """Detect turning points in a match based on events and stats.

    Returns a list of TurningPoint dataclasses, newest first.
    """
    points = []
    event_list = list(events)

    # 1. Goal is always a turning point
    for e in event_list:
        if e.event_type == "goal":
            team = e.team
            opponent = match.away_team if team == match.home_team else match.home_team
            points.append(TurningPoint(
                minute=e.minute,
                title=f"Goal — {team}",
                description=f"{e.player} scored for {team}.",
                evidence=[{"minute": e.minute, "event": e.event_type,
                           "player": e.player, "team": e.team,
                           "xg": e.xg_value}],
                impact=f"{team}_advantage",
                confidence="high",
            ))

    # 2. Pressure surge: >2 pressure events in final third within 5 minutes
    pressure_events = [e for e in event_list if e.event_type == "pressure"]
    for i in range(len(pressure_events) - 1):
        window = [e for e in pressure_events[i:]
                  if e.minute - pressure_events[i].minute <= 5]
        if len(window) >= 3:
            team = window[0].team
            opponent = match.away_team if team == match.home_team else match.home_team
            points.append(TurningPoint(
                minute=window[0].minute,
                title=f"Pressure surge — {team}",
                description=(
                    f"{team} applied {len(window)} pressure events in the "
                    f"final third within 5 minutes starting {window[0].minute}'."
                ),
                evidence=[{"minute": e.minute, "event": e.event_type,
                           "player": e.player, "team": e.team,
                           "x": e.x, "y": e.y} for e in window],
                impact=f"{team}_advantage",
                confidence="medium",
            ))
            break  # only one pressure surge turning point

    # 3. Shot volume shift: one team has 3x more shots in last 15 minutes
    recent_events = [e for e in event_list if e.minute >= 75]
    if recent_events:
        home_shots = len([e for e in recent_events
                          if e.team == match.home_team and e.event_type == "shot"])
        away_shots = len([e for e in recent_events
                          if e.team == match.away_team and e.event_type == "shot"])
        if home_shots >= 3 and home_shots >= 3 * away_shots and away_shots >= 1:
            points.append(TurningPoint(
                minute=75,
                title="Shot volume shift — home",
                description=(
                    f"Home side created {home_shots} shots vs {away_shots} "
                    f"for away in the last 15 minutes."
                ),
                evidence=[{"minute": e.minute, "event": e.event_type,
                           "player": e.player, "team": e.team,
                           "xg": e.xg_value} for e in recent_events
                          if e.team == match.home_team and e.event_type == "shot"],
                impact="home_advantage",
                confidence="medium",
            ))
        elif away_shots >= 3 and away_shots >= 3 * home_shots and home_shots >= 1:
            points.append(TurningPoint(
                minute=75,
                title="Shot volume shift — away",
                description=(
                    f"Away side created {away_shots} shots vs {home_shots} "
                    f"for home in the last 15 minutes."
                ),
                evidence=[{"minute": e.minute, "event": e.event_type,
                           "player": e.player, "team": e.team,
                           "xg": e.xg_value} for e in recent_events
                          if e.team == match.away_team and e.event_type == "shot"],
                impact="away_advantage",
                confidence="medium",
            ))

    # 4. Substitution impact: goal within 10 minutes of a sub
    subs = [e for e in event_list if e.event_type == "substitution"]
    goals = [e for e in event_list if e.event_type == "goal"]
    for sub in subs:
        for goal in goals:
            if 0 <= goal.minute - sub.minute <= 10:
                team = sub.team
                points.append(TurningPoint(
                    minute=goal.minute,
                    title=f"Substitution impact — {team}",
                    description=(
                        f"{team} scored {goal.minute - sub.minute} minutes "
                        f"after a substitution."
                    ),
                    evidence=[
                        {"minute": sub.minute, "event": sub.event_type,
                         "player": sub.player, "team": sub.team},
                        {"minute": goal.minute, "event": goal.event_type,
                         "player": goal.player, "team": goal.team,
                         "xg": goal.xg_value},
                    ],
                    impact=f"{team}_advantage",
                    confidence="medium",
                ))
                break

    # Sort by minute descending (newest first), dedupe by title
    seen = set()
    unique = []
    for p in sorted(points, key=lambda x: x.minute, reverse=True):
        if p.title not in seen:
            seen.add(p.title)
            unique.append(p)
    return unique
