# 🚀 2-Minute Deployment Guide

## Pehla: Telegram Bot Token Lo

1. Telegram kholo → search box mein type karo: **`BotFather`**
2. Blue tick wala **@BotFather** select karo
3. **START** button dabao
4. Send karo: `/newbot`
5. Bot ka naam type karo (e.g. `Mini Games Bot`)
6. Username type karo (must end with `bot`, e.g. `mygames123_bot`)
7. **Token copy karo** — kuch aisa dikhega:
   ```
   7891234567:AAH1xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
8. **Apna Telegram ID lo:** search karo `@userinfobot` → START → number copy karo

---

## Doosra: Render.com Pe Deploy Karo (FREE)

### A. Account banao
1. Jao [render.com](https://render.com) → **Sign Up** with GitHub
2. GitHub authorize karo

### B. Service create karo
1. Dashboard pe **+ New** → **Blueprint**
2. **Connect a repository** → `Miten001/timebucks` choose karo
3. Render automatically `render.yaml` detect kar lega
4. **Apply** dabao

### C. Environment Variables daalo
Render dashboard pe service open hoga. Left sidebar mein **Environment** click karo:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | (BotFather wala token paste karo) |
| `ADMIN_ID` | (aapka Telegram user ID) |
| `SPONSOR_CHANNELS` | (khali rakho abhi) |

**Save** dabao → **Manual Deploy** → **Deploy latest commit**

### D. 2-3 minute mein bot live hoga 🎉
Logs mein dikhega: `Bot starting...`

---

## Teesra: Bot Test Karo

Telegram mein apne bot ka username search karo (jo BotFather ko diya tha) → `/start` bhejo → game khelo!

---

## 📞 Stuck?

Render dashboard ke **Logs** tab mein error dikh raha hai — wo screenshot/text mujhe bhejo, main fix kar dunga.
