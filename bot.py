"""Telegram Mini-Games Bot — entry point.

Features:
  • 6 mini games (Quiz / Number Guess / RPS / Coin Flip / Dice / Math Quick)
  • Coin economy with daily bonus and refer & earn
  • Force-subscribe sponsor channels (your ad-revenue mechanism)
  • Leaderboard, profile, redeem (manual via admin)

Run:
  pip install -r requirements.txt
  cp .env.example .env  &&  edit .env
  python bot.py
"""
from __future__ import annotations

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import database as db
import games
from config import (
    ADMIN_ID,
    BOT_TOKEN,
    COINS_PER_REFERRAL,
    COIN_TO_INR,
    DAILY_BONUS_COINS,
    MIN_REDEEM_COINS,
    SPONSOR_CHANNELS,
)
from force_sub import build_join_keyboard, get_unjoined_channels

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Menus
# ─────────────────────────────────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎮 Free Games", callback_data="menu:free"),
            InlineKeyboardButton("💰 Betting Games", callback_data="menu:betting"),
        ],
        [
            InlineKeyboardButton("👤 Profile", callback_data="menu:profile"),
            InlineKeyboardButton("🏆 Leaders", callback_data="menu:leaders"),
        ],
        [
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="menu:daily"),
            InlineKeyboardButton("🤝 Refer", callback_data="menu:refer"),
        ],
        [
            InlineKeyboardButton("💸 Redeem", callback_data="menu:redeem"),
            InlineKeyboardButton("ℹ️ Help", callback_data="menu:help"),
        ],
    ])


def free_games_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧠 Quiz", callback_data="game:quiz"),
            InlineKeyboardButton("🎯 Number Guess", callback_data="game:guess"),
        ],
        [
            InlineKeyboardButton("🪨📄✂️ RPS", callback_data="game:rps"),
            InlineKeyboardButton("➗ Math Quick", callback_data="game:math"),
        ],
        [
            InlineKeyboardButton("🔤 Word Scramble", callback_data="game:word"),
            InlineKeyboardButton("⭕❌ Tic Tac Toe", callback_data="game:ttt"),
        ],
        [
            InlineKeyboardButton("🎬 Emoji Quiz", callback_data="game:emoji"),
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")],
    ])


def betting_games_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🪙 Coin Flip", callback_data="game:coinflip"),
            InlineKeyboardButton("🎲 Dice", callback_data="game:dice"),
        ],
        [
            InlineKeyboardButton("🎰 Slot Machine", callback_data="game:slot"),
            InlineKeyboardButton("🃏 Hi-Lo Cards", callback_data="game:hilo"),
        ],
        [
            InlineKeyboardButton("🎨 Color Predict", callback_data="game:color"),
            InlineKeyboardButton("🎡 Lucky Wheel", callback_data="game:wheel"),
        ],
        [
            InlineKeyboardButton("🚀 Aviator Crash", callback_data="game:aviator"),
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")],
    ])


