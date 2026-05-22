# 🎮 Telegram Mini-Games Bot

A Telegram bot with **14 mini-games**, coin economy, daily bonus, refer & earn, and force-subscribe sponsor channels — your **monetization mechanism**.

## ⚡ ONE-CLICK DEPLOY

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Miten001/timebucks)
[![Run on Replit](https://replit.com/badge/github/Miten001/timebucks)](https://replit.com/new/github/Miten001/timebucks)

After clicking: just paste your `BOT_TOKEN` in environment variables and your bot is live.

## 🕹️ Games Included

### 🎮 Free Games (no bet, pure skill/luck → coins)

| # | Game | How it works | Reward |
|---|------|--------------|--------|
| 1 | 🧠 Quiz | 5 questions across 5 categories (GK, Bollywood, Cricket, Tech, Hindi) | 10 coins per correct |
| 2 | 🎯 Number Guess | Bot picks 1-100, user has 7 tries with hi/lo hints | 10-200 coins (less per try) |
| 3 | 🪨📄✂️ Rock Paper Scissors | Best of 3 vs bot | 30 coins on win |
| 4 | ➗ Math Quick | 5 quick math MCQs | 10 coins per correct |
| 5 | 🔤 Word Scramble | Unscramble word from hint, 2 tries | 30 coins |
| 6 | ⭕❌ Tic Tac Toe | 3x3 grid vs smart-ish bot AI | 25 (win) / 5 (draw) |
| 7 | 🎬 Emoji Quiz | Guess what 5 emoji combos mean | 25 coins per correct |

### 💰 Betting Games (risk coins → bigger payouts)

| # | Game | How it works | Payout |
|---|------|--------------|--------|
| 8 | 🪙 Coin Flip | Bet on heads/tails | 2x bet |
| 9 | 🎲 Dice Battle | User vs bot, higher wins | 2x bet |
| 10 | 🎰 Slot Machine | 3 reels of fruit/jackpot symbols | up to **50x** (7️⃣7️⃣7️⃣) |
| 11 | 🃏 Hi-Lo Cards | Predict if next card is higher / lower | 2x bet |
| 12 | 🎨 Color Prediction | 🔴 Red / 🟢 Green / 🟣 Violet | 2x or 5x |
| 13 | 🎡 Lucky Wheel | Spin a weighted wheel | up to **20x** (jackpot) |
| 14 | 🚀 Aviator Crash | Pick auto cash-out target before flight | up to **50x** target |

## 💰 How You Earn

This bot is built around **force-subscribe sponsor channels**:

1. Other Telegram channels pay you **₹500-₹2000/month** to be in your sponsor list.
2. New users **must join all sponsor channels** before they can play.
3. As your bot grows (1k+ users), more channels will pay to advertise.

Other revenue paths you can add later:
- **Telegram Stars** (premium features)
- **Adsgram / Monetag** (only inside Telegram Mini Apps)
- **Affiliate links** in quiz answers (Amazon, etc.)
- **Sponsored quiz questions**

## 🚀 Quick Setup

### 1. Get a bot token

1. Open Telegram → search **@BotFather**
2. Send `/newbot` and follow prompts
3. Copy the token (looks like `7891234567:AAFxxxxxx...`)

### 2. Get your Telegram ID

Open **@userinfobot** in Telegram and send `/start`.

### 3. Configure

```bash
cp .env.example .env
# Edit .env and fill BOT_TOKEN and ADMIN_ID
```

### 4. Install & Run

```bash
pip install -r requirements.txt
python bot.py
```

The bot will start polling. Open Telegram, search your bot, send `/start`.

## 📦 Deploy Free (Recommended: Render.com)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → New → Background Worker.
3. Connect your repo. Render auto-detects `Procfile` and `requirements.txt`.
4. In **Environment**, add `BOT_TOKEN`, `ADMIN_ID`, `SPONSOR_CHANNELS`.
5. Click **Deploy**.

Other free options:
- **Railway.app** — similar to Render
- **Replit** — simplest, browser-based
- **VPS** (e.g., Oracle free tier) — most control

## 🔧 Add Sponsor Channels

When advertisers want to be promoted on your bot:

1. Make your bot **admin** in their channel (only "Manage messages" needed; or just member-check permission).
2. Add their channel username to `SPONSOR_CHANNELS` in `.env`:
   ```
   SPONSOR_CHANNELS=channel1,channel2,channel3
   ```
3. Restart bot. New users will be forced to join before playing.

## 📁 Project Structure

```
.
├── bot.py            # Main entry: command + callback handlers
├── games.py          # All 6 mini-game logic
├── questions.py      # Quiz question bank (add more here!)
├── database.py       # SQLite operations (users, coins, redemptions)
├── force_sub.py      # Force-subscribe gate (your ad mechanism)
├── config.py         # Env config loader
├── requirements.txt
├── Procfile          # For Render/Heroku/Railway
├── runtime.txt       # Python version
├── .env.example
└── README.md
```

## 💸 Redemption Flow

When a user has ≥ `MIN_REDEEM_COINS` (default 5000):

1. User taps **💸 Redeem** in menu and sends UPI ID.
2. Coins are deducted, request stored in `redemptions` table.
3. **Admin** (you) gets a Telegram DM with details.
4. Manually pay via UPI, then update DB status to `paid`.

> ⚠️ **Important:** Only redeem when YOU have earned enough from sponsors / ads to cover payouts. Set `COIN_TO_INR` low enough that you're profitable.

## 🔐 Safety / ToS Notes

- ✅ Coin Flip & Dice are **gameplay**, not real-money gambling — coins are virtual rewards. As long as you don't sell coins, it's fine.
- ❌ Don't host **pirated content** or **adult content** — Telegram will ban your bot.
- ✅ Force-subscribe is allowed by Telegram — just don't spam users.

## 🛠️ Future Add-ons

- Trivia tournaments with prizes
- Telegram Stars premium tier (ad-free + bonus coins)
- Mini App (HTML5) version with Adsgram ads
- Auto-payout via Razorpay / Cashfree API
- Hangman game
- Type Race
- Riddles
- Admin panel for redemption approvals
