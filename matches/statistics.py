"""
Match state statistics computation.

Computes deterministic match statistics from MatchEvents:
possession, shot volume, pressure in final third, passing accuracy,
xG, time in attacking third, events per minute window.
"""
from collections import defaultdict


class MatchStats:
    """Computed statistics for a match, grounded in stored events."""

    def __init__(self, match, events):
        self.match = match
        self.events = list(events)
        self.home = match.home_team
        self.away = match.away_team

    def possession(self):
        """Proxy possession: share of pass + pressure events per team."""
        home_events = [e for e in self.events if e.team == self.home]
        away_events = [e for e in self.events if e.team == self.away]
        total = len(home_events) + len(away_events)
        if total == 0:
            return {self.home: 50, self.away: 50}
        home_share = round(100 * len(home_events) / total)
        return {self.home: home_share, self.away: 100 - home_share}

    def shots(self):
        """Shot counts per team."""
        return {
            self.home: len([e for e in self.events if e.team == self.home and e.event_type == "shot"]),
            self.away: len([e for e in self.events if e.team == self.away and e.event_type == "shot"]),
        }

    def shots_on_target(self):
        """Shots with xG >= 0.15 counted as on target."""
        return {
            self.home: len([e for e in self.events
                            if e.team == self.home
                            and e.event_type in ("shot", "goal", "save")
                            and e.xg_value and e.xg_value >= 0.15]),
            self.away: len([e for e in self.events
                            if e.team == self.away
                            and e.event_type in ("shot", "goal", "save")
                            and e.xg_value and e.xg_value >= 0.15]),
        }

    def pressure_in_final_third(self):
        """Pressure events in attacking third (x > 66) per team."""
        return {
            self.home: len([e for e in self.events
                            if e.team == self.home and e.event_type == "pressure"
                            and e.x and e.x > 66]),
            self.away: len([e for e in self.events
                            if e.team == self.away and e.event_type == "pressure"
                            and e.x and e.x > 66]),
        }

    def xg(self):
        """Expected goals per team (sum of shot xG)."""
        home_xg = sum(e.xg_value for e in self.events
                      if e.team == self.home and e.event_type == "shot" and e.xg_value)
        away_xg = sum(e.xg_value for e in self.events
                      if e.team == self.away and e.event_type == "shot" and e.xg_value)
        return {self.home: round(home_xg, 2), self.away: round(away_xg, 2)}

    def events_by_minute_window(self, window_minutes=10):
        """Event counts per team in sliding windows."""
        windows = defaultdict(lambda: defaultdict(int))
        for e in self.events:
            window = (e.minute // window_minutes) * window_minutes
            windows[window][e.team] += 1
        return dict(windows)

    def events_by_type(self):
        """Event type counts per team."""
        home_types = defaultdict(int)
        away_types = defaultdict(int)
        for e in self.events:
            if e.team == self.home:
                home_types[e.event_type] += 1
            elif e.team == self.away:
                away_types[e.event_type] += 1
        return {self.home: home_types, self.away: away_types}

    def as_dict(self):
        return {
            "possession": self.possession(),
            "shots": self.shots(),
            "shots_on_target": self.shots_on_target(),
            "pressure_final_third": self.pressure_in_final_third(),
            "xg": self.xg(),
            "total_events": len(self.events),
        }
