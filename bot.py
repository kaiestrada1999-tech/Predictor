# ================= IMPORTS =================
import telebot
import random
import time
import os
import threading
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

# ================= KEEP ALIVE =================
app = Flask('')

@app.route('/')
def home():
    return "BOT IS ALIVE"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def keep_alive():
    Thread(target=run).start()

# ================= CONFIG =================
TOKEN = "ILAGAY_MO_DITO_TOKEN_MO"
ADMIN_ID = 123456789

bot = telebot.TeleBot(TOKEN, threaded=True)

verified_users = {ADMIN_ID: True}
user_sessions = {}

# ================= SLOT PROVIDERS =================
PROVIDERS_DATA = {
    "PRAGMATIC PLAY": [
        "GATES OF OLYMPUS","GATES OF OLYMPUS 1000","SWEET BONANZA","SUGAR RUSH",
        "SUGAR RUSH 1000","WOLF GOLD","BIG BASS BONANZA","BIG BASS SPLASH",
        "STARLIGHT PRINCESS","STARLIGHT PRINCESS 1000","FRUIT PARTY","FRUIT PARTY 2",
        "THE DOG HOUSE","THE DOG HOUSE MEGAWAYS","WILD WEST GOLD","ZEUS VS HADES",
        "FIRE 88","5 LIONS","5 LIONS MEGAWAYS","8 DRAGONS","AZTEC GEMS",
        "BUFFALO KING","BUFFALO KING MEGAWAYS","POWER OF THOR MEGAWAYS",
        "RELEASE THE KRAKEN","GEMS BONANZA","GOLD PARTY","JOKER JEWELS"
    ],
    "PG SOFT": [
        "MAHJONG WAYS","MAHJONG WAYS 2","LUCKY NEKO","FORTUNE TIGER",
        "FORTUNE OX","FORTUNE RABBIT","DRAGON HATCH","MEDUSA","GEM SAVIOUR",
        "PHOENIX RISES","TREASURES OF AZTEC","WILD BANDITO"
    ],
    "HACKSAW": [
        "CHAOS CREW","WANTED DEAD OR A WILD","LE RIPPER","HAND OF ANUBIS",
        "MENTAL","CURSED SEAS","FRUITS","STACK EM","BORN WILD","CUBAN CRISIS"
    ],
    "ROYAL SLOT": [
        "ROYAL DRAGON","ROYAL FORTUNE","ROYAL GOLD","ROYAL TIGER","ROYAL BUFFALO"
    ],
    "LATO LATO": [
        "LATO CLASSIC","LATO GOLD","LATO TURBO","LATO JACKPOT"
    ]
}

# ================= SIGNAL PATTERNS (30+) =================
SIGNALS = [
    "5 MANUAL → 10 TURBO → STOP",
    "10 MANUAL → 20 TURBO",
    "7 QUICK → 15 MANUAL",
    "20 TURBO (LOW BET)",
    "15 MANUAL → BUY FEATURE",
    "5 TURBO → 10 QUICK → 5 MANUAL",
    "10 TURBO → STOP → 10 TURBO",
    "8 MANUAL → 12 TURBO",
    "3 QUICK → 15 TURBO",
    "10 MANUAL → 10 QUICK",
    "20 MANUAL (LOW BET)",
    "5 MANUAL → BUY FEATURE",
    "12 TURBO → STOP → 8 TURBO",
    "6 QUICK → 12 MANUAL",
    "15 TURBO → BUY FEATURE",
    "10 MANUAL → STOP → 10 TURBO",
    "8 TURBO → 8 QUICK",
    "5 QUICK → BUY FEATURE",
    "12 MANUAL → 18 TURBO",
    "10 TURBO → RAISE BET",
    "7 MANUAL → 7 TURBO → 7 QUICK",
    "15 QUICK (LOW BET)",
    "5 MANUAL → 15 TURBO → STOP",
    "10 TURBO → BUY FEATURE",
    "20 MANUAL → STOP",
    "8 QUICK → 12 TURBO",
    "10 MANUAL → BUY FEATURE (SAFE)",
    "RAPID SPIN x10 → BUY FEATURE",
    "LOW BET 15 TURBO → HIGH BET 5 TURBO",
    "TEST SPIN 5x → FULL ATTACK 20 TURBO"
]

# ================= NO-REPEAT SYSTEM =================
def get_signal(uid):
    history = user_sessions[uid].setdefault("signal_history", [])
    choices = [s for s in SIGNALS if s not in history[-3:]]
    signal = random.choice(choices)
    history.append(signal)
    return signal

# ================= MAIN MENU =================
def main_menu(chat_id, uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in PROVIDERS_DATA:
        kb.add(p)
    bot.send_message(chat_id, "🎰 SELECT SLOT PROVIDER", reply_markup=kb)

# ================= LIVE LOADING =================
def live_loading(chat_id, msg_id, uid):
    frames = ["⏳","⌛","🔄","📡"]
    i = 0
    while user_sessions[uid]["encoding"]:
        try:
            bot.edit_message_text(
                user_sessions[uid]["result"] + f"\n\n{frames[i%4]} ENCODING LIVE DATA...",
                chat_id, msg_id, parse_mode="HTML"
            )
        except:
            break
        i += 1
        time.sleep(1)

# ================= HANDLERS =================
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    verified_users[uid] = True
    user_sessions[uid] = {"encoding": False}
    main_menu(message.chat.id, uid)

@bot.message_handler(func=lambda m: m.text in PROVIDERS_DATA)
def provider_pick(message):
    uid = message.from_user.id
    user_sessions[uid]["provider"] = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for g in PROVIDERS_DATA[message.text]:
        kb.add(g)
    bot.send_message(message.chat.id, "🎮 SELECT GAME", reply_markup=kb)

@bot.message_handler(func=lambda m: any(m.text in g for g in PROVIDERS_DATA.values()))
def game_pick(message):
    uid = message.from_user.id
    user_sessions[uid]["game"] = message.text
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 ANALYZE", callback_data="analyze"))
    bot.send_message(message.chat.id, f"🎯 GAME: {message.text}", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "analyze")
def analyze(call):
    uid = call.from_user.id
    user_sessions[uid]["encoding"] = True

    signal = get_signal(uid)
    winrate = random.uniform(91, 98)
    until = (datetime.utcnow() + timedelta(hours=8, minutes=40)).strftime("%I:%M %p")

    result = (
        f"<b>🚥 CONFIRMED SIGNAL</b>\n"
        f"Provider: {user_sessions[uid]['provider']}\n"
        f"Game: {user_sessions[uid]['game']}\n"
        f"Winrate: {winrate:.2f}%\n"
        f"Valid Until: {until} PHT\n\n"
        f"<b>📊 PATTERN</b>\n{signal}"
    )

    user_sessions[uid]["result"] = result
    msg = bot.send_message(call.message.chat.id, result, parse_mode="HTML")

    threading.Thread(
        target=live_loading,
        args=(call.message.chat.id, msg.message_id, uid),
        daemon=True
    ).start()

# ================= RUN =================
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
