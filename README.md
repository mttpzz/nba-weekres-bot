# NBA Weekly Results Bot 🏀

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Weekly Telegram digest: results of every NBA game played that week, top
player performances (with a highlighted "performance of the week", computed
via the Hollinger Game Score) and updated standings.

Runs for free on GitHub Actions with a weekly cron (Mondays at 9:00 Italian
time), no server to maintain.

Data (results, box scores, standings) comes from ESPN's unofficial public
APIs (`site.api.espn.com`) — free, no API key, no date restrictions, no
registration required. (api-sports.io's free plan was ruled out: it limits
queries to a ~3-day rolling window around today and blocks current-season
standings, incompatible with a weekly digest.)

## Sample output

```
🏀 Results (01/04 - 02/04)

01/04
Philadelphia 76ers 153 - 131 Washington Wizards
Boston Celtics 147 - 129 Miami Heat

⭐ Top performances of the week
Victor Wembanyama (San Antonio Spurs) — San Antonio Spurs @ Golden State Warriors, 02/04: 41 PTS / 18 REB / 3 AST — Game Score 41.2
Paul George (Philadelphia 76ers) — Philadelphia 76ers @ Washington Wizards, 01/04: 39 PTS / 5 REB / 6 AST — Game Score 37.1

🔥 Performance of the week
Victor Wembanyama (San Antonio Spurs) — 41 PTS / 18 REB / 3 AST / 0 STL / 3 BLK (Game Score 41.2) — San Antonio Spurs @ Golden State Warriors on 02/04

📊 Updated standings

Eastern Conference
1. Detroit Pistons (60-22)
2. Boston Celtics (56-26)
...
```

## Setup

### 1. Create the Telegram bot

1. Open a chat with [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot`, follow the prompts, get your **bot token** (e.g. `123456:ABC-...`).
3. Send any message to your new bot (needed to make the chat show up).
4. Get your **chat id**: open in a browser
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` after sending the
   message, and read the `chat.id` field in the JSON response.

### 2. Configure the GitHub repository

1. Fork or clone this repository.
2. In `Settings > Secrets and variables > Actions`, add 2 secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. The workflow `.github/workflows/nba-weekres.yml` runs every Monday at
   9:00 (Italian time). You can also trigger it manually from
   `Actions > nba-weekres > Run workflow`.

## Local development

```bash
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) with `TELEGRAM_BOT_TOKEN` and
`TELEGRAM_CHAT_ID` — it's loaded automatically.

```bash
# print the message instead of sending it to Telegram
python -m nba_weekres.main --since 2026-04-01 --until 2026-04-07 --dry-run

# actually send it
python -m nba_weekres.main --since 2026-04-01 --until 2026-04-07
```

Without `--since`/`--until`, the script uses `state.json` to resume from the
last successful send (or the last 7 days on first run) up to today.

### Unit tests

```bash
python -m unittest discover tests
```

## How it works

- `nba_weekres/api_client.py` — client for ESPN's public APIs (games, box scores, standings).
- `nba_weekres/gamescore.py` — Hollinger Game Score formula.
- `nba_weekres/aggregator.py` — groups results by day and computes top performances.
- `nba_weekres/formatter.py` — builds the digest's Markdown message.
- `nba_weekres/telegram_client.py` — sends it via the Telegram Bot API.
- `nba_weekres/main.py` — orchestrator, CLI entry point.

## Notes

- "Performance of the week" is the statline with the highest **Game Score**
  (Hollinger) of the week — a proxy for the best individual performance,
  computed from standard box score stats. The free APIs used here don't
  include play-by-play data, so there's no real highlight/replay of a single
  "play".
- If there are no games in the period (All-Star break, off-season), no
  digest is sent.
- Telegram messages are capped at 4096 characters: if the digest exceeds
  that, it's automatically split into multiple messages.
- The ESPN endpoints used are public but unofficial/undocumented: stable for
  years and widely used in open source projects, but could change without
  notice.

## Contributing

Issues and pull requests are welcome.

## License

[MIT](LICENSE) © Matteo Pozzi
