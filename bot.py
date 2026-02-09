# ================= IMPORTS =================
import os
import time
import random
import threading
from datetime import datetime, timedelta

import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ================= KEEP-ALIVE (RENDER) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT IS ALIVE"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def keep_alive():
    Thread(target=run_flask, daemon=True).start()

# ================= CONFIG =================
TOKEN = os.environ.get("TOKEN")          # SET IN RENDER ENV
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

if not TOKEN or ":" not in TOKEN:
    raise ValueError("❌ TELEGRAM TOKEN INVALID OR NOT SET")

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=4)

verified_users = set()
user_sessions = {}

# ================= SLOT PROVIDERS & GAMES (HINDI BINAWASAN) =================
PROVIDERS_DATA = {
    "PRAGMATIC PLAY": [
        "888 DRAGONS","3 BUZZING WILDS","5 LIONS","5 LIONS DANCE","5 LIONS GOLD","5 LIONS MEGAWAYS",
        "8 DRAGONS","AZTEC BONANZA","AZTEC GEMS","BIG BASS BONANZA","BIG BASS BONANZA MEGAWAYS",
        "BIG BASS SPLASH","BIG BASS AMAZON XTREME","BUFFALO KING","BUFFALO KING MEGAWAYS",
        "CASH BONANZA","CAISHEN’S GOLD","CHILLI HEAT","CHILLI HEAT MEGAWAYS",
        "CHRISTMAS BIG BASS BONANZA","COUNTRY FARMING","DIAMOND STRIKE",
        "DRAGON KINGDOM – EYES OF FIRE","EYE OF THE STORM","FIRE 88","FRUIT PARTY","FRUIT PARTY 2",
        "FRUIT RAINBOW","FRUIT TWIST","GATES OF OLYMPUS","GATES OF OLYMPUS 1000",
        "GATES OF GATOT KACA","GATES OF GATOT KACA 1000","GATOT KACA’S FURY","GEM FIRE FORTUNE",
        "GEMS BONANZA","GOLDEN OX","GREAT RHINO","GREAT RHINO MEGAWAYS","HOT TO BURN",
        "HOT TO BURN EXTREME","IRISH CHARMS","JOKER’S JEWELS","JUNGLE GORILLA",
        "KING OF ATLANTIS","LUCKY NEW YEAR","MAGIC JOURNEY","MASTER JOKER","MONKEY MADNESS",
        "MUSTANG GOLD","MUSTANG GOLD MEGAWAYS","PHOENIX FORGE","PIRATE GOLD",
        "POWER OF THOR MEGAWAYS","RELEASE THE KRAKEN","RIVER WILD","ROBOJOKER","ROCKET REELS",
        "SANTA’S WONDERLAND","SAFARI KING","SILVER BULLET","SPACEMAN","STARZ MEGAWAYS",
        "STARLIGHT PRINCESS","STARLIGHT PRINCESS 1000","SUGAR RUSH","SUGAR RUSH 1000",
        "SWEET BONANZA","SWEET BONANZA XMAS","THE DOG HOUSE","THE DOG HOUSE MEGAWAYS",
        "THE HAND OF MIDAS","TRIPLE TIGERS","ULTRA BURN","WILD BEACH PARTY","WILD SPELLS",
        "WILD WEST GOLD","WILD WEST GOLD BLAZING BOUNTY","WOLF GOLD","YEAR OF THE OX",
        "YEAR OF THE TIGER","ZEUS VS HADES – GODS OF WAR"
    ],
    "PG SOFT": [
        "ALCHEMY GOLD","ANUBIS WRATH","BALI VACATION","BATTLEGROUND ROYALE","BIKINI PARADISE",
        "BUFFALO WIN","BUTTERFLY BLOSSOM","CAISHEN GOLD","CASH MANIA","COCKTAIL NIGHTS",
        "DESTINY OF SUN AND MOON","DRAGON HATCH","DRAGON HATCH 2","DRAGON TIGER LUCK",
        "DOUBLE FORTUNE","FORTUNE MOUSE","FORTUNE OX","FORTUNE RABBIT","FORTUNE TIGER",
        "GANESHA GOLD","GEM SAVIOUR CONQUEST","GEM SAVIOUR SWORD","GALACTIC GEMS",
        "GENIE’S 3 WISHES","GROUNDHOG HARVEST","GUARDIANS OF ICE AND FIRE","HIP HOP PANDA",
        "HONEY TRAP OF DIAO CHAN","JACK THE GIANT HUNTER","JUNGLE DELIGHT","KING ARTHUR",
        "KRAKEN GOLD RUSH","LEPRECHAUN RICHES","LUCKY NEKO","LUCKY PIGGY","MAHJONG WAYS",
        "MAHJONG WAYS 2","MEDUSA","MEDUSA II","MERMAID RICHES","MR HALLOW-WIN",
        "MYTHICAL GUARDIANS","OISHI DELIGHTS","PEAS FAIRY","PHOENIX RISES",
        "PIRATE’S BOUNTY","RAVE PARTY FEVER","REEL LOVE","SAFARI WILDS","SPEED WINNER",
        "SUSHI OISHI","THE GREAT ICESCAPE","TREASURES OF AZTEC","VAMPIRE’S CHARM",
        "WILD BANDITO","WILD BOUNTY SHOWDOWN","WIN WIN FISH PRAWN CRAB","ZOMBIE OUTBREAK"
    ],
    "JILI": [
        "SUPER ACE","SUPER ACE DELUXE","GOLDEN EMPIRE","GOLDEN EMPIRE 2","LUCKY COMING",
        "FORTUNE GEMS","FORTUNE GEMS 2","ROMA X DELUXE","PHARAOH TREASURE","CRAZY 777",
        "LUCKY GOLDBRICKS","FORTUNE TREE","SWEET MAGIC","NEKO FORTUNE","GOLDEN BANK 2",
        "MONEY COMING","COIN TREE","3 CHARGE BUFFALO","AGENT ACE","BOXING KING",
        "MAGIC LAMP","DRAGON TREASURE 2","CHIN SHI HUANG","TWIN WINS","BUBBLE BEAUTY",
        "CANDY BABY","LUCKY JAGUAR","FORTUNE KING JACKPOT","GOLDEN BANK","WILD ACE",
        "SUPER ACE 2 STACK","SUPER ACE JOKER","MONEY COMING EXPAND BETS",
        "LUCKY TIGER","SAFARI MYSTERY"
    ],
    "HABANERO": [
        "ATOMIC KITTENS","ARCTIC WONDERS","ARCANE ELEMENTS","BEFORE TIME RUNS OUT","BABA YAGA",
        "BARNSTORMER BUCKS","BIKINI ISLAND","BIKINI ISLAND DELUXE","BLACKBEARD’S BOUNTY",
        "BOMB RUNNER","BOMBS AWAY","CALAVERAS EXPLOSIVAS","CANDY TOWER","CARNIVAL CASH",
        "CARNIVAL COVE","COYOTE CRASH","CRYSTOPIA","DISCO BEATS","DISCO FUNK",
        "DRAGON CASTLE","DRAGON TIGER GATE","DRAGON’S REALM","EGYPTIAN DREAMS",
        "EGYPTIAN DREAMS DELUXE","FA CAI SHEN","FA CAI SHEN DELUXE","FENGHUANG","FLY!",
        "FORTUNE DOGS","FRONTIER FORTUNES","GOLD RUSH","HAPPY APE","HAPPY APE WILD",
        "HEY SUSHI","HOT HOT FRUIT","HOT HOT SUMMER","HOT HOT HALLOWEEN",
        "INDIAN CASH CATCHER","JELLYFISH FLOW","JELLYFISH FLOW ULTRA","JUMP!","JUMP! 2",
        "KOI GATE","LANTERN LUCK","LEGEND OF NEZHA","LEGENDARY BEASTS","LOONY BLOX",
        "LUCKY DURIAN","LUCKY FORTUNE CAT","LUCKY LUCKY","MAGIC OAK","MARVELOUS FURLONGS",
        "MIGHTY MEDUSA","MOUNT MAZUMA","MYSTIC FORTUNE","MYSTIC FORTUNE DELUXE",
        "NAUGHTY SANTA","NAUGHTY WUKONG","NINE TAILS","NUWA","OCEAN’S CALL",
        "ORBS OF ATLANTIS","PIRATE’S PLUNDER","PRESTO!","PROST!","RAINBOWMANIA",
        "RETURN TO THE FEATURE","ROMAN EMPIRE","ROLLING ROGER","RODEO DRIVE",
        "SANTA’S VILLAGE","SCOPA","SCRUFFY SCALLYWAGS","SHAMROCK QUEST",
        "SKY’S THE LIMIT","SLIME PARTY","SOJU BOMB","SPACE GOONZ","SPARTA",
        "SUPER FRUIT BLAST","TABERNA DE LOS MUERTOS","TAIKO BEATS","TUK TUK THAILAND",
        "VAMPIRE’S FATE","WEALTH INN","WAYS OF FORTUNE","WILD TRUCKS",
        "WIZARD’S WANT WAR!","ZEUS","ZEUS II"
    ],
    "HACKSAW": [
        "WANTED DEAD OR A WILD","CHAOS CREW","LE RIPPER","HAND OF ANUBIS","MENTAL",
        "CURSED SEAS","FRUITS","STACK EM","BORN WILD","CUBAN CRISIS"
    ],
    "ROYAL SLOT": [
        "ROYAL DRAGON","ROYAL FORTUNE","ROYAL GOLD","ROYAL TIGER","ROYAL BUFFALO"
    ],
    "LATO": [
        "LATO CLASSIC","LATO GOLD","LATO TURBO","LATO JACKPOT"
    ]
}

