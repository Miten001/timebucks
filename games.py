"""Mini game logic for the Telegram bot.

Each game uses `context.user_data` to hold per-user state.
All games return coin rewards through database.add_coins / deduct_coins.
"""
from __future__ import annotations

import random
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import database as db
from config import COINS_PER_CORRECT, QUESTIONS_PER_GAME
from questions import CATEGORIES, get_random_questions

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """Quick keyboard builder. Each row: list of (text, callback_data)."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t, callback_data=c) for t, c in row] for row in rows]
    )


async def edit_or_send(update: Update, text: str, reply_markup=None):
    """Edit callback message if present, else reply."""
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="HTML"
            )
            return
        except Exception:
            pass
    target = update.effective_message
    if target:
        await target.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────────────────
# 1) QUIZ GAME
# ─────────────────────────────────────────────────────────────────────────────

async def quiz_pick_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [[(c, f"quiz_cat:{c}")] for c in CATEGORIES]
    rows.append([("⬅️ Back", "menu:main")])
    await edit_or_send(
        update,
        "🧠 <b>Quiz Game</b>\nCategory chuno:",
        reply_markup=kb(rows),
    )


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    questions = get_random_questions(category, QUESTIONS_PER_GAME)
    if not questions:
        await edit_or_send(update, "❌ Iss category mein questions nahi hain.")
        return
    context.user_data["quiz"] = {
        "category": category,
        "questions": questions,
        "index": 0,
        "correct": 0,
    }
    await quiz_send_question(update, context)


async def quiz_send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("quiz")
    if not state:
        await edit_or_send(update, "Quiz state khatam ho gaya. /start dabao.")
        return

    idx = state["index"]
    q_text, options, _ = state["questions"][idx]
    rows = [[(opt, f"quiz_ans:{i}")] for i, opt in enumerate(options)]
    text = (
        f"🧠 <b>Quiz - {state['category']}</b>\n"
        f"Question {idx + 1}/{len(state['questions'])}\n\n"
        f"<b>{q_text}</b>"
    )
    await edit_or_send(update, text, reply_markup=kb(rows))


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: int):
    state = context.user_data.get("quiz")
    if not state:
        await edit_or_send(update, "Quiz over ho gaya. /start dabao.")
        return
    idx = state["index"]
    _, options, correct_idx = state["questions"][idx]
    is_correct = choice == correct_idx
    if is_correct:
        state["correct"] += 1

    feedback = "✅ Sahi!" if is_correct else f"❌ Galat! Sahi answer: <b>{options[correct_idx]}</b>"
    state["index"] += 1

    if state["index"] >= len(state["questions"]):
        # Game over
        correct = state["correct"]
        total = len(state["questions"])
        reward = correct * COINS_PER_CORRECT
        balance = db.add_coins(update.effective_user.id, reward)
        db.increment_stats(update.effective_user.id, correct=correct, played=1)
        context.user_data.pop("quiz", None)
        text = (
            f"{feedback}\n\n"
            f"🎉 <b>Quiz Complete!</b>\n"
            f"Score: {correct}/{total}\n"
            f"💰 Coins earned: <b>+{reward}</b>\n"
            f"💳 Balance: <b>{balance}</b>"
        )
        await edit_or_send(
            update,
            text,
            reply_markup=kb([
                [("🔁 Play Again", "game:quiz"), ("🏠 Menu", "menu:main")],
            ]),
        )
    else:
        # Next question
        await edit_or_send(update, feedback)
        await quiz_send_question(update, context)


# ─────────────────────────────────────────────────────────────────────────────
# 2) NUMBER GUESS
# ─────────────────────────────────────────────────────────────────────────────

GUESS_MAX_TRIES = 7
GUESS_REWARD_BY_TRIES = {1: 200, 2: 100, 3: 60, 4: 40, 5: 25, 6: 15, 7: 10}


async def guess_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    secret = random.randint(1, 100)
    context.user_data["guess"] = {"secret": secret, "tries": 0}
    text = (
        "🎯 <b>Number Guess</b>\n\n"
        "Maine 1-100 ke beech ek number socha hai.\n"
        f"Aapke paas <b>{GUESS_MAX_TRIES} tries</b> hain.\n\n"
        "Reward: <b>1st try = 200 💰</b>, then less each try.\n\n"
        "Number type karke send karo (e.g., 50)"
    )
    await edit_or_send(update, text, reply_markup=kb([[("❌ Cancel", "menu:main")]]))


async def guess_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if message was handled by this game."""
    state = context.user_data.get("guess")
    if not state:
        return False
    text = (update.message.text or "").strip()
    if not text.isdigit():
        await update.message.reply_text("Sirf number bhejo (1-100).")
        return True
    n = int(text)
    if not 1 <= n <= 100:
        await update.message.reply_text("1 se 100 ke beech bhejo.")
        return True

    state["tries"] += 1
    secret = state["secret"]

    if n == secret:
        reward = GUESS_REWARD_BY_TRIES.get(state["tries"], 5)
        balance = db.add_coins(update.effective_user.id, reward)
        db.increment_stats(update.effective_user.id, correct=1, played=1)
        context.user_data.pop("guess", None)
        await update.message.reply_text(
            f"🎉 <b>JEET GAYE!</b>\n"
            f"Number tha: <b>{secret}</b>\n"
            f"Tries: <b>{state['tries']}/{GUESS_MAX_TRIES}</b>\n"
            f"💰 Reward: <b>+{reward}</b>\n"
            f"💳 Balance: <b>{balance}</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [("🔁 Play Again", "game:guess"), ("🏠 Menu", "menu:main")],
            ]),
        )
        return True

    if state["tries"] >= GUESS_MAX_TRIES:
        db.increment_stats(update.effective_user.id, correct=0, played=1)
        context.user_data.pop("guess", None)
        await update.message.reply_text(
            f"😔 Tries khatam!\nNumber tha: <b>{secret}</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [("🔁 Try Again", "game:guess"), ("🏠 Menu", "menu:main")],
            ]),
        )
        return True

    hint = "🔼 Bada socho" if n < secret else "🔽 Chhota socho"
    left = GUESS_MAX_TRIES - state["tries"]
    await update.message.reply_text(
        f"{hint}\nTries left: <b>{left}</b>",
        parse_mode="HTML",
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 3) ROCK PAPER SCISSORS (Best of 3)
# ─────────────────────────────────────────────────────────────────────────────

