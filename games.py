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


async def alert_no_state(
    update: Update,
    msg: str = "❌ Ye game khatam ho gaya, ya kisi aur user ne start kiya tha.\n👉 /start dabake apna khud ka game shuru karo!",
) -> None:
    """Show a popup alert without editing the original message.

    Group-friendly: when User B clicks User A's inline button, B's
    `context.user_data` is empty for that game. Instead of overwriting
    A's quiz message with a "state khatam" error, we show a private
    popup to B and leave A's game intact.
    """
    if update.callback_query:
        try:
            await update.callback_query.answer(msg, show_alert=True)
            return
        except Exception:
            pass
    if update.effective_message:
        try:
            await update.effective_message.reply_text(msg)
        except Exception:
            pass


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
        await alert_no_state(update)
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
        await alert_no_state(update)
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
        await alert_no_state(update)
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
        await alert_no_state(update)
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
        await alert_no_state(update)
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



# ─────────────────────────────────────────────────────────────────────────────
# 7) SLOT MACHINE 🎰  (bet)
# ─────────────────────────────────────────────────────────────────────────────

SLOT_SYMBOLS = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
SLOT_BETS = [10, 50, 100]


async def slot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🎰 <b>Slot Machine</b>\n\n"
        "3 same symbols = win!\n"
        "  7️⃣7️⃣7️⃣  = <b>50x</b> JACKPOT\n"
        "  💎💎💎  = <b>20x</b>\n"
        "  Other 3-match = <b>10x</b>\n"
        "  Any 2-match  = <b>1x</b> (bet returned)\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>"
    )
    rows = [[(f"🎰 Spin for {b}", f"slot_bet:{b}")] for b in SLOT_BETS]
    rows.append([("🏠 Back", "menu:betting")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def slot_play(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user or user["coins"] < bet:
        await edit_or_send(update, "❌ Insufficient coins.")
        return
    if not db.deduct_coins(user_id, bet):
        await edit_or_send(update, "❌ Coin deduct fail.")
        return

    reels = [random.choice(SLOT_SYMBOLS) for _ in range(3)]

    if reels[0] == reels[1] == reels[2]:
        if reels[0] == "7️⃣":
            mult, label = 50, "🎉 JACKPOT!"
        elif reels[0] == "💎":
            mult, label = 20, "💎 Diamond Triple!"
        else:
            mult, label = 10, "🎊 Triple match!"
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        mult, label = 1, "🟡 2-match (bet returned)"
    else:
        mult, label = 0, "💔 No match"

    payout = bet * mult
    if payout > 0:
        balance = db.add_coins(user_id, payout)
        verdict = f"{label}\n💰 +{payout} (x{mult})"
    else:
        balance = db.get_user(user_id)["coins"]
        verdict = f"{label}\n💸 -{bet}"

    db.increment_stats(user_id, correct=int(mult > 1), played=1)
    await edit_or_send(
        update,
        f"🎰 SPIN\n\n"
        f"┃ {reels[0]} ┃ {reels[1]} ┃ {reels[2]} ┃\n\n"
        f"{verdict}\n"
        f"💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Spin Again", "game:slot"), ("🏠 Menu", "menu:main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8) TIC TAC TOE ⭕❌  (vs bot AI)
# ─────────────────────────────────────────────────────────────────────────────

TTT_WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),             # diagonals
]
TTT_REWARD_WIN = 25
TTT_REWARD_DRAW = 5


def _ttt_check_winner(board: list) -> Optional[str]:
    for a, b, c in TTT_WIN_LINES:
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a]
    return None


def _ttt_bot_move(board: list) -> int:
    """Smart-ish bot: win > block > center > corner > side."""
    # 1. Try to win
    for i in range(9):
        if board[i] is None:
            board[i] = "O"
            if _ttt_check_winner(board) == "O":
                board[i] = None
                return i
            board[i] = None
    # 2. Try to block
    for i in range(9):
        if board[i] is None:
            board[i] = "X"
            if _ttt_check_winner(board) == "X":
                board[i] = None
                return i
            board[i] = None
    # 3. Center
    if board[4] is None:
        return 4
    # 4. Corners
    corners = [i for i in (0, 2, 6, 8) if board[i] is None]
    if corners:
        return random.choice(corners)
    # 5. Sides
    sides = [i for i in (1, 3, 5, 7) if board[i] is None]
    if sides:
        return random.choice(sides)
    return -1


def _ttt_render_kb(board: list) -> InlineKeyboardMarkup:
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            label = board[i] if board[i] else "·"
            # Empty cells use callback "ttt:i"; filled cells are no-op
            cb = f"ttt:{i}" if board[i] is None else "ttt:noop"
            row.append((label, cb))
        rows.append(row)
    rows.append([("🏠 Quit", "menu:main")])
    return kb(rows)


async def ttt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ttt"] = {"board": [None] * 9}
    await edit_or_send(
        update,
        "⭕❌ <b>Tic Tac Toe</b>\nYou: <b>X</b>  |  Bot: <b>O</b>\n\nApna move chuno:",
        reply_markup=_ttt_render_kb(context.user_data["ttt"]["board"]),
    )


async def ttt_play(update: Update, context: ContextTypes.DEFAULT_TYPE, cell: int):
    state = context.user_data.get("ttt")
    if not state:
        await alert_no_state(update)
        return
    board = state["board"]
    if board[cell] is not None:
        return  # ignore clicks on filled cells

    # User move
    board[cell] = "X"
    winner = _ttt_check_winner(board)
    if winner is None and any(b is None for b in board):
        # Bot move
        bot_idx = _ttt_bot_move(board)
        if bot_idx >= 0:
            board[bot_idx] = "O"
        winner = _ttt_check_winner(board)

    is_draw = winner is None and all(b is not None for b in board)

    if winner or is_draw:
        user_id = update.effective_user.id
        if winner == "X":
            balance = db.add_coins(user_id, TTT_REWARD_WIN)
            verdict = f"🏆 You won!\n💰 +{TTT_REWARD_WIN}\n💳 <b>{balance}</b>"
            won = True
        elif winner == "O":
            balance = db.get_user(user_id)["coins"]
            verdict = f"😔 Bot won!\n💳 <b>{balance}</b>"
            won = False
        else:
            balance = db.add_coins(user_id, TTT_REWARD_DRAW)
            verdict = f"🤝 Draw!\n💰 +{TTT_REWARD_DRAW}\n💳 <b>{balance}</b>"
            won = False
        db.increment_stats(user_id, correct=int(won), played=1)
        context.user_data.pop("ttt", None)
        await edit_or_send(
            update,
            f"⭕❌ Game over\n\n{verdict}",
            reply_markup=kb([
                [("🔁 Play Again", "game:ttt"), ("🏠 Menu", "menu:main")],
            ]),
        )
    else:
        await edit_or_send(
            update,
            "⭕❌ <b>Tic Tac Toe</b>\nYou: <b>X</b>  |  Bot: <b>O</b>",
            reply_markup=_ttt_render_kb(board),
        )


# ─────────────────────────────────────────────────────────────────────────────
# 9) HI-LO CARDS 🃏  (bet)
# ─────────────────────────────────────────────────────────────────────────────

HILO_BETS = [10, 50, 100]
CARD_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}


