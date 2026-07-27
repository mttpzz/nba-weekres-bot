import requests

# ESPN's public, unauthenticated NBA endpoints. Undocumented/unofficial but
# widely used and, unlike api-sports.io's free plan, not restricted to a
# narrow rolling date window and don't require an API key.
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"

BOX_SCORE_FIELD_BY_LABEL = {
    "PTS": "points",
    "TO": "turnovers",
    "STL": "steals",
    "BLK": "blocks",
    "OREB": "offReb",
    "DREB": "defReb",
    "PF": "pFouls",
    "REB": "totReb",
    "AST": "assists",
}


class NbaDataError(RuntimeError):
    pass


def _split_made_attempted(value):
    try:
        made, attempted = value.split("-")
        return int(made), int(attempted)
    except (ValueError, AttributeError):
        return 0, 0


def _split_name(display_name):
    parts = (display_name or "?").split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], ""


class EspnClient:
    def __init__(self, session=None, timeout=15):
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get_json(self, url, params=None):
        resp = self.session.get(url, params=params or {}, timeout=self.timeout)
        if resp.status_code != 200:
            raise NbaDataError(f"GET {url} failed: {resp.status_code} {resp.text[:300]}")
        return resp.json()

    def get_games(self, date):
        """date: 'YYYY-MM-DD'. Returns finished-game dicts for that date, in the
        shape the rest of the app expects (status/teams/scores/date.start)."""
        data = self._get_json(SCOREBOARD_URL, {"dates": date.replace("-", "")})
        games = []
        for event in data.get("events", []):
            competition = (event.get("competitions") or [{}])[0]
            status = competition.get("status") or {}
            finished = ((status.get("type") or {}).get("name")) == "STATUS_FINAL"
            competitors = {c.get("homeAway"): c for c in competition.get("competitors", [])}
            home = competitors.get("home") or {}
            away = competitors.get("away") or {}
            games.append(
                {
                    "id": event.get("id"),
                    "date": {"start": event.get("date")},
                    "status": {"long": "Finished" if finished else "Not Finished"},
                    "teams": {
                        "home": {"name": (home.get("team") or {}).get("displayName", "?")},
                        "visitors": {"name": (away.get("team") or {}).get("displayName", "?")},
                    },
                    "scores": {
                        "home": {"points": int(home.get("score", 0) or 0)},
                        "visitors": {"points": int(away.get("score", 0) or 0)},
                    },
                }
            )
        return games

    def get_player_stats(self, game_id):
        """Box score rows (one per player) for a single finished game, in the
        shape gamescore.py / aggregator.py expect."""
        data = self._get_json(SUMMARY_URL, {"event": game_id})
        rows = []
        for team_block in (data.get("boxscore") or {}).get("players", []):
            team_name = (team_block.get("team") or {}).get("displayName", "?")
            for stat_group in team_block.get("statistics", []):
                labels = stat_group.get("labels", [])
                for athlete_row in stat_group.get("athletes", []):
                    stats_values = athlete_row.get("stats") or []
                    if not stats_values or athlete_row.get("didNotPlay"):
                        continue
                    stat_map = dict(zip(labels, stats_values))
                    fgm, fga = _split_made_attempted(stat_map.get("FG", "0-0"))
                    ftm, fta = _split_made_attempted(stat_map.get("FT", "0-0"))
                    firstname, lastname = _split_name(
                        (athlete_row.get("athlete") or {}).get("displayName")
                    )
                    row = {
                        "player": {"firstname": firstname, "lastname": lastname},
                        "team": {"name": team_name},
                        "fgm": fgm,
                        "fga": fga,
                        "ftm": ftm,
                        "fta": fta,
                    }
                    for label, field in BOX_SCORE_FIELD_BY_LABEL.items():
                        try:
                            row[field] = int(stat_map.get(label, 0))
                        except ValueError:
                            row[field] = 0
                    rows.append(row)
        return rows

    def get_standings(self):
        """Current-season standings grouped by conference.

        Returns {"east": [...], "west": [...]}, each a list of
        {"rank", "team", "win", "loss"} sorted by playoff seed.
        """
        data = self._get_json(STANDINGS_URL)
        by_conf = {"east": [], "west": []}
        conf_key_by_name = {"Eastern Conference": "east", "Western Conference": "west"}
        for conf in data.get("children", []):
            key = conf_key_by_name.get(conf.get("name"))
            if not key:
                continue
            for entry in (conf.get("standings") or {}).get("entries", []):
                stats = {
                    s["name"]: s["value"]
                    for s in entry.get("stats", [])
                    if "value" in s
                }
                by_conf[key].append(
                    {
                        "rank": int(stats.get("playoffSeed", 999)),
                        "team": (entry.get("team") or {}).get("displayName", "?"),
                        "win": int(stats.get("wins", 0)),
                        "loss": int(stats.get("losses", 0)),
                    }
                )
            by_conf[key].sort(key=lambda r: r["rank"])
        return by_conf
