import time

import requests

from .formatter import split_for_telegram


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    # Retry/backoff settings for transient failures (429 flood control, 5xx blips).
    MAX_ATTEMPTS = 5
    BASE_BACKOFF_SECONDS = 1

    def __init__(self, bot_token, chat_id, session=None, timeout=15):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.session = session or requests.Session()
        self.timeout = timeout

    def send_message(self, text, parse_mode="Markdown"):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        for chunk in split_for_telegram(text):
            # Each chunk is retried on its own before we give up, so a single
            # transient 429/5xx does not abort the run after earlier chunks
            # already landed (which would otherwise cause duplicate resends
            # on the next run, since state.json is only saved once all
            # chunks succeed).
            self._post_with_retry(url, chunk, parse_mode)

    def _post_with_retry(self, url, chunk, parse_mode):
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            resp = self.session.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": parse_mode,
                },
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                return
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == self.MAX_ATTEMPTS:
                    break
                # Telegram's 429 body includes retry_after (seconds) telling us
                # how long to wait before its per-chat rate limit resets; fall
                # back to exponential backoff for 5xx or if it's missing/unparseable.
                retry_after = None
                if resp.status_code == 429:
                    try:
                        retry_after = resp.json().get("parameters", {}).get("retry_after")
                    except ValueError:
                        retry_after = None
                delay = retry_after if retry_after is not None else self.BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                time.sleep(delay)
                continue
            # Non-retryable error (e.g. 400 bad request) - fail immediately.
            raise TelegramError(
                f"sendMessage failed: {resp.status_code} {resp.text[:300]}"
            )
        raise TelegramError(
            f"sendMessage failed after {self.MAX_ATTEMPTS} attempts: "
            f"{resp.status_code} {resp.text[:300]}"
        )
