from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from .gamescore import game_score

# NBA slates are scheduled/queried by US Eastern date, but ESPN reports
# event timestamps in UTC; an evening US tip-off (e.g. 7:30pm PT) rolls
# over to the next UTC calendar day, so we must convert back to Eastern
# before truncating to a date, or games land under the wrong day.
US_EASTERN = ZoneInfo("America/New_York")


def is_finished(game):
    return (game.get("status") or {}).get("long") == "Finished"


def game_date(game):
    """Returns the 'YYYY-MM-DD' date the game was played on (US Eastern slate date)."""
    start = (game.get("date") or {}).get("start") or ""
    if not start:
        return ""
    # ESPN's timestamps end in 'Z'; datetime.fromisoformat needs an explicit offset.
    iso = start.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return start[:10]
    return dt.astimezone(US_EASTERN).strftime("%Y-%m-%d")


def summarize_game(game):
    teams = game.get("teams") or {}
    scores = game.get("scores") or {}
    home = teams.get("home") or {}
    away = teams.get("visitors") or {}
    home_pts = (scores.get("home") or {}).get("points")
    away_pts = (scores.get("visitors") or {}).get("points")
    return {
        "game_id": game.get("id"),
        "date": game_date(game),
        "home_team": home.get("name") or home.get("code") or "?",
        "away_team": away.get("name") or away.get("code") or "?",
        "home_points": home_pts,
        "away_points": away_pts,
    }


def group_games_by_day(games):
    """games: list of raw finished game dicts -> {date: [summary, ...]} sorted by date."""
    by_day = defaultdict(list)
    for game in games:
        by_day[game_date(game)].append(summarize_game(game))
    return dict(sorted(by_day.items()))


def build_player_rows(game_summary, stat_rows):
    """Attach Game Score + matchup context to each player's box-score row."""
    matchup = f"{game_summary['away_team']} @ {game_summary['home_team']}"
    enriched = []
    for row in stat_rows:
        player = row.get("player") or {}
        team = row.get("team") or {}
        name = f"{player.get('firstname', '').strip()} {player.get('lastname', '').strip()}".strip()
        if not name:
            continue
        enriched.append(
            {
                "player": name,
                "team": team.get("name") or team.get("code") or "?",
                "matchup": matchup,
                "date": game_summary["date"],
                "points": row.get("points", 0) or 0,
                "reb": row.get("totReb", 0) or 0,
                "ast": row.get("assists", 0) or 0,
                "stl": row.get("steals", 0) or 0,
                "blk": row.get("blocks", 0) or 0,
                "game_score": round(game_score(row), 1),
            }
        )
    return enriched


def top_performances(all_player_rows, n=5):
    return sorted(all_player_rows, key=lambda r: r["game_score"], reverse=True)[:n]


def performance_of_the_week(all_player_rows):
    top = top_performances(all_player_rows, n=1)
    return top[0] if top else None