RPS_EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


async def rps_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rps"] = {"u": 0, "b": 0, "round": 1}
    await rps_show(update, context, "🪨📄✂️ <b>Rock Paper Scissors</b>\nBest of 3. Choose:")


async def rps_show(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix: str):
    state = context.user_data.get("rps", {"u": 0, "b": 0, "round": 1})
    text = (
        f"{prefix}\n\n"
        f"Round: <b>{state['round']}/3</b>\n"
        f"You: <b>{state['u']}</b>  |  Bot: <b>{state['b']}</b>"
    )
    await edit_or_send(
        update,
        text,
        reply_markup=kb([
            [("🪨 Rock", "rps:rock"), ("📄 Paper", "rps:paper"), ("✂️ Scissors", "rps:scissors")],
            [("🏠 Quit", "menu:main")],
        ]),
    )


async def rps_play(update: Update, context: ContextTypes.DEFAULT_TYPE, user_choice: str):
    state = context.user_data.get("rps")
    if not state:
        await rps_start(update, context)
        return

    bot_choice = random.choice(list(RPS_EMOJI.keys()))
    if user_choice == bot_choice:
        result = "🤝 Draw"
    elif RPS_BEATS[user_choice] == bot_choice:
        state["u"] += 1
        result = "✅ You win this round!"
    else:
        state["b"] += 1
        result = "❌ Bot wins this round"

    state["round"] += 1
    prefix = (
        f"You played {RPS_EMOJI[user_choice]}  vs  Bot {RPS_EMOJI[bot_choice]}\n"
        f"{result}\n"
    )

    # Check if match over
    if state["u"] == 2 or state["b"] == 2 or state["round"] > 3:
        if state["u"] > state["b"]:
            reward = 30
            balance = db.add_coins(update.effective_user.id, reward)
            verdict = f"🏆 <b>You won the match!</b>\n💰 +{reward}\n💳 Balance: <b>{balance}</b>"
        elif state["b"] > state["u"]:
            verdict = "💀 Bot won the match. Better luck next time!"
        else:
            verdict = "🤝 Match drawn."
        db.increment_stats(update.effective_user.id, correct=int(state["u"] > state["b"]), played=1)
        context.user_data.pop("rps", None)
        await edit_or_send(
            update,
            f"{prefix}\nFinal: You {state['u']} - {state['b']} Bot\n\n{verdict}",
            reply_markup=kb([
                [("🔁 Play Again", "game:rps"), ("🏠 Menu", "menu:main")],
            ]),
        )
    else:
        await rps_show(update, context, prefix)


