import argparse
import sys
from datetime import date, datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from .aggregator import (
    build_player_rows,
    group_games_by_day,
    is_finished,
    performance_of_the_week,
    summarize_game,
    top_performances,
)
from .api_client import EspnClient
from .config import load_config
from .formatter import compose_digest
from .state import load_last_sent_date, save_last_sent_date
from .telegram_client import TelegramClient


def _parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _daterange(since, until):
    d = since
    while d <= until:
        yield d
        d += timedelta(days=1)


def build_args(argv=None):
    parser = argparse.ArgumentParser(description="NBA weekly Telegram digest")
    parser.add_argument("--since", type=_parse_date, help="YYYY-MM-DD, overrides state file")
    parser.add_argument("--until", type=_parse_date, help="YYYY-MM-DD, default: today")
    parser.add_argument("--state-file", default=None)
    parser.add_argument("--dry-run", action="store_true", help="print message instead of sending")
    return parser.parse_args(argv)


def run(argv=None):
    args = build_args(argv)

    until = args.until or date.today()
    if args.since:
        since = args.since
    else:
        last_sent = load_last_sent_date(args.state_file) if args.state_file else load_last_sent_date()
        # _daterange is inclusive of both ends, so "last 7 days" means until minus 6, not 7.
        since = _parse_date(last_sent) + timedelta(days=1) if last_sent else until - timedelta(days=6)

    if since > until:
        print(f"Nothing to do: since ({since}) is after until ({until}).")
        return

    config = load_config()
    api = EspnClient()

    finished_games = []
    for d in _daterange(since, until):
        games = api.get_games(d.isoformat())
        finished_games.extend(g for g in games if is_finished(g))

    games_by_day = group_games_by_day(finished_games)

    all_player_rows = []
    for game in finished_games:
        stat_rows = api.get_player_stats(game.get("id"))
        all_player_rows.extend(build_player_rows(summarize_game(game), stat_rows))

    top5 = top_performances(all_player_rows, n=5)
    poy = performance_of_the_week(all_player_rows)

    standings_by_conf = api.get_standings()

    message = compose_digest(
        since.isoformat(), until.isoformat(), games_by_day, top5, poy, standings_by_conf
    )

    if not finished_games:
        print("No games in this period, digest not sent.")
    elif args.dry_run:
        print(message)
    else:
        telegram = TelegramClient(config.telegram_bot_token, config.telegram_chat_id)
        telegram.send_message(message)
        print("Digest sent to Telegram.")

    # Don't persist state on dry runs: no message was actually sent, so the
    # range must remain available for the next real (scheduled) run.
    if args.dry_run:
        pass
    elif not args.state_file:
        save_last_sent_date(until.isoformat())
    else:
        save_last_sent_date(until.isoformat(), args.state_file)


if __name__ == "__main__":
    sys.exit(run())
