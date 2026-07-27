import os

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    pass


def _require_env(name):
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


class Config:
    def __init__(self):
        self.telegram_bot_token = _require_env("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = _require_env("TELEGRAM_CHAT_ID")


def load_config():
    return Config()