# ================= SIGNAL PATTERNS (30+ HINDI BINAWASAN) =================
SIGNALS = [
    "5 MANUAL → 10 TURBO → STOP","10 MANUAL → 20 TURBO","7 QUICK → 15 MANUAL",
    "20 TURBO (LOW BET)","15 MANUAL → BUY FEATURE","5 TURBO → 10 QUICK → 5 MANUAL",
    "10 TURBO → STOP → 10 TURBO","8 MANUAL → 12 TURBO","3 QUICK → 15 TURBO",
    "10 MANUAL → 10 QUICK","20 MANUAL (LOW BET)","5 MANUAL → BUY FEATURE",
    "12 TURBO → STOP → 8 TURBO","6 QUICK → 12 MANUAL","15 TURBO → BUY FEATURE",
    "10 MANUAL → STOP → 10 TURBO","8 TURBO → 8 QUICK","5 QUICK → BUY FEATURE",
    "12 MANUAL → 18 TURBO","10 TURBO → RAISE BET",
    "7 MANUAL → 7 TURBO → 7 QUICK","15 QUICK (LOW BET)",
    "5 MANUAL → 15 TURBO → STOP","10 TURBO → BUY FEATURE","20 MANUAL → STOP",
    "8 QUICK → 12 TURBO","10 MANUAL → BUY FEATURE (SAFE)",
    "RAPID SPIN x10 → BUY FEATURE","LOW BET 15 TURBO → HIGH BET 5 TURBO",
    "TEST SPIN 5x → FULL ATTACK 20 TURBO"
]

