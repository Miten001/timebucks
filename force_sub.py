"""Force-subscribe helper.

Users must join all sponsor channels before they can play.
THIS IS YOUR PRIMARY AD-REVENUE MECHANISM:
  - Other channels pay you (₹500-₹2000/month) to be in this list.
  - The bot itself becomes a "promotion service".
"""
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

from config import SPONSOR_CHANNELS


async def get_unjoined_channels(bot: Bot, user_id: int) -> list[str]:
    """Return list of channel usernames the user hasn't joined yet."""
    if not SPONSOR_CHANNELS:
        return []

    pending: list[str] = []
    for channel in SPONSOR_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if member.status not in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                pending.append(channel)
        except TelegramError:
            # Bot might not be admin in the channel; skip silently
            # but log so admin can fix.
            pending.append(channel)
    return pending


def build_join_keyboard(channels: list[str]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(f"📢 Join @{ch}", url=f"https://t.me/{ch}")]
        for ch in channels
    ]
    keyboard.append(
        [InlineKeyboardButton("✅ I've Joined - Verify", callback_data="verify_join")]
    )
    return InlineKeyboardMarkup(keyboard)