# ─────────────────────────────────────────────────────────────────────────────
# 4) COIN FLIP (bet coins)
# ─────────────────────────────────────────────────────────────────────────────

COIN_FLIP_BETS = [10, 50, 100, 500]


async def coinflip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🪙 <b>Coin Flip</b>\n\n"
        "Apna bet aur side choose karo.\n"
        "Win = 2x coins, Lose = bet gone.\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>"
    )
    rows = [[(f"💰 Bet {b}", f"cf_bet:{b}")] for b in COIN_FLIP_BETS]
    rows.append([("🏠 Back", "menu:main")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def coinflip_choose_side(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user = db.get_user(update.effective_user.id)
    if not user or user["coins"] < bet:
        await edit_or_send(
            update,
            f"❌ Insufficient coins. Need {bet}, have {user['coins'] if user else 0}.",
            reply_markup=kb([[("🏠 Menu", "menu:main")]]),
        )
        return
    context.user_data["cf_bet"] = bet
    await edit_or_send(
        update,
        f"Bet: <b>{bet}</b>\n\nChoose side:",
        reply_markup=kb([
            [("👑 Heads", "cf_side:heads"), ("🪙 Tails", "cf_side:tails")],
            [("⬅️ Back", "game:coinflip")],
        ]),
    )


async def coinflip_play(update: Update, context: ContextTypes.DEFAULT_TYPE, side: str):
    bet = context.user_data.get("cf_bet")
    if not bet:
        await coinflip_menu(update, context)
        return
    if not db.deduct_coins(update.effective_user.id, bet):
        await edit_or_send(update, "❌ Coins kam ho gaye. Game cancel.")
        return

    flip = random.choice(["heads", "tails"])
    won = flip == side
    if won:
        reward = bet * 2
        balance = db.add_coins(update.effective_user.id, reward)
        verdict = f"🎉 <b>WIN!</b> Coin: {flip.upper()}\n💰 +{reward}"
    else:
        balance = db.get_user(update.effective_user.id)["coins"]
        verdict = f"😔 Lost. Coin: {flip.upper()}\n💸 -{bet}"

    db.increment_stats(update.effective_user.id, correct=int(won), played=1)
    context.user_data.pop("cf_bet", None)
    await edit_or_send(
        update,
        f"🪙 Coin Flip Result\n\n{verdict}\n💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Again", "game:coinflip"), ("🏠 Menu", "menu:main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5) DICE ROLL (vs bot)
# ─────────────────────────────────────────────────────────────────────────────

DICE_BETS = [10, 50, 100]


async def dice_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🎲 <b>Dice Roll Battle</b>\n\n"
        "Tum aur bot ek-ek dice roll karoge.\n"
        "Higher number = winner. Tie = bet returned.\n"
        "Win = 2x bet.\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>"
    )
    rows = [[(f"🎲 Roll for {b}", f"dice_bet:{b}")] for b in DICE_BETS]
    rows.append([("🏠 Back", "menu:main")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def dice_play(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user = db.get_user(update.effective_user.id)
    if not user or user["coins"] < bet:
        await edit_or_send(update, "❌ Insufficient coins.")
        return
    if not db.deduct_coins(update.effective_user.id, bet):
        await edit_or_send(update, "❌ Coin deduct fail.")
        return

    user_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    if user_roll > bot_roll:
        reward = bet * 2
        balance = db.add_coins(update.effective_user.id, reward)
        verdict = f"🏆 <b>You win!</b>\n💰 +{reward}"
        won = True
    elif user_roll < bot_roll:
        balance = db.get_user(update.effective_user.id)["coins"]
        verdict = f"😔 Bot wins.\n💸 -{bet}"
        won = False
    else:
        # refund
        balance = db.add_coins(update.effective_user.id, bet)
        verdict = f"🤝 Tie. Bet returned."
        won = False

    db.increment_stats(update.effective_user.id, correct=int(won), played=1)
    await edit_or_send(
        update,
        f"🎲 Dice Roll\n\n"
        f"You: 🎲 <b>{user_roll}</b>   vs   Bot: 🎲 <b>{bot_roll}</b>\n"
        f"{verdict}\n"
        f"💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Again", "game:dice"), ("🏠 Menu", "menu:main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6) MATH QUICK (5 quick math questions)
# ─────────────────────────────────────────────────────────────────────────────

def _make_math_q() -> tuple[str, int]:
    a = random.randint(2, 25)
    b = random.randint(2, 25)
    op = random.choice(["+", "-", "*"])
    if op == "+":
        return f"{a} + {b}", a + b
    if op == "-":
        # ensure non-negative
        if a < b:
            a, b = b, a
        return f"{a} - {b}", a - b
    return f"{a} × {b}", a * b


async def math_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qs = [_make_math_q() for _ in range(5)]
    context.user_data["math"] = {"qs": qs, "i": 0, "correct": 0}
    await math_send(update, context)


async def math_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("math")
    if not state:
        return
    i = state["i"]
    q, ans = state["qs"][i]
    # Build 4 options around correct
    options = {ans}
    while len(options) < 4:
        options.add(ans + random.choice([-3, -2, -1, 1, 2, 3, 5, -5]))
    opts = list(options)
    random.shuffle(opts)
    correct_idx = opts.index(ans)
    state["correct_idx"] = correct_idx
    rows = [[(str(o), f"math_ans:{idx}")] for idx, o in enumerate(opts)]
    rows.append([("🏠 Quit", "menu:main")])
    await edit_or_send(
        update,
        f"➗ <b>Math Quick</b>\n"
        f"Question {i + 1}/5\n\n"
        f"<b>{q} = ?</b>",
        reply_markup=kb(rows),
    )


async def math_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: int):
    state = context.user_data.get("math")
    if not state:
        await edit_or_send(update, "Game khatam.")
        return
    is_correct = choice == state["correct_idx"]
    if is_correct:
        state["correct"] += 1
    state["i"] += 1
    feedback = "✅ Sahi!" if is_correct else "❌ Galat!"

    if state["i"] >= len(state["qs"]):
        correct = state["correct"]
        reward = correct * COINS_PER_CORRECT
        balance = db.add_coins(update.effective_user.id, reward)
        db.increment_stats(update.effective_user.id, correct=correct, played=1)
        context.user_data.pop("math", None)
        await edit_or_send(
            update,
            f"{feedback}\n\n"
            f"🎉 <b>Math Complete!</b>\n"
            f"Score: {correct}/5\n"
            f"💰 +{reward}\n"
            f"💳 Balance: <b>{balance}</b>",
            reply_markup=kb([
                [("🔁 Again", "game:math"), ("🏠 Menu", "menu:main")],
            ]),
        )
    else:
        await edit_or_send(update, feedback)
        await math_send(update, context)
