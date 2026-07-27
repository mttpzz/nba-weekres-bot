from datetime import datetime

TELEGRAM_MAX_LEN = 4096

# Telegram's legacy "Markdown" parse mode (used by telegram_client.send_message)
# treats these characters as formatting tokens; any unescaped/unbalanced one in
# ESPN-sourced text (team/player names, matchups) makes the whole request 400.
_MD_SPECIAL_CHARS = ("_", "*", "`", "[")


def _escape_md(value):
    text = str(value)
    for ch in _MD_SPECIAL_CHARS:
        text = text.replace(ch, "\\" + ch)
    return text


def _fmt_date(iso_date):
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m")
    except ValueError:
        return iso_date


def compose_digest(since, until, games_by_day, top_performances, performance_of_week, standings_by_conf):
    lines = []
    lines.append(f"*🏀 Results ({_fmt_date(since)} - {_fmt_date(until)})*")
    if not games_by_day:
        lines.append("_No games in this period._")
    for date, games in games_by_day.items():
        lines.append(f"\n_{_fmt_date(date)}_")
        for g in games:
            # Team names come straight from ESPN JSON, so they must be escaped
            # before landing in Markdown text (see _escape_md above).
            lines.append(
                f"{_escape_md(g['away_team'])} {g['away_points']} - "
                f"{g['home_points']} {_escape_md(g['home_team'])}"
            )

    if top_performances:
        lines.append("\n*⭐ Top performances of the week*")
        for p in top_performances:
            lines.append(
                f"{_escape_md(p['player'])} ({_escape_md(p['team'])}) — "
                f"{_escape_md(p['matchup'])}, {_fmt_date(p['date'])}: "
                f"{p['points']} PTS / {p['reb']} REB / {p['ast']} AST "
                f"— Game Score {p['game_score']}"
            )

    if performance_of_week:
        p = performance_of_week
        lines.append("\n*🔥 Performance of the week*")
        lines.append(
            f"{_escape_md(p['player'])} ({_escape_md(p['team'])}) — {p['points']} PTS / {p['reb']} REB / "
            f"{p['ast']} AST / {p['stl']} STL / {p['blk']} BLK "
            f"(Game Score {p['game_score']}) — {_escape_md(p['matchup'])} on {_fmt_date(p['date'])}"
        )

    lines.append("\n*📊 Updated standings*")
    for conf_label, key in (("Eastern Conference", "east"), ("Western Conference", "west")):
        rows = standings_by_conf.get(key) or []
        if not rows:
            continue
        lines.append(f"\n_{conf_label}_")
        for r in rows:
            lines.append(f"{r['rank']}. {_escape_md(r['team'])} ({r['win']}-{r['loss']})")

    return "\n".join(lines)


def split_for_telegram(text, max_len=TELEGRAM_MAX_LEN):
    """Split text into chunks that fit Telegram's message size limit,
    breaking on line boundaries so formatting stays intact."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = []
    current_len = 0
    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > max_len and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks
