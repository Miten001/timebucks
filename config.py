"""Configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)

# Sponsor channels - your monetization slots
_sponsor_raw = os.getenv("SPONSOR_CHANNELS", "").strip()
SPONSOR_CHANNELS = [c.strip().lstrip("@") for c in _sponsor_raw.split(",") if c.strip()]

# Economy
COIN_TO_INR = float(os.getenv("COIN_TO_INR", "0.01"))
MIN_REDEEM_COINS = int(os.getenv("MIN_REDEEM_COINS", "5000"))

# Game settings
COINS_PER_CORRECT = 10
COINS_PER_REFERRAL = 50
DAILY_BONUS_COINS = 25
QUESTIONS_PER_GAME = 5
QUESTION_TIME_LIMIT = 30  # seconds

# Database
DB_PATH = os.getenv("DB_PATH", "quiz_bot.db")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Get one from @BotFather on Telegram and put it in .env"
    )