def _card_label(n: int) -> str:
    return CARD_NAMES.get(n, str(n))


async def hilo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🃏 <b>Hi-Lo Cards</b>\n\n"
        "Card 1-13. Predict next card.\n"
        "Higher / Lower = <b>2x</b> bet.\n"
        "Same number = lose.\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>"
    )
    rows = [[(f"🃏 Play for {b}", f"hilo_bet:{b}")] for b in HILO_BETS]
    rows.append([("🏠 Back", "menu:betting")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def hilo_choose_dir(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user = db.get_user(update.effective_user.id)
    if not user or user["coins"] < bet:
        await edit_or_send(update, "❌ Insufficient coins.")
        return
    card = random.randint(1, 13)
    context.user_data["hilo"] = {"bet": bet, "card": card}
    await edit_or_send(
        update,
        f"🃏 Current card: <b>[ {_card_label(card)} ]</b>\n\n"
        f"Bet: <b>{bet}</b>\n\nNext card hogi?",
        reply_markup=kb([
            [("🔼 Higher", "hilo_dir:high"), ("🔽 Lower", "hilo_dir:low")],
            [("⬅️ Cancel", "game:hilo")],
        ]),
    )


async def hilo_play(update: Update, context: ContextTypes.DEFAULT_TYPE, direction: str):
    state = context.user_data.get("hilo")
    if not state:
        await alert_no_state(update)
        return
    bet = state["bet"]
    current = state["card"]
    user_id = update.effective_user.id
    if not db.deduct_coins(user_id, bet):
        await edit_or_send(update, "❌ Coin deduct fail.")
        return

    next_card = random.randint(1, 13)
    if next_card == current:
        won = False
        outcome = "🟰 Same number — you lose!"
    elif (direction == "high" and next_card > current) or (
        direction == "low" and next_card < current
    ):
        won = True
        outcome = "✅ Correct!"
    else:
        won = False
        outcome = "❌ Wrong!"

    if won:
        balance = db.add_coins(user_id, bet * 2)
        verdict = f"💰 +{bet * 2}"
    else:
        balance = db.get_user(user_id)["coins"]
        verdict = f"💸 -{bet}"

    db.increment_stats(user_id, correct=int(won), played=1)
    context.user_data.pop("hilo", None)
    await edit_or_send(
        update,
        f"🃏 You had: <b>[ {_card_label(current)} ]</b>\n"
        f"Next: <b>[ {_card_label(next_card)} ]</b>\n\n"
        f"{outcome}\n{verdict}\n💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Again", "game:hilo"), ("🏠 Menu", "menu:main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10) COLOR PREDICTION 🎨  (bet)
# ─────────────────────────────────────────────────────────────────────────────

COLOR_BETS = [10, 50, 100]
# (key, emoji, label, multiplier, weight)
COLORS = [
    ("red",    "🔴", "Red",    2, 40),
    ("green",  "🟢", "Green",  2, 40),
    ("violet", "🟣", "Violet", 5, 20),
]


def _pick_color() -> str:
    weights = [c[4] for c in COLORS]
    return random.choices([c[0] for c in COLORS], weights=weights, k=1)[0]


async def color_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🎨 <b>Color Prediction</b>\n\n"
        "🔴 Red — <b>2x</b>\n"
        "🟢 Green — <b>2x</b>\n"
        "🟣 Violet — <b>5x</b> (rare)\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>"
    )
    rows = [[(f"🎨 Play for {b}", f"color_bet:{b}")] for b in COLOR_BETS]
    rows.append([("🏠 Back", "menu:betting")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def color_choose(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user = db.get_user(update.effective_user.id)
    if not user or user["coins"] < bet:
        await edit_or_send(update, "❌ Insufficient coins.")
        return
    context.user_data["color_bet"] = bet
    await edit_or_send(
        update,
        f"Bet: <b>{bet}</b>\n\nColor chuno:",
        reply_markup=kb([
            [("🔴 Red 2x", "color_pick:red"), ("🟢 Green 2x", "color_pick:green")],
            [("🟣 Violet 5x", "color_pick:violet")],
            [("⬅️ Back", "game:color")],
        ]),
    )


async def color_play(update: Update, context: ContextTypes.DEFAULT_TYPE, picked: str):
    bet = context.user_data.get("color_bet")
    if not bet:
        await alert_no_state(update)
        return
    user_id = update.effective_user.id
    if not db.deduct_coins(user_id, bet):
        await edit_or_send(update, "❌ Coin deduct fail.")
        return

    result = _pick_color()
    chosen = next(c for c in COLORS if c[0] == picked)
    actual = next(c for c in COLORS if c[0] == result)
    won = result == picked

    if won:
        payout = bet * chosen[3]
        balance = db.add_coins(user_id, payout)
        verdict = f"🎉 You picked {chosen[1]} — Result {actual[1]}\n💰 +{payout}"
    else:
        balance = db.get_user(user_id)["coins"]
        verdict = f"😔 You picked {chosen[1]} — Result {actual[1]}\n💸 -{bet}"

    db.increment_stats(user_id, correct=int(won), played=1)
    context.user_data.pop("color_bet", None)
    await edit_or_send(
        update,
        f"🎨 Color Prediction\n\n{verdict}\n💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Again", "game:color"), ("🏠 Menu", "menu:main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 11) LUCKY WHEEL 🎡  (bet)
# ─────────────────────────────────────────────────────────────────────────────

WHEEL_BETS = [10, 50, 100]
# (multiplier, weight, emoji label)
WHEEL_SEGMENTS = [
    (0,   40, "💔 Lose"),
    (1,   30, "🟡 Return"),
    (2,   20, "🟢 2x"),
    (5,    7, "🔵 5x"),
    (10, 2.5, "🟣 10x"),
    (20, 0.5, "🌟 20x"),
]


async def wheel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🎡 <b>Lucky Wheel</b>\n\n"
        "Spin and win!\n"
        "  💔 Lose (40%)\n"
        "  🟡 Return bet (30%)\n"
        "  🟢 2x (20%)\n"
        "  🔵 5x (7%)\n"
        "  🟣 10x (2.5%)\n"
        "  🌟 20x (0.5%) JACKPOT\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>"
    )
    rows = [[(f"🎡 Spin for {b}", f"wheel_bet:{b}")] for b in WHEEL_BETS]
    rows.append([("🏠 Back", "menu:betting")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def wheel_play(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user or user["coins"] < bet:
        await edit_or_send(update, "❌ Insufficient coins.")
        return
    if not db.deduct_coins(user_id, bet):
        await edit_or_send(update, "❌ Coin deduct fail.")
        return

    weights = [s[1] for s in WHEEL_SEGMENTS]
    seg = random.choices(WHEEL_SEGMENTS, weights=weights, k=1)[0]
    mult, _, label = seg
    payout = bet * mult
    if payout > 0:
        balance = db.add_coins(user_id, payout)
        verdict = f"{label}\n💰 +{payout}"
    else:
        balance = db.get_user(user_id)["coins"]
        verdict = f"{label}\n💸 -{bet}"

    db.increment_stats(user_id, correct=int(mult >= 2), played=1)
    await edit_or_send(
        update,
        f"🎡 Wheel spinning... ✨\n\n"
        f"Landed on: <b>{label}</b>\n"
        f"{verdict}\n"
        f"💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Spin Again", "game:wheel"), ("🏠 Menu", "menu:main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 12) WORD SCRAMBLE 🔤  (free, text input)
# ─────────────────────────────────────────────────────────────────────────────

WORDS = [
    ("PYTHON", "Programming language / saap"),
    ("INDIA", "Hamara desh"),
    ("CRICKET", "Most-loved sport"),
    ("BOLLYWOOD", "Hindi film industry"),
    ("MUMBAI", "City of dreams"),
    ("DELHI", "Bharat ki rajdhani"),
    ("INTERNET", "Worldwide connection"),
    ("ELEPHANT", "Bada jaanwar"),
    ("BANANA", "Yellow fruit"),
    ("MANGO", "King of fruits"),
    ("APPLE", "iPhone banane wali company / fruit"),
    ("GUITAR", "Stringed instrument"),
    ("CAMERA", "Photo lene wala device"),
    ("MOBILE", "Phone"),
    ("LAPTOP", "Portable computer"),
    ("ENGINEER", "Tech professional"),
    ("DOCTOR", "Treats patients"),
    ("TEACHER", "Padhata hai"),
    ("CHENNAI", "South Indian metro"),
    ("KOLKATA", "City of joy"),
    ("FRIEND", "Yaar / dost"),
    ("FAMILY", "Parivaar"),
    ("RAILWAY", "Train system"),
    ("DIWALI", "Festival of lights"),
    ("CHAPATI", "Roti"),
]
WORD_REWARD = 30
WORD_MAX_TRIES = 2


def _scramble(word: str) -> str:
    letters = list(word)
    while True:
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word:
            return scrambled


async def word_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word, hint = random.choice(WORDS)
    context.user_data["word"] = {
        "word": word,
        "hint": hint,
        "tries": 0,
    }
    await edit_or_send(
        update,
        f"🔤 <b>Word Scramble</b>\n\n"
        f"Letters: <b>{_scramble(word)}</b>\n"
        f"Hint: <i>{hint}</i>\n\n"
        f"Tries: <b>{WORD_MAX_TRIES}</b>\nReward: <b>{WORD_REWARD} coins</b>\n\n"
        "Type the word in chat 👇",
        reply_markup=kb([[("❌ Skip", "menu:main")]]),
    )


async def word_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = context.user_data.get("word")
    if not state:
        return False
    guess = (update.message.text or "").strip().upper()
    if not guess.isalpha():
        await update.message.reply_text("Sirf letters bhejo (no spaces/numbers).")
        return True

    state["tries"] += 1
    if guess == state["word"]:
        balance = db.add_coins(update.effective_user.id, WORD_REWARD)
        db.increment_stats(update.effective_user.id, correct=1, played=1)
        context.user_data.pop("word", None)
        await update.message.reply_text(
            f"✅ Correct! Word was <b>{state['word']}</b>\n"
            f"💰 +{WORD_REWARD}\n💳 Balance: <b>{balance}</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [("🔁 Next Word", "game:word"), ("🏠 Menu", "menu:main")],
            ]),
        )
        return True

    if state["tries"] >= WORD_MAX_TRIES:
        db.increment_stats(update.effective_user.id, correct=0, played=1)
        context.user_data.pop("word", None)
        await update.message.reply_text(
            f"❌ Out of tries! Word was <b>{state['word']}</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [("🔁 Try Another", "game:word"), ("🏠 Menu", "menu:main")],
            ]),
        )
        return True

    left = WORD_MAX_TRIES - state["tries"]
    await update.message.reply_text(
        f"❌ Galat. Tries left: <b>{left}</b>",
        parse_mode="HTML",
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 13) EMOJI QUIZ 🎬  (free)
# ─────────────────────────────────────────────────────────────────────────────

EMOJI_PUZZLES = [
    ("👨‍🎓📚",      ["Student", "Teacher", "Pilot", "Doctor"], 0),
    ("🐍💻",        ["Java", "Python", "C++", "Go"], 1),
    ("🏏🏆",        ["Hockey", "Football", "Cricket", "Tennis"], 2),
    ("🍕🇮🇹",      ["Pasta", "Burger", "Pizza", "Sushi"], 2),
    ("🌧️☂️",       ["Sun", "Rain", "Snow", "Wind"], 1),
    ("👫💍",        ["Wedding", "Party", "Birthday", "Concert"], 0),
    ("🐘🇮🇳",      ["Tiger", "Lion", "Elephant", "Cow"], 2),
    ("🚂🌍",        ["Cycling", "Walking", "Travel", "Cooking"], 2),
    ("🦁👑",        ["Tiger King", "Lion King", "Jungle Book", "Madagascar"], 1),
    ("🧒🎂",        ["Wedding", "Birthday", "Anniversary", "Funeral"], 1),
    ("🍔🍟",        ["KFC", "Subway", "McDonald's", "Pizza Hut"], 2),
    ("🌅🏖️",       ["Mountain", "Beach", "Desert", "Forest"], 1),
    ("👨‍🍳🍳",      ["Chef", "Doctor", "Painter", "Singer"], 0),
    ("⚽🏆",        ["Cricket", "Football", "Basketball", "Hockey"], 1),
    ("🎬⭐",        ["Music", "Movie", "Theater", "Dance"], 1),
    ("📱🍎",        ["Samsung", "iPhone", "OnePlus", "Nokia"], 1),
    ("🚗🏁",        ["Race", "Parking", "Garage", "Tunnel"], 0),
    ("🌙🌟",        ["Day", "Night", "Morning", "Evening"], 1),
    ("👮‍♂️🚓",      ["Doctor", "Teacher", "Police", "Lawyer"], 2),
    ("💊🏥",        ["School", "Office", "Hospital", "Stadium"], 2),
]
EMOJI_QUESTIONS_PER_GAME = 5
EMOJI_REWARD_PER_CORRECT = 25


async def emoji_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    puzzles = random.sample(EMOJI_PUZZLES, min(EMOJI_QUESTIONS_PER_GAME, len(EMOJI_PUZZLES)))
    context.user_data["emoji"] = {"puzzles": puzzles, "i": 0, "correct": 0}
    await emoji_send(update, context)


async def emoji_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("emoji")
    if not state:
        return
    i = state["i"]
    emojis, options, _ = state["puzzles"][i]
    rows = [[(opt, f"emoji_ans:{idx}")] for idx, opt in enumerate(options)]
    rows.append([("🏠 Quit", "menu:main")])
    await edit_or_send(
        update,
        f"🎬 <b>Emoji Quiz</b>\n"
        f"Question {i + 1}/{len(state['puzzles'])}\n\n"
        f"<b>{emojis}</b>\n\nKya hai ye?",
        reply_markup=kb(rows),
    )


async def emoji_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: int):
    state = context.user_data.get("emoji")
    if not state:
        await alert_no_state(update)
        return
    i = state["i"]
    emojis, options, correct_idx = state["puzzles"][i]
    is_correct = choice == correct_idx
    if is_correct:
        state["correct"] += 1
    feedback = (
        "✅ Sahi!" if is_correct
        else f"❌ Galat! Sahi answer: <b>{options[correct_idx]}</b>"
    )
    state["i"] += 1

    if state["i"] >= len(state["puzzles"]):
        correct = state["correct"]
        total = len(state["puzzles"])
        reward = correct * EMOJI_REWARD_PER_CORRECT
        balance = db.add_coins(update.effective_user.id, reward)
        db.increment_stats(update.effective_user.id, correct=correct, played=1)
        context.user_data.pop("emoji", None)
        await edit_or_send(
            update,
            f"{feedback}\n\n"
            f"🎉 <b>Emoji Quiz Complete!</b>\n"
            f"Score: {correct}/{total}\n"
            f"💰 +{reward}\n"
            f"💳 Balance: <b>{balance}</b>",
            reply_markup=kb([
                [("🔁 Again", "game:emoji"), ("🏠 Menu", "menu:main")],
            ]),
        )
    else:
        await edit_or_send(update, feedback)
        await emoji_send(update, context)


# ─────────────────────────────────────────────────────────────────────────────
# 14) AVIATOR CRASH 🚀  (bet, target multiplier)
# ─────────────────────────────────────────────────────────────────────────────

AVIATOR_BETS = [10, 50, 100]
AVIATOR_TARGETS = [1.5, 2.0, 3.0, 5.0, 10.0, 50.0]


def _aviator_crash() -> float:
    """Generate a crash multiplier with ~1% house edge.

    P(crash > x) = 0.99 / x. Capped at 100x for sanity.
    """
    r = random.random()
    if r < 0.01:
        return 1.0  # instant crash, ~1% house edge
    crash = 0.99 / r
    return min(100.0, round(crash, 2))


async def aviator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    text = (
        "🚀 <b>Aviator Crash</b>\n\n"
        "Plane udta hai, multiplier badhta hai...\n"
        "Apna <b>auto cash-out</b> multiplier choose karo BEFORE the flight.\n"
        "Plane crash before target = <b>lose bet</b>\n"
        "Plane survives target = <b>win bet × target</b>\n\n"
        f"💳 Balance: <b>{user['coins'] if user else 0}</b>\n\nFirst, choose bet:"
    )
    rows = [[(f"💰 Bet {b}", f"av_bet:{b}")] for b in AVIATOR_BETS]
    rows.append([("🏠 Back", "menu:betting")])
    await edit_or_send(update, text, reply_markup=kb(rows))


async def aviator_choose_target(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    user = db.get_user(update.effective_user.id)
    if not user or user["coins"] < bet:
        await edit_or_send(update, "❌ Insufficient coins.")
        return
    context.user_data["av_bet"] = bet
    rows = [
        [(f"{t}x  ({int(99 / t)}% chance)", f"av_target:{t}")]
        for t in AVIATOR_TARGETS
    ]
    rows.append([("⬅️ Back", "game:aviator")])
    await edit_or_send(
        update,
        f"Bet: <b>{bet}</b>\n\nAuto cash-out target:",
        reply_markup=kb(rows),
    )


async def aviator_play(update: Update, context: ContextTypes.DEFAULT_TYPE, target: float):
    bet = context.user_data.get("av_bet")
    if not bet:
        await alert_no_state(update)
        return
    user_id = update.effective_user.id
    if not db.deduct_coins(user_id, bet):
        await edit_or_send(update, "❌ Coin deduct fail.")
        return

    crash = _aviator_crash()
    won = crash >= target

    if won:
        payout = int(bet * target)
        balance = db.add_coins(user_id, payout)
        verdict = (
            f"✅ Cashed out at <b>{target}x</b>\n"
            f"Crash was at <b>{crash}x</b>\n"
            f"💰 +{payout}"
        )
    else:
        balance = db.get_user(user_id)["coins"]
        verdict = (
            f"💥 Plane crashed at <b>{crash}x</b>\n"
            f"(target was {target}x)\n"
            f"💸 -{bet}"
        )

    # Build a little flight log
    stops = []
    for m in [1.2, 1.5, 2.0, 3.0, 5.0, 10.0]:
        if crash >= m:
            stops.append(f"  ✈️ {m}x")
        else:
            break
    flight_log = "\n".join(stops) if stops else "  💥 Instant crash"

    db.increment_stats(user_id, correct=int(won), played=1)
    context.user_data.pop("av_bet", None)
    await edit_or_send(
        update,
        f"🚀 <b>Flight Log</b>\n{flight_log}\n\n{verdict}\n💳 Balance: <b>{balance}</b>",
        reply_markup=kb([
            [("🔁 Again", "game:aviator"), ("🏠 Menu", "menu:main")],
        ]),
    )