def main_menu_text(user_row: dict) -> str:
    return (
        f"🎮 <b>Mini Games Bot</b>\n"
        f"Welcome, {user_row.get('first_name') or 'Player'}!\n\n"
        f"💳 Coins: <b>{user_row['coins']}</b>\n"
        f"🎯 Games played: <b>{user_row['games_played']}</b>\n\n"
        "👇 Game choose karo:"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Force subscribe gate
# ─────────────────────────────────────────────────────────────────────────────

async def require_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True if user is OK to play. If not, send join prompt."""
    if not SPONSOR_CHANNELS:
        return True
    pending = await get_unjoined_channels(context.bot, update.effective_user.id)
    if not pending:
        return True
    text = (
        "🔒 <b>Channels join karne padenge</b>\n\n"
        "Bot use karne ke liye in channels mein join karo, fir <b>Verify</b> dabao:"
    )
    await (update.effective_message or update.callback_query.message).reply_text(
        text, reply_markup=build_join_keyboard(pending), parse_mode="HTML"
    )
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Command handlers
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Detect referral: /start <ref_id>
    referred_by = None
    if context.args:
        try:
            ref_id = int(context.args[0])
            if ref_id != user.id:
                referred_by = ref_id
        except ValueError:
            pass

    existing = db.get_user(user.id)
    is_new = existing is None
    user_row = db.add_or_get_user(
        user.id,
        user.username,
        user.first_name,
        referred_by=referred_by if is_new else None,
    )

    # Reward referrer if this is a new user with a valid referrer
    if is_new and referred_by:
        if db.get_user(referred_by):
            db.add_coins(referred_by, COINS_PER_REFERRAL)
            try:
                await context.bot.send_message(
                    referred_by,
                    f"🎉 New referral joined!\n💰 +{COINS_PER_REFERRAL} coins",
                )
            except Exception:
                pass

    if not await require_subscribed(update, context):
        return

    # Show a group-aware hint above the menu when invoked from a group/supergroup
    is_group = bool(
        update.effective_chat and update.effective_chat.type in ("group", "supergroup")
    )
    intro = main_menu_text(user_row)
    if is_group:
        intro = (
            "👥 <b>Group Play Mode</b>\n"
            "Har player apna khud ka game khel sakta hai 🎮\n"
            "Sirf jisne start kiya wo apne buttons dabaye.\n\n"
            f"{intro}"
        )

    await update.effective_message.reply_text(
        intro,
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_row = db.add_or_get_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
    )
    inr = round(user_row["coins"] * COIN_TO_INR, 2)
    await update.message.reply_text(
        f"💳 Balance: <b>{user_row['coins']}</b> coins (~ ₹{inr})",
        parse_mode="HTML",
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total = db.total_users()
    leaders = db.get_leaderboard(5)
    text = f"📊 <b>Admin Stats</b>\nTotal users: {total}\n\nTop 5:\n"
    for i, u in enumerate(leaders, 1):
        text += f"{i}. {u.get('first_name') or 'User'} - {u['coins']} coins\n"
    await update.message.reply_text(text, parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────────────────
# Callback router
# ─────────────────────────────────────────────────────────────────────────────

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    # Force-subscribe verification
    if data == "verify_join":
        pending = await get_unjoined_channels(context.bot, update.effective_user.id)
        if pending:
            await query.answer("Abhi tak sab channels join nahi kiye.", show_alert=True)
            return
        user_row = db.add_or_get_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
        )
        await query.edit_message_text(
            main_menu_text(user_row), reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        return

    # All other actions require sub
    if not await require_subscribed(update, context):
        return

    # Menu navigation
    if data == "menu:main":
        user_row = db.add_or_get_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
        )
        await query.edit_message_text(
            main_menu_text(user_row), reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        return

    if data == "menu:free":
        await query.edit_message_text(
            "🎮 <b>Free Games</b>\nKhelo aur coins kamao (no bet):",
            reply_markup=free_games_kb(),
            parse_mode="HTML",
        )
        return

    if data == "menu:betting":
        u = db.get_user(update.effective_user.id)
        await query.edit_message_text(
            f"💰 <b>Betting Games</b>\nCoins lagao, jeeto big!\n\n"
            f"💳 Balance: <b>{u['coins'] if u else 0}</b>",
            reply_markup=betting_games_kb(),
            parse_mode="HTML",
        )
        return

    if data == "menu:profile":
        u = db.get_user(update.effective_user.id)
        refs = db.get_referral_count(update.effective_user.id)
        inr = round(u["coins"] * COIN_TO_INR, 2)
        text = (
            f"👤 <b>Profile</b>\n\n"
            f"Name: {u.get('first_name') or '-'}\n"
            f"💳 Coins: <b>{u['coins']}</b> (~ ₹{inr})\n"
            f"🎯 Games played: {u['games_played']}\n"
            f"✅ Correct: {u['correct_answers']}\n"
            f"🤝 Referrals: {refs}"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Menu", callback_data="menu:main")]]
            ),
            parse_mode="HTML",
        )
        return

    if data == "menu:leaders":
        rows = db.get_leaderboard(10)
        lines = ["🏆 <b>Top 10 Players</b>\n"]
        medals = ["🥇", "🥈", "🥉"]
        for i, u in enumerate(rows):
            mark = medals[i] if i < 3 else f"{i + 1}."
            name = u.get("first_name") or u.get("username") or "Player"
            lines.append(f"{mark} {name} — <b>{u['coins']}</b> coins")
        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Menu", callback_data="menu:main")]]
            ),
            parse_mode="HTML",
        )
        return

    if data == "menu:daily":
        claimed, balance = db.claim_daily_bonus(update.effective_user.id, DAILY_BONUS_COINS)
        if claimed:
            text = f"🎁 Daily bonus claimed!\n💰 +{DAILY_BONUS_COINS}\n💳 Balance: <b>{balance}</b>"
        else:
            text = "⏳ Aaj ka bonus already claimed.\nKal phir try karo."
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Menu", callback_data="menu:main")]]
            ),
            parse_mode="HTML",
        )
        return

    if data == "menu:refer":
        bot_user = await context.bot.get_me()
        link = f"https://t.me/{bot_user.username}?start={update.effective_user.id}"
        refs = db.get_referral_count(update.effective_user.id)
        text = (
            "🤝 <b>Refer & Earn</b>\n\n"
            f"Aapke har referral pe <b>{COINS_PER_REFERRAL} coins</b>!\n\n"
            f"Aapka link:\n<code>{link}</code>\n\n"
            f"Total referrals: <b>{refs}</b>"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Menu", callback_data="menu:main")]]
            ),
            parse_mode="HTML",
        )
        return

    if data == "menu:redeem":
        u = db.get_user(update.effective_user.id)
        if u["coins"] < MIN_REDEEM_COINS:
            text = (
                f"💸 <b>Redeem</b>\n\n"
                f"Minimum: <b>{MIN_REDEEM_COINS}</b> coins\n"
                f"Aapke: <b>{u['coins']}</b> coins\n\n"
                f"Aur khelo aur coins kamao!"
            )
        else:
            context.user_data["awaiting_upi"] = True
            inr = round(u["coins"] * COIN_TO_INR, 2)
            text = (
                f"💸 <b>Redeem Request</b>\n\n"
                f"Available: <b>{u['coins']}</b> coins (~ ₹{inr})\n\n"
                "Apna UPI ID bhejo (e.g., yourname@paytm).\n"
                "Admin manually process karega 24-48 hours mein."
            )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Menu", callback_data="menu:main")]]
            ),
            parse_mode="HTML",
        )
        return

    if data == "menu:help":
        text = (
            "ℹ️ <b>Help</b>\n\n"
            "🎮 6 mini games available — har game se coins kamao.\n"
            "🎁 Daily bonus claim karo har din.\n"
            "🤝 Friends ko refer karo — har referral pe bonus.\n"
            f"💸 {MIN_REDEEM_COINS} coins jamake UPI mein redeem karo.\n\n"
            "Commands:\n"
            "/start - Main menu\n"
            "/balance - Coin balance dekho"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Menu", callback_data="menu:main")]]
            ),
            parse_mode="HTML",
        )
        return

    # ── Game launchers ──
    if data == "game:quiz":
        await games.quiz_pick_category(update, context)
        return
    if data.startswith("quiz_cat:"):
        await games.quiz_start(update, context, data.split(":", 1)[1])
        return
    if data.startswith("quiz_ans:"):
        await games.quiz_answer(update, context, int(data.split(":", 1)[1]))
        return

    if data == "game:guess":
        await games.guess_start(update, context)
        return

    if data == "game:rps":
        await games.rps_start(update, context)
        return
    if data.startswith("rps:"):
        await games.rps_play(update, context, data.split(":", 1)[1])
        return

    if data == "game:coinflip":
        await games.coinflip_menu(update, context)
        return
    if data.startswith("cf_bet:"):
        await games.coinflip_choose_side(update, context, int(data.split(":", 1)[1]))
        return
    if data.startswith("cf_side:"):
        await games.coinflip_play(update, context, data.split(":", 1)[1])
        return

    if data == "game:dice":
        await games.dice_menu(update, context)
        return
    if data.startswith("dice_bet:"):
        await games.dice_play(update, context, int(data.split(":", 1)[1]))
        return

    if data == "game:math":
        await games.math_start(update, context)
        return
    if data.startswith("math_ans:"):
        await games.math_answer(update, context, int(data.split(":", 1)[1]))
        return

    # ── Slot Machine ──
    if data == "game:slot":
        await games.slot_menu(update, context)
        return
    if data.startswith("slot_bet:"):
        await games.slot_play(update, context, int(data.split(":", 1)[1]))
        return

    # ── Tic Tac Toe ──
    if data == "game:ttt":
        await games.ttt_start(update, context)
        return
    if data == "ttt:noop":
        return  # ignore clicks on filled cells
    if data.startswith("ttt:"):
        await games.ttt_play(update, context, int(data.split(":", 1)[1]))
        return

    # ── Hi-Lo Cards ──
    if data == "game:hilo":
        await games.hilo_menu(update, context)
        return
    if data.startswith("hilo_bet:"):
        await games.hilo_choose_dir(update, context, int(data.split(":", 1)[1]))
        return
    if data.startswith("hilo_dir:"):
        await games.hilo_play(update, context, data.split(":", 1)[1])
        return

    # ── Color Prediction ──
    if data == "game:color":
        await games.color_menu(update, context)
        return
    if data.startswith("color_bet:"):
        await games.color_choose(update, context, int(data.split(":", 1)[1]))
        return
    if data.startswith("color_pick:"):
        await games.color_play(update, context, data.split(":", 1)[1])
        return

    # ── Lucky Wheel ──
    if data == "game:wheel":
        await games.wheel_menu(update, context)
        return
    if data.startswith("wheel_bet:"):
        await games.wheel_play(update, context, int(data.split(":", 1)[1]))
        return

    # ── Word Scramble ──
    if data == "game:word":
        await games.word_start(update, context)
        return

    # ── Emoji Quiz ──
    if data == "game:emoji":
        await games.emoji_start(update, context)
        return
    if data.startswith("emoji_ans:"):
        await games.emoji_answer(update, context, int(data.split(":", 1)[1]))
        return

    # ── Aviator Crash ──
    if data == "game:aviator":
        await games.aviator_menu(update, context)
        return
    if data.startswith("av_bet:"):
        await games.aviator_choose_target(update, context, int(data.split(":", 1)[1]))
        return
    if data.startswith("av_target:"):
        await games.aviator_play(update, context, float(data.split(":", 1)[1]))
        return

    # Fallback
    await query.answer("Unknown action", show_alert=True)


# ─────────────────────────────────────────────────────────────────────────────
# Free-text router (for Number Guess + Redeem UPI input)
# ─────────────────────────────────────────────────────────────────────────────

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_subscribed(update, context):
        return

    # Number-guess game uses text input
    if await games.guess_handle_text(update, context):
        return

    # Word Scramble uses text input
    if await games.word_handle_text(update, context):
        return

    # Redeem flow
    if context.user_data.get("awaiting_upi"):
        upi = (update.message.text or "").strip()
        if "@" not in upi or len(upi) < 5:
            await update.message.reply_text("❌ UPI ID galat lagti hai. Phir bhejo.")
            return
        u = db.get_user(update.effective_user.id)
        if not u or u["coins"] < MIN_REDEEM_COINS:
            await update.message.reply_text("❌ Coins kam ho gaye.")
            context.user_data.pop("awaiting_upi", None)
            return
        coins = u["coins"]
        if not db.deduct_coins(update.effective_user.id, coins):
            await update.message.reply_text("❌ Deduct fail.")
            return
        rid = db.create_redemption(update.effective_user.id, coins, upi)
        context.user_data.pop("awaiting_upi", None)
        inr = round(coins * COIN_TO_INR, 2)
        await update.message.reply_text(
            f"✅ Request #{rid} submit ho gayi!\n"
            f"Coins: {coins}\n"
            f"UPI: {upi}\n"
            f"Approx: ₹{inr}\n\n"
            "Admin 24-48 hours mein process karega.",
        )
        # Notify admin
        if ADMIN_ID:
            try:
                user = update.effective_user
                await context.bot.send_message(
                    ADMIN_ID,
                    f"💸 New redemption #{rid}\n"
                    f"User: {user.first_name} (@{user.username}) [{user.id}]\n"
                    f"Coins: {coins}\n"
                    f"UPI: {upi}\n"
                    f"Approx: ₹{inr}",
                )
            except Exception as e:
                logger.warning("admin notify failed: %s", e)
        return

    # Otherwise show menu hint — only in private chats (avoid group spam)
    if update.effective_chat and update.effective_chat.type == "private":
        await update.message.reply_text("👋 /start dabake game khelo!")


# ─────────────────────────────────────────────────────────────────────────────
# Error handler
# ─────────────────────────────────────────────────────────────────────────────

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update: %s", context.error, exc_info=context.error)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # Start a tiny HTTP healthcheck server in a background thread so that
    # platforms that require an open port (e.g., Render free Web Service tier)
    # see this as a healthy service. Telegram polling continues in the main
    # thread.
    _start_health_server()

    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    # Aliases — better UX in groups where users may type any of these
    app.add_handler(CommandHandler("play", cmd_start))
    app.add_handler(CommandHandler("games", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_start))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_error_handler(on_error)

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


# ─────────────────────────────────────────────────────────────────────────────
# Tiny HTTP healthcheck (only used by hosting providers that require a port)
# ─────────────────────────────────────────────────────────────────────────────

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - Mini Games Bot is alive")

    def log_message(self, *args, **kwargs):  # silence default access logs
        return


def _start_health_server() -> None:
    port_env = os.environ.get("PORT")
    if not port_env:
        # No PORT env var → we're running locally, skip health server.
        logger.info("PORT not set; skipping healthcheck server")
        return
    try:
        port = int(port_env)
    except ValueError:
        logger.warning("Invalid PORT=%s; skipping healthcheck server", port_env)
        return

    def _serve() -> None:
        try:
            server = HTTPServer(("0.0.0.0", port), _HealthHandler)
            logger.info("Healthcheck HTTP server listening on :%s", port)
            server.serve_forever()
        except Exception as exc:  # pragma: no cover
            logger.warning("Healthcheck server stopped: %s", exc)

    t = threading.Thread(target=_serve, name="healthcheck", daemon=True)
    t.start()


if __name__ == "__main__":
    main()