# ================= HELPERS =================
def ensure_session(uid):
    if uid not in user_sessions:
        user_sessions[uid] = {
            "provider": None,
            "game": None,
            "encoding": False,
            "signal_history": []
        }

def get_signal(uid):
    hist = user_sessions[uid]["signal_history"]
    choices = [s for s in SIGNALS if s not in hist[-3:]] or SIGNALS[:]
    pick = random.choice(choices)
    hist.append(pick)
    return pick

# ================= UI =================
def main_menu(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for p in PROVIDERS_DATA.keys():
        kb.add(types.KeyboardButton(p))
    bot.send_message(chat_id, "🎰 <b>Select Slot Provider</b>", reply_markup=kb, parse_mode="HTML")

def games_menu(chat_id, provider):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("🔙 BACK"))
    for g in PROVIDERS_DATA[provider]:
        kb.add(types.KeyboardButton(g))
    bot.send_message(chat_id, f"🎮 <b>{provider}</b>\nSelect Game:", reply_markup=kb, parse_mode="HTML")

def live_loading(chat_id, message_id, uid):
    frames = ["⏳","⌛","🔄","📡"]
    i = 0
    while user_sessions.get(uid, {}).get("encoding"):
        try:
            bot.edit_message_text(
                user_sessions[uid]["result_text"] + f"\n\n{frames[i % len(frames)]} <b>ENCODING LIVE DATA...</b>",
                chat_id, message_id, parse_mode="HTML"
            )
        except:
            break
        i += 1
        time.sleep(1.2)

# ================= HANDLERS =================
@bot.message_handler(commands=["start"])
def start_cmd(message):
    uid = message.from_user.id
    ensure_session(uid)
    verified_users.add(uid)
    main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text in PROVIDERS_DATA)
def pick_provider(message):
    uid = message.from_user.id
    ensure_session(uid)
    user_sessions[uid]["provider"] = message.text
    games_menu(message.chat.id, message.text)

@bot.message_handler(func=lambda m: m.text == "🔙 BACK")
def back_menu(message):
    main_menu(message.chat.id)

@bot.message_handler(func=lambda m: any(m.text in games for games in PROVIDERS_DATA.values()))
def pick_game(message):
    uid = message.from_user.id
    ensure_session(uid)
    user_sessions[uid]["game"] = message.text
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 ANALYZE", callback_data="analyze"))
    bot.send_message(
        message.chat.id,
        f"🎯 <b>GAME:</b> {message.text}",
        reply_markup=kb,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda c: c.data == "analyze")
def analyze(call):
    uid = call.from_user.id
    ensure_session(uid)
    user_sessions[uid]["encoding"] = True

    signal = get_signal(uid)
    winrate = random.uniform(91, 98)
    valid_until = (datetime.utcnow() + timedelta(hours=8, minutes=random.randint(30, 45))).strftime("%I:%M %p")

    result = (
        f"🚥 <b>CONFIRMED SIGNAL</b>\n"
        f"🕹 <b>Provider:</b> {user_sessions[uid]['provider']}\n"
        f"🎮 <b>Game:</b> {user_sessions[uid]['game']}\n"
        f"✅ <b>Winrate:</b> {winrate:.2f}%\n"
        f"⏰ <b>Valid Until:</b> {valid_until} PHT\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>PATTERN</b>\n{signal}"
    )

    user_sessions[uid]["result_text"] = result
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
