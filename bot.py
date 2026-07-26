import telebot
import random
import time
import os
import threading
import uuid
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

# ================= KEEP-ALIVE PARA SA RENDER =================
app = Flask('')

@app.route('/')
def home():
    return "SYSTEM STATUS: LIVE SYNC ACTIVE"

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or ""
ADMIN_ID = os.environ.get("ADMIN_ID") or ""

# URL ng Image para sa Intro
INTRO_IMAGE_URL = "https://i.imghippo.com/files/jFEp1747BHI.png" 

# ================= CASINO LINKS DATABASE =================
CASINO_DATA = {
    "BINGOPLUS ": "https://t.me/Helpslotwinbot/bingoplus",
    "AGILA CLUB": "https://t.me/Helpslotwinbot/agilaclub",
    "PLAYTIME": "https://t.me/Helpslotwinbot/playtime",
    "JILIBET": "https://t.me/Helpslotwinbot/jilibet",
    "TIKLUCK (new)": "https://t.me/Helpslotwinbot/tikluck",
    "GD ENEMERALD": "https://t.me/Helpslotwinbot/gdemerald",
    "MACALLAN77": "https://t.me/Helpslotwinbot/macallan77",
    "INFERNO PLAY": "https://t.me/Helpslotwinbot/infernoplay",
    "BUGATTI PLAY ": "https://t.me/Helpslotwinbot/buggatattiplay",
    "MASERATI PLAY": "https://t.me/Helpslotwinbot/maseratiplay",
    "LOTUS PLAY": "https://t.me/Helpslotwinbot/lotusplay",
    "LAMBO PLAY": "https://t.me/Helpslotwinbot/lamboplay"
}

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)

# ================= SECURITY CONFIG & OVERRIDES =================
PROTECT_CONTENT = True
PROTECT_FILE = "protect_settings.txt"

def load_protect_setting():
    global PROTECT_CONTENT
    if os.path.exists(PROTECT_FILE):
        try:
            with open(PROTECT_FILE, "r") as f:
                content = f.read().strip()
                if content == "False":
                    PROTECT_CONTENT = False
                else:
                    PROTECT_CONTENT = True
        except: pass

def save_protect_setting(val):
    global PROTECT_CONTENT
    PROTECT_CONTENT = val
    try:
        with open(PROTECT_FILE, "w") as f:
            f.write(str(val))
    except: pass

load_protect_setting()

def is_admin(chat_id):
    try:
        admin_val = int(ADMIN_ID) if ADMIN_ID else 0
        return str(chat_id) == str(admin_val)
    except:
        return False

_orig_send_message = bot.send_message
def _secure_send_message(chat_id, text, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    return _orig_send_message(chat_id, text, **kwargs)
bot.send_message = _secure_send_message

_orig_send_photo = bot.send_photo
def _secure_send_photo(chat_id, photo, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    return _orig_send_photo(chat_id, photo, **kwargs)
bot.send_photo = _secure_send_photo

_orig_send_document = bot.send_document
def _secure_send_document(chat_id, document, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    return _orig_send_document(chat_id, document, **kwargs)
bot.send_document = _secure_send_document

_orig_copy_message = bot.copy_message
def _secure_copy_message(chat_id, from_chat_id, message_id, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    return _orig_copy_message(chat_id, from_chat_id, message_id, **kwargs)
bot.copy_message = _secure_copy_message

def teleclaw_thinking(chat_id, action="Working", duration=2, final_text=None, reply_markup=None, call_id=None):
    try:
        bot.send_chat_action(chat_id, "typing")
        caption = f"âœ¨ {action}...\n<code>0s</code>"
        msg = bot.send_message(chat_id, caption, parse_mode="HTML")
        
        steps = duration * 2
        for step in range(1, steps + 1):
            time.sleep(0.5)
            try:
                if step % 3 == 0:
                    bot.send_chat_action(chat_id, "typing")
                
                sec_val = step // 2
                curr_dots = "." * (1 + (step % 3))
                edited_text = f"âœ¨ {action}{curr_dots}\n<code>{sec_val}s</code>"
                
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=edited_text,
                    parse_mode="HTML"
                )
            except:
                break
        
        time.sleep(0.3)
        try:
            if final_text:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=final_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                bot.delete_message(chat_id, msg.message_id)
        except:
            pass
        
        # Answer the callback query only after animation completes
        if call_id:
            try:
                bot.answer_callback_query(call_id)
            except:
                pass
    except:
        pass

user_sessions = {}
user_ids = set() 
USER_IDS_FILE = "users.txt"

def load_users():
    global user_ids
    if os.path.exists(USER_IDS_FILE):
        try:
            with open(USER_IDS_FILE, "r") as f:
                ids = f.read().splitlines()
                user_ids = set(int(uid) for uid in ids if uid.strip().isdigit())
        except: pass

def save_user(uid):
    if uid not in user_ids:
        user_ids.add(uid)
        try:
            with open(USER_IDS_FILE, "a") as f:
                f.write(f"{uid}\n")
        except: pass

# ================= TURSO DATABASE SETUP =================
# Persistent storage powered by Turso (libSQL)
import libsql_client as libsql
import os

class TursoDB:
    def __init__(self, url, token):
        # Force https for better compatibility in server environments
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://")
        self.client = libsql.create_client_sync(url=url, auth_token=token)
        self.init_db()
    def init_db(self):
        self.client.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
    def add_user(self, user_id):
        try:
            self.client.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", [user_id])
            return True
        except Exception as e:
            print(f"Error adding user to Turso: {e}")
            return False
    def add_users_batch(self, user_ids_list):
        if not user_ids_list: return True
        try:
            for i in range(0, len(user_ids_list), 500):
                chunk = user_ids_list[i:i+500]
                placeholders = ",".join(["(?)"] * len(chunk))
                self.client.execute(f"INSERT OR IGNORE INTO users (id) VALUES {placeholders}", chunk)
            return True
        except Exception as e:
            print(f"Error batch adding users to Turso: {e}")
            return False

    def get_all_users(self):
        try:
            rs = self.client.execute("SELECT id FROM users")
            return [row[0] for row in rs]
        except Exception as e:
            print(f"Error getting users from Turso: {e}")
            return []

# Priority: Environment Variables -> Dashboard Config
TURSO_URL = os.environ.get("TURSO_URL") or "libsql://slotusers-slotposter.aws-ap-northeast-1.turso.io"
TURSO_TOKEN = os.environ.get("TURSO_TOKEN") or "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzg1OTQ1MzAsImlkIjoiMDE5ZTFjN2UtOWQwMS03ZGZmLWJiMzItNjVlNDZlZDMxNmUyIiwicmlkIjoiOGE0MGFiNzMtMTllZC00MDAzLWJjOTktZjY5ZTVlZjkxZDk0In0.gGXftGF720LX27uLV5ezHp29WoQUez6CHGulnArbNpCXKXM1soDbhKfzTndqlg6Rrk90zWZK5gfw9fYcKbY3BA"

db_manager = None
if TURSO_URL and TURSO_TOKEN:
    try:
        db_manager = TursoDB(url=TURSO_URL, token=TURSO_TOKEN)
        print("âœ… Turso Database connected successfully.")
    except Exception as e:
        print(f"âš ï¸ Turso Database connection error: {e}. Falling back to local file storage.")
else:
    print("â„¹ï¸ TURSO_URL or TURSO_TOKEN not provided. Falling back to local file storage.")

# Safe fallback user handlers
def load_users_local():
    global user_ids
    if os.path.exists(USER_IDS_FILE):
        try:
            with open(USER_IDS_FILE, "r") as f:
                ids = f.read().splitlines()
                user_ids = set(int(uid) for uid in ids if uid.strip().isdigit())
        except: pass

def save_user_local(uid):
    if uid not in user_ids:
        user_ids.add(uid)
        try:
            with open(USER_IDS_FILE, "a") as f:
                f.write(f"{uid}\n")
        except: pass

def load_users():
    global user_ids
    if db_manager:
        try:
            users = db_manager.get_all_users()
            if users:
                user_ids = set(users)
                print(f"Loaded {len(user_ids)} users from Turso.")
                return
        except Exception as e:
            print(f"Error loading users from Turso: {e}")
    load_users_local()
    print(f"Loaded {len(user_ids)} users from local file.")

def save_user(uid):
    global user_ids
    if uid not in user_ids:
        saved_turso = False
        if db_manager:
            saved_turso = db_manager.add_user(uid)
        save_user_local(uid)
        if saved_turso:
            print(f"New user {uid} saved to Turso & local file.")

load_users()


# ================= DATA: EXPANDED GAME LIST =================
DEFAULT_PROVIDERS_DATA = {
        "PRAGMATIC PLAY": [
            {"n": "GATES OF OLYMPUS", "bb": 0}, {"n": "GATES OF OLYMPUS 1000", "bb": 1}, {"n": "SWEET BONANZA", "bb": 1}, {"n": "SWEET BONANZA 1000", "bb": 1}, {"n": "SUGAR RUSH", "bb": 0}, {"n": "SUGAR RUSH 1000", "bb": 1},
            {"n": "STARLIGHT PRINCESS", "bb": 1}, {"n": "STARLIGHT PRINCESS 1000", "bb": 1}, {"n": "THE DOG HOUSE", "bb": 0}, {"n": "THE DOG HOUSE MEGAWAYS", "bb": 1}, {"n": "THE DOG HOUSE MULTIHOLD", "bb": 0}, {"n": "FRUIT PARTY", "bb": 0},
            {"n": "FRUIT PARTY 2", "bb": 0}, {"n": "WOLF GOLD", "bb": 0}, {"n": "MUSTANG GOLD", "bb": 0}, {"n": "GREAT RHINO MEGAWAYS", "bb": 1}, {"n": "CHILLI HEAT", "bb": 0}, {"n": "AZTEC GEMS", "bb": 0},
            {"n": "AZTEC GEMS DELUXE", "bb": 0}, {"n": "WILD WEST GOLD", "bb": 0}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "THE HAND OF MIDAS", "bb": 0}, {"n": "POWER OF THOR MEGAWAYS", "bb": 1}, {"n": "BUFFALO KING", "bb": 0},
            {"n": "BUFFALO KING MEGAWAYS", "bb": 1}, {"n": "JUICY FRUITS", "bb": 0}, {"n": "GEMS BONANZA", "bb": 1}, {"n": "RISE OF GIZA", "bb": 0}, {"n": "CHICKEN DROP", "bb": 0}, {"n": "BOOK OF FALLEN", "bb": 0},
            {"n": "MAGICIAN'S SECRETS", "bb": 0}, {"n": "CRYSTAL CAVERNS", "bb": 0}, {"n": "SMUGGLERS COVE", "bb": 0}, {"n": "SANTA'S WONDERLAND", "bb": 0}, {"n": "STAR PIRATES CODE", "bb": 0}, {"n": "MYSTIC CHIEF", "bb": 0},
            {"n": "PIGGY BANK BILLS", "bb": 0}, {"n": "TREASURE WILD", "bb": 0}, {"n": "GATES OF GATOT KACA", "bb": 0}, {"n": "MOCKTAIL NIGHTS", "bb": 0}, {"n": "SWORD OF ARES", "bb": 0}, {"n": "SHIELD OF SPARTA", "bb": 0},
            {"n": "TOWERING FORTUNES", "bb": 0}, {"n": "RELEASE THE KRAKEN 2", "bb": 0}, {"n": "SPIN & SCORE", "bb": 0}, {"n": "OLD GOLD MINER", "bb": 0}, {"n": "CANDY STARS", "bb": 0}, {"n": "CLEOCATRA", "bb": 0},
            {"n": "WILD BEACH PARTY", "bb": 0}, {"n": "QUEEN OF GODS", "bb": 0}, {"n": "ZOMBIE CARNIVAL", "bb": 0}, {"n": "FORTUNE OF GIZA", "bb": 0}, {"n": "SPIRIT OF ADVENTURE", "bb": 0}, {"n": "CLOVER GOLD", "bb": 0},
            {"n": "EYE OF CLEOPATRA", "bb": 0}, {"n": "NORTH GUARDIANS", "bb": 0}, {"n": "DRILL THAT GOLD", "bb": 0}, {"n": "BARN FESTIVAL", "bb": 0}, {"n": "RAINBOW GOLD", "bb": 0}, {"n": "TIC TAC TAKE", "bb": 0},
            {"n": "WILD DEPTHS", "bb": 0}, {"n": "GOLD PARTY", "bb": 0}, {"n": "ROCK VEGAS", "bb": 0}, {"n": "EMPEROR CAISHEN", "bb": 0}, {"n": "LUCKY LIGHTNING", "bb": 0}, {"n": "DRAGON HOT HOLD & SPIN", "bb": 0},
            {"n": "HEART OF RIO", "bb": 0}, {"n": "PANDA'S FORTUNE 2", "bb": 0}, {"n": "5 LIONS MEGAWAYS", "bb": 1}, {"n": "BOOK OF VIKINGS", "bb": 0}, {"n": "LUCKY GRACE AND CHARM", "bb": 0}, {"n": "RISE OF SAMURAI MEGAWAYS", "bb": 1},
            {"n": "CHICKEN CHASE", "bb": 0}, {"n": "WILD WEST DUELS", "bb": 0}, {"n": "MYSTERY OF THE ORIENT", "bb": 0}, {"n": "PEAK POWER", "bb": 0}, {"n": "CLUB TROPICANA", "bb": 0}, {"n": "THE KNIGHT KING", "bb": 0},
            {"n": "GODS OF GIZA", "bb": 0}, {"n": "KINGDOM OF THE DEAD", "bb": 0}, {"n": "EXCALIBUR UNLEASHED", "bb": 0}, {"n": "ZEUS VS HADES", "bb": 0}, {"n": "JEWEL RUSH", "bb": 0}, {"n": "STICKY BEES", "bb": 0},
            {"n": "PIRATES PUB", "bb": 0}, {"n": "FLOATING DRAGON", "bb": 0}, {"n": "FLOATING DRAGON MEGAWAYS", "bb": 1}, {"n": "TRIPLE TIGERS", "bb": 0}, {"n": "888 DRAGONS", "bb": 0}, {"n": "MONKEY MADNESS", "bb": 0},
            {"n": "MASTER JOKER", "bb": 0}, {"n": "FIRE STRIKE", "bb": 0}, {"n": "FIRE STRIKE 2", "bb": 0}, {"n": "DIAMOND STRIKE", "bb": 0}, {"n": "EXTRA JUICY", "bb": 0}, {"n": "EXTRA JUICY MEGAWAYS", "bb": 1},
            {"n": "WILD WILD RICHES", "bb": 0}, {"n": "WILD WILD RICHES MEGAWAYS", "bb": 1}, {"n": "PYRAMID KING", "bb": 0}, {"n": "HOT TO BURN", "bb": 0}, {"n": "HOT TO BURN EXTREME", "bb": 0}, {"n": "ULTRA HOLD AND SPIN", "bb": 0},
            {"n": "LUCKY, GRACE & CHARM", "bb": 0}, {"n": "EMPTY THE BANK", "bb": 0}, {"n": "FLOATING DRAGON", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "7 PIGGIES", "bb": 0}, {"n": "888 GOLD", "bb": 0},
            {"n": "ALADDIN AND THE SORCERER", "bb": 0}, {"n": "AMAZING MONEY MACHINE", "bb": 0}, {"n": "ANCIENT EGYPT CLASSIC", "bb": 0}, {"n": "BEOWULF", "bb": 0}, {"n": "BOOK OF TUT", "bb": 0}, {"n": "BRONCO SPIRIT", "bb": 0},
            {"n": "CASH BONANZA", "bb": 1}, {"n": "CASH ELEVATOR", "bb": 0}, {"n": "CONGO CASH", "bb": 0}, {"n": "COWBOYS GOLD", "bb": 0}, {"n": "CURSE OF THE WEREWOLF", "bb": 0}, {"n": "DA VINCI'S TREASURE", "bb": 0},
            {"n": "DANCE PARTY", "bb": 0}, {"n": "DAY OF DEAD", "bb": 0}, {"n": "DIAMOND ARE FOREVER", "bb": 0}, {"n": "DRAGON KINGDOM", "bb": 0}, {"n": "DRAGON TIGER", "bb": 0}, {"n": "DWARF MINE", "bb": 0},
            {"n": "EMERALD KING", "bb": 0}, {"n": "EMERALD KING JACKPOT", "bb": 0}, {"n": "FAIRYTALE FORTUNE", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "GATES OF VALHALLA", "bb": 0}, {"n": "GLOOMY GRAVEYARD", "bb": 0},
            {"n": "GOLD RUSH", "bb": 0}, {"n": "GOLD TRAIN", "bb": 0}, {"n": "GOLDEN BEAUTY", "bb": 0}, {"n": "GOLDEN OX", "bb": 0}, {"n": "GREAT RHINO", "bb": 0}, {"n": "GREAT RHINO DELUXE", "bb": 0},
            {"n": "HERCULES AND PEGASUS", "bb": 0}, {"n": "HOT SAFARI", "bb": 0}, {"n": "JADE BUTTERFLY", "bb": 0}, {"n": "JOKER KING", "bb": 0}, {"n": "JOKER'S JEWELS", "bb": 0}, {"n": "JOURNEY TO THE WEST", "bb": 0},
            {"n": "JUNGLE GORILLA", "bb": 0}, {"n": "KNIGHT HOT SPOTZ", "bb": 0}, {"n": "LEPRECHAUN CAROL", "bb": 0}, {"n": "LEPRECHAUN SONG", "bb": 0}, {"n": "LUCKY DRAGONS", "bb": 0}, {"n": "LUCKY NEW YEAR", "bb": 0},
            {"n": "MASTER CHEN'S FORTUNE", "bb": 0}, {"n": "MEDUSA STRIKE", "bb": 0}, {"n": "MONEY MOUSE", "bb": 0}, {"n": "MONKEY WARRIOR", "bb": 0}, {"n": "MOON PRINCESS", "bb": 1}, {"n": "MYSTERIOUS", "bb": 0},
            {"n": "MYSTERIOUS EGYPT", "bb": 0}, {"n": "PANDA'S FORTUNE", "bb": 0}, {"n": "PEKING LUCK", "bb": 0}, {"n": "PHOENIX FORGE", "bb": 0}, {"n": "PIXIE WINGS", "bb": 0}, {"n": "PYRAMID KING", "bb": 0},
            {"n": "QUEEN OF ATLANTIS", "bb": 0}, {"n": "QUEEN OF GOLD", "bb": 0}, {"n": "RELEASE THE KRAKEN", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "SANTA", "bb": 0}, {"n": "SCARAB QUEEN", "bb": 0},
            {"n": "SEVEN PIGGIES", "bb": 0}, {"n": "STAR BOUNTY", "bb": 0}, {"n": "STREET RACER", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "TEMPLAR TUMBLE", "bb": 0}, {"n": "THE CHAMPIONS", "bb": 0},
            {"n": "THE DOG HOUSE", "bb": 0}, {"n": "THE WILD MACHINE", "bb": 0}, {"n": "THREE STAR FORTUNE", "bb": 0}, {"n": "TREE OF RICHES", "bb": 0}, {"n": "TRIPLE DRAGONS", "bb": 0}, {"n": "TRIPLE JOKER", "bb": 0},
            {"n": "VAMPIRE VS WOLVES", "bb": 0}, {"n": "VEGAS MAGIC", "bb": 0}, {"n": "VEGAS NIGHTS", "bb": 0}, {"n": "VOODOO MAGIC", "bb": 0}, {"n": "WILD GLADIATORS", "bb": 0}, {"n": "WILD PIXIES", "bb": 0},
            {"n": "WILD SPELLS", "bb": 0}, {"n": "WILD WALKER", "bb": 0}, {"n": "WOLF GOLD", "bb": 0}
        ],
        "PG SOFT": [
            {"n": "MAHJONG WAYS", "bb": 0}, {"n": "MAHJONG WAYS 2", "bb": 0}, {"n": "LUCKY NEKO", "bb": 0}, {"n": "TREASURES OF AZTEC", "bb": 0}, {"n": "FORTUNE OX", "bb": 0}, {"n": "FORTUNE MOUSE", "bb": 0},
            {"n": "FORTUNE TIGER", "bb": 0}, {"n": "FORTUNE RABBIT", "bb": 0}, {"n": "FORTUNE DRAGON", "bb": 0}, {"n": "DRAGON HATCH", "bb": 0}, {"n": "DRAGON HATCH 2", "bb": 0}, {"n": "GATES OF GATOT KACA", "bb": 0},
            {"n": "CAISHEN WINS", "bb": 0}, {"n": "GANESHA GOLD", "bb": 0}, {"n": "WILD BANDITO", "bb": 0}, {"n": "WAYS OF THE QILIN", "bb": 0}, {"n": "DREAMS OF MACAU", "bb": 0}, {"n": "SUPERMARKET SPREE", "bb": 0},
            {"n": "ROYAL KATT", "bb": 0}, {"n": "CANDY BONANZA", "bb": 1}, {"n": "HEIST STAKES", "bb": 0}, {"n": "RISE OF APOLLO", "bb": 0}, {"n": "CRYPTO GOLD", "bb": 0}, {"n": "BALI VACATION", "bb": 0},
            {"n": "OPERA DYNASTY", "bb": 0}, {"n": "GUARDIANS OF ICE & FIRE", "bb": 0}, {"n": "JACK FROST'S WINTER", "bb": 0}, {"n": "GALACTIC GEMS", "bb": 0}, {"n": "JEWELS OF PROSPERITY", "bb": 0}, {"n": "QUEEN OF BOUNTY", "bb": 0},
            {"n": "VAMPIRE'S CHARM", "bb": 0}, {"n": "SECRET OF CLEOPATRA", "bb": 0}, {"n": "GENIE'S 3 WISHES", "bb": 0}, {"n": "CIRCUS DELIGHT", "bb": 0}, {"n": "DRAGON TIGER LUCK", "bb": 0}, {"n": "PHOENIX RISES", "bb": 0},
            {"n": "WILD FIREWORKS", "bb": 0}, {"n": "EGYPT'S BOOK OF MYSTERY", "bb": 0}, {"n": "CAPTAIN'S BOUNTY", "bb": 0}, {"n": "JOURNEY TO THE WEALTH", "bb": 0}, {"n": "GEM SAVIOUR", "bb": 0}, {"n": "GEM SAVIOUR SWORD", "bb": 0},
            {"n": "PIGGY GOLD", "bb": 0}, {"n": "JUNGLE DELIGHT", "bb": 0}, {"n": "THREE MONKEYS", "bb": 0}, {"n": "EMPEROR'S FAVOUR", "bb": 0}, {"n": "MUAY THAI CHAMPION", "bb": 0}, {"n": "THE GREAT ICESCAPE", "bb": 0},
            {"n": "LEPRECHAUN RICHES", "bb": 0}, {"n": "FLIRTING SCHOLAR", "bb": 0}, {"n": "NINJA VS SAMURAI", "bb": 0}, {"n": "DRAGON LEGEND", "bb": 0}, {"n": "SANTA'S GIFT RUSH", "bb": 0}, {"n": "BATTLEGROUND ROYALE", "bb": 0},
            {"n": "ROOSTER RUMBLE", "bb": 0}, {"n": "BUTTERFLY BLOSSOM", "bb": 0}, {"n": "LUCKY PIGGY", "bb": 0}, {"n": "PROSPERITY FORTUNE TREE", "bb": 0}, {"n": "TOTEM WONDERS", "bb": 0}, {"n": "ALCHEMY GOLD", "bb": 0},
            {"n": "MIDAS FORTUNE", "bb": 0}, {"n": "BAKERY BONANZA", "bb": 1}, {"n": "RAVE PARTY FEVER", "bb": 0}, {"n": "LUXURY GOODS", "bb": 0}, {"n": "MYSTICAL SPIRITS", "bb": 0}, {"n": "ULTIMATE STRIKER", "bb": 0},
            {"n": "PINATA WINS", "bb": 0}, {"n": "SAFARI WILDS", "bb": 0}, {"n": "WEREWOLF'S HUNT", "bb": 0}, {"n": "GLADIATOR'S GLORY", "bb": 0}, {"n": "CRUISE ROYALE", "bb": 0}, {"n": "THREE PIGLETS", "bb": 0},
            {"n": "SONGKRAN SPLASH", "bb": 0}, {"n": "HAWAIIAN TIKI", "bb": 0}, {"n": "SPIRITED WONDERS", "bb": 0}, {"n": "LEGEND OF PERSEUS", "bb": 0}, {"n": "ORIENTAL PROSPERITY", "bb": 0}, {"n": "MASK CARNIVAL", "bb": 0},
            {"n": "EMOJI RICHES", "bb": 0}, {"n": "FARM INVADERS", "bb": 0}, {"n": "DESTINY OF SUN & MOON", "bb": 0}, {"n": "MAJESTIC TREASURES", "bb": 0}, {"n": "CANDY BURST", "bb": 0}, {"n": "ASGARDIA", "bb": 0},
            {"n": "BIKINI PARADISE", "bb": 0}, {"n": "DOUBLE FORTUNE", "bb": 0}, {"n": "DRAGON TIGER LUCK", "bb": 0}, {"n": "GEM SAVIOUR CONQUEST", "bb": 0}, {"n": "HOOD VS WOLF", "bb": 0}, {"n": "HOTPOT", "bb": 0},
            {"n": "ICE SCAPE", "bb": 0}, {"n": "LEGEND OF HOU YI", "bb": 0}, {"n": "MEDUSA II", "bb": 0}, {"n": "MEDUSA", "bb": 0}, {"n": "MR. HALLOW-WIN", "bb": 0}, {"n": "PLUSHIE FRENZY", "bb": 0},
            {"n": "PROSPERITY LION", "bb": 0}, {"n": "REEL LOVE", "bb": 0}, {"n": "SANTA'S GIFT RUSH", "bb": 0}, {"n": "SHAOLIN SOCCER", "bb": 0}, {"n": "STEAMPUNK FORTUNE", "bb": 0}, {"n": "SYMBOLS OF EGYPT", "bb": 0},
            {"n": "THE GREAT ICESCAPE", "bb": 0}, {"n": "TREE OF FORTUNE", "bb": 0}, {"n": "WILD FIREWORKS", "bb": 0}, {"n": "WIN WIN WON", "bb": 0}
        ],
        "JILI": [
            {"n": "SUPER ACE", "bb": 0}, {"n": "SUPER ACE DELUXE", "bb": 0}, {"n": "GOLDEN EMPIRE", "bb": 0}, {"n": "GOLDEN EMPIRE 2", "bb": 0}, {"n": "FORTUNE GEMS", "bb": 0}, {"n": "FORTUNE GEMS 2", "bb": 0},
            {"n": "FORTUNE GEMS 3", "bb": 0}, {"n": "MONEY COMING", "bb": 0}, {"n": "MONEY COMING EXPAND", "bb": 0}, {"n": "BOXING KING", "bb": 0}, {"n": "ALI BABA", "bb": 0}, {"n": "MEGA ACE", "bb": 0},
            {"n": "MAGIC LAMP", "bb": 0}, {"n": "TWIN WINS", "bb": 0}, {"n": "FENG SHEN", "bb": 0}, {"n": "ROMA X", "bb": 0}, {"n": "ROMA X DELUXE", "bb": 0}, {"n": "CRAZY 777", "bb": 0},
            {"n": "GOLDEN QUEEN", "bb": 0}, {"n": "JUNGLE KING", "bb": 0}, {"n": "CHARGE BUFFALO", "bb": 0}, {"n": "CHARGE BUFFALO 2", "bb": 0}, {"n": "PHARAOH TREASURE", "bb": 0}, {"n": "BUBBLE BEAUTY", "bb": 0},
            {"n": "CANDY BABY", "bb": 0}, {"n": "NIGHT CITY", "bb": 0}, {"n": "SUPER RICH", "bb": 0}, {"n": "HAPPY TAXI", "bb": 0}, {"n": "WORLD CUP", "bb": 0}, {"n": "MAYAN EMPIRE", "bb": 0},
            {"n": "CHIN SHI HUANG", "bb": 0}, {"n": "GOLDEN BANK", "bb": 0}, {"n": "LUCKY GOLDBRICKS", "bb": 0}, {"n": "HYPER BURST", "bb": 0}, {"n": "PARTY NIGHT", "bb": 0}, {"n": "SEVEN SEVEN SEVEN", "bb": 0},
            {"n": "WAR OF DRAGONS", "bb": 0}, {"n": "AGENT ACE", "bb": 0}, {"n": "HOT CHILLI", "bb": 0}, {"n": "MEDUSA", "bb": 0}, {"n": "SECRET TREASURE", "bb": 0}, {"n": "TRIAL OF ADVERSITY", "bb": 0},
            {"n": "WILD PANDA", "bb": 0}, {"n": "BOOK OF GOLD", "bb": 0}, {"n": "GOD OF MARTIAL", "bb": 0}, {"n": "SAMURAI", "bb": 0}, {"n": "WILD RACER", "bb": 0}, {"n": "GOLDEN LAND", "bb": 0},
            {"n": "LUCKY LADY", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "CRAZY FA FA FA", "bb": 0}, {"n": "DRAGON & TIGER", "bb": 0}, {"n": "KA CHIN", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0},
            {"n": "WORLD CUP 2022", "bb": 0}, {"n": "GOLDEN JOKER", "bb": 0}, {"n": "JILI CAISHEN", "bb": 0}, {"n": "BOOK OF MYSTERY", "bb": 0}, {"n": "PIRATE QUEEN", "bb": 0}, {"n": "MONEY TREE", "bb": 0},
            {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD FOX", "bb": 0}, {"n": "CRAZY GOLDEN BANK", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "777", "bb": 0}, {"n": "ACE OF SPADES", "bb": 0},
            {"n": "BAO BOON CHIN", "bb": 0}, {"n": "BOXING KING", "bb": 0}, {"n": "CANDY BABY", "bb": 0}, {"n": "CHARGE BUFFALO", "bb": 0}, {"n": "CRAZY 777", "bb": 0}, {"n": "FENG SHEN", "bb": 0},
            {"n": "FORTUNE GEMS", "bb": 0}, {"n": "FORTUNE TREE", "bb": 0}, {"n": "GOLDEN EMPIRE", "bb": 0}, {"n": "GOLDEN QUEEN", "bb": 0}, {"n": "HOT CHILLI", "bb": 0}, {"n": "JUNGLE KING", "bb": 0},
            {"n": "LUCKY GOLDBRICKS", "bb": 0}, {"n": "MAGIC LAMP", "bb": 0}, {"n": "MEGA ACE", "bb": 0}, {"n": "MONEY COMING", "bb": 0}, {"n": "NIGHT CITY", "bb": 0}, {"n": "PARTY NIGHT", "bb": 0},
            {"n": "PHARAOH TREASURE", "bb": 0}, {"n": "ROMA X", "bb": 0}, {"n": "SEVEN SEVEN SEVEN", "bb": 0}, {"n": "SUPER ACE", "bb": 0}, {"n": "SUPER RICH", "bb": 0}, {"n": "TWIN WINS", "bb": 0},
            {"n": "WAR OF DRAGONS", "bb": 0}, {"n": "WORLD CUP", "bb": 0}
        ],
        "NOLIMIT CITY": [
            {"n": "SAN QUENTIN XWAYS", "bb": 0}, {"n": "MENTAL", "bb": 0}, {"n": "FIRE IN THE HOLE", "bb": 0}, {"n": "DAS XBOOT", "bb": 0}, {"n": "XWAYS HOARDER", "bb": 0}, {"n": "EAST COAST VS WEST COAST", "bb": 0},
            {"n": "PUNK ROCKER", "bb": 0}, {"n": "DEADWOOD", "bb": 0}, {"n": "TOMBSTONE", "bb": 0}, {"n": "TOMBSTONE RIP", "bb": 0}, {"n": "EL PASO GUNFIGHT", "bb": 0}, {"n": "BUSHIDO WAYS", "bb": 0},
            {"n": "INFECTIOUS 5", "bb": 0}, {"n": "WARRIOR GRAVEYARD", "bb": 0}, {"n": "BARBARIAN FURY", "bb": 0}, {"n": "DRAGON TRIBE", "bb": 0}, {"n": "GAELIC GOLD", "bb": 0}, {"n": "HARLEQUIN CARNIVAL", "bb": 0},
            {"n": "ICE ICE YETI", "bb": 0}, {"n": "KITCHEN DRAMA", "bb": 0}, {"n": "MANHATTAN GOES WILD", "bb": 0}, {"n": "MAYA MAGIC", "bb": 0}, {"n": "MILKY WAYS", "bb": 0}, {"n": "MONKEY'S GOLD", "bb": 0},
            {"n": "OWLS", "bb": 0}, {"n": "PIXIES VS PIRATES", "bb": 0}, {"n": "POISON EVE", "bb": 0}, {"n": "STARSTRUCK", "bb": 0}, {"n": "TESLA JOLT", "bb": 0}, {"n": "THE CREEPY CARNIVAL", "bb": 0},
            {"n": "THOR", "bb": 0}, {"n": "TRACTOR BEAM", "bb": 0}, {"n": "TURST YOURSELF", "bb": 0}, {"n": "WIXX", "bb": 0}, {"n": "HOT 4 CASH", "bb": 0}, {"n": "IMMORTAL FRUITS", "bb": 0},
            {"n": "BOOK OF SHADOWS", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "TOMB OF NEFERTITI", "bb": 0}, {"n": "TOMB OF AKHENATEN", "bb": 0}, {"n": "FOXY WILD HEART", "bb": 0}, {"n": "EVIL GOBLINS", "bb": 0},
            {"n": "LEGION X", "bb": 0}, {"n": "TRUE GRIT REDEMPTION", "bb": 0}, {"n": "MISERY MINING", "bb": 0}, {"n": "REMEMBER GULAG", "bb": 0}, {"n": "KAREN MANEATER", "bb": 0}, {"n": "THE RAVE", "bb": 0},
            {"n": "ROAD RAGE", "bb": 0}, {"n": "NINE TO FIVE", "bb": 0}, {"n": "DEVIL'S CROSSROAD", "bb": 0}, {"n": "D-DAY", "bb": 0}, {"n": "POSSESSED", "bb": 0}, {"n": "KENNY'S BEST", "bb": 0},
            {"n": "LAND OF THE FREE", "bb": 0}, {"n": "BRICK SNAKE 2000", "bb": 0}, {"n": "FIRE IN THE HOLE 2", "bb": 0}, {"n": "WHACKED!", "bb": 0}, {"n": "BLOOD & SHADOW", "bb": 0}, {"n": "DISTURBED", "bb": 0},
            {"n": "KISS MY CHAINS", "bb": 0}, {"n": "BENJI KILLED IN VEGAS", "bb": 0}, {"n": "WALK OF SHAME", "bb": 0}, {"n": "THE CAGE", "bb": 0}, {"n": "GLUTTONY", "bb": 0}, {"n": "THE CRYPT", "bb": 0},
            {"n": "DJ PSYCHO", "bb": 0}, {"n": "SERIAL", "bb": 0}, {"n": "PEARL HARBOR", "bb": 0}, {"n": "DEAD CANARY", "bb": 0}, {"n": "FOLSOM PRISON", "bb": 0}, {"n": "THE SHADOW ORDER", "bb": 0},
            {"n": "WOLF RITUAL", "bb": 0}, {"n": "DRAGON TRIBE", "bb": 0}, {"n": "MANHATTAN GOES WILD", "bb": 0}, {"n": "MAYA MAGIC", "bb": 0}, {"n": "POISON EVE", "bb": 0}
        ],
        "MICROGAMING": [
            {"n": "MEGA MOOLAH", "bb": 0}, {"n": "IMMORTAL ROMANCE", "bb": 0}, {"n": "THUNDERSTRUCK II", "bb": 0}, {"n": "9 MASKS OF FIRE", "bb": 0}, {"n": "BREAK DA BANK AGAIN", "bb": 0}, {"n": "JURASSIC PARK", "bb": 0},
            {"n": "GAME OF THRONES", "bb": 0}, {"n": "AVALON II", "bb": 0}, {"n": "BOOK OF OZ", "bb": 0}, {"n": "WHEEL OF WISHES", "bb": 0}, {"n": "ADVENTURE PALACE", "bb": 0}, {"n": "AGENT JANE BLONDE", "bb": 0},
            {"n": "ARIANA", "bb": 0}, {"n": "BIG BAD WOLF", "bb": 0}, {"n": "BUST THE BANK", "bb": 0}, {"n": "CARNAVAL", "bb": 0}, {"n": "COOL BUCK", "bb": 0}, {"n": "DECK THE HALLS", "bb": 0},
            {"n": "DRAGONZ", "bb": 0}, {"n": "EAGLE'S WINGS", "bb": 0}, {"n": "EMPEROR OF THE SEA", "bb": 0}, {"n": "FOOTBALL STAR", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "FORTUNIUM", "bb": 0},
            {"n": "GIRLS WITH GUNS", "bb": 0}, {"n": "GOLD FACTORY", "bb": 0}, {"n": "HALLOWEEN", "bb": 0}, {"n": "HAPPY HOLIDAYS", "bb": 0}, {"n": "HELLBOY", "bb": 0}, {"n": "HIGHLANDER", "bb": 0},
            {"n": "HITMAN", "bb": 0}, {"n": "HOT INK", "bb": 0}, {"n": "JUNGLE JIM EL DORADO", "bb": 0}, {"n": "KATHMANDU", "bb": 0}, {"n": "KINGS OF CASH", "bb": 0}, {"n": "LADIES NITE", "bb": 0},
            {"n": "LARA CROFT", "bb": 0}, {"n": "LOADED", "bb": 0}, {"n": "LOST VEGAS", "bb": 0}, {"n": "LUCKY LEPRECHAUN", "bb": 0}, {"n": "LUCKY ZODIAC", "bb": 0}, {"n": "PLAYBOY", "bb": 0},
            {"n": "PRETTY KITTY", "bb": 0}, {"n": "PURE PLATINUM", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "TERMINATOR 2", "bb": 0}, {"n": "TOMB RAIDER", "bb": 0}, {"n": "TREASURE NILE", "bb": 0},
            {"n": "WAXY VAN GOGH", "bb": 0}, {"n": "WICKED TALES", "bb": 0}, {"n": "WILD SCARABS", "bb": 0}, {"n": "WOLF HOWL", "bb": 0}, {"n": "AMAZING LINK ZEUS", "bb": 0}, {"n": "ANCIENT FORTUNES: ZEUS", "bb": 0},
            {"n": "ASSASSIN MOON", "bb": 0}, {"n": "AURUM CODEX", "bb": 0}, {"n": "BANANA ODYSSEY", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "BEAUTIFUL BONES", "bb": 0}, {"n": "BIG KAHUNA", "bb": 0},
            {"n": "5 REEL DRIVE", "bb": 0}, {"n": "777 ROYAL WHEEL", "bb": 0}, {"n": "A DARK MATTER", "bb": 0}, {"n": "ABSALOOTLY MAD", "bb": 0}, {"n": "AFRICAN QUEST", "bb": 0}, {"n": "AGE OF CONQUEST", "bb": 0},
            {"n": "ALCHEMISTS GOLD", "bb": 0}, {"n": "ALL WIN FC", "bb": 0}, {"n": "AMAZING LINK APOLLO", "bb": 0}, {"n": "ANCIENT FORTUNES: POSEIDON", "bb": 0}, {"n": "ARENA OF GOLD", "bb": 0}, {"n": "ARTHUR'S FORTUNE", "bb": 0},
            {"n": "ATLANTIS RISING", "bb": 0}, {"n": "AURORA WILD", "bb": 0}, {"n": "AZTEC FALLS", "bb": 0}, {"n": "BAR BAR BLACK SHEEP", "bb": 0}, {"n": "BEACH BABES", "bb": 0}, {"n": "BELIEVE IT OR NOT", "bb": 0},
            {"n": "BIG TOP", "bb": 0}, {"n": "BOOK OF ATEM", "bb": 0}, {"n": "BOOK OF CAPTAIN SILVER", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "BOOM PIRATES", "bb": 0}, {"n": "BREAK AWAY", "bb": 0},
            {"n": "BREAK AWAY LUCKY WILDS", "bb": 0}, {"n": "BULLSEYE", "bb": 0}, {"n": "BURNING DESIRE", "bb": 0}, {"n": "BUSH TELEGRAPH", "bb": 0}, {"n": "CASH OF KINGDOMS", "bb": 0}, {"n": "CASH SPLASH", "bb": 0},
            {"n": "CASHVILLE", "bb": 0}, {"n": "CAT IN VEGAS", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CENTURION", "bb": 0}, {"n": "CHICAGO GOLD", "bb": 0}
        ],
        "BNG (BOOONGO)": [
            {"n": "SUN OF EGYPT", "bb": 0}, {"n": "SUN OF EGYPT 2", "bb": 0}, {"n": "SUN OF EGYPT 3", "bb": 0}, {"n": "SUN OF EGYPT 4", "bb": 0}, {"n": "15 DRAGON PEARLS", "bb": 0}, {"n": "DRAGON PEARLS", "bb": 0},
            {"n": "MAGIC APPLE", "bb": 0}, {"n": "MAGIC APPLE 2", "bb": 0}, {"n": "TIGER JUNGLE", "bb": 0}, {"n": "HIT THE GOLD", "bb": 0}, {"n": "BLACK WOLF", "bb": 0}, {"n": "BLACK WOLF 2", "bb": 0},
            {"n": "AZTEC SUN", "bb": 0}, {"n": "GREAT PANDA", "bb": 0}, {"n": "MOON SISTERS", "bb": 0}, {"n": "BUDDHA FORTUNE", "bb": 0}, {"n": "SCARAB TEMPLE", "bb": 0}, {"n": "3 COINS", "bb": 0},
            {"n": "3 COINS EGYPT", "bb": 0}, {"n": "3 HOT CHILLIES", "bb": 0}, {"n": "WUKONG", "bb": 0}, {"n": "WOLF SAGA", "bb": 0}, {"n": "QUEEN OF THE SUN", "bb": 0}, {"n": "GOLD EXPRESS", "bb": 0},
            {"n": "CANDY BOOM", "bb": 0}, {"n": "GIE GIE GIE", "bb": 0}, {"n": "LOTUS CHARM", "bb": 0}, {"n": "ORCHID PRINCESS", "bb": 1}, {"n": "TIGER STONE", "bb": 0}, {"n": "SUPER RICH GOD", "bb": 0},
            {"n": "EYE OF GOLD", "bb": 0}, {"n": "BOOK OF SUN", "bb": 0}, {"n": "BOOK OF SUN MULTICHANCE", "bb": 0}, {"n": "GOD'S TEMPLE", "bb": 0}, {"n": "OLYMPIAN GODS", "bb": 0}, {"n": "POISONED APPLE", "bb": 0},
            {"n": "POISONED APPLE 2", "bb": 0}, {"n": "777 GEMS", "bb": 0}, {"n": "SUPREME HOT", "bb": 0}, {"n": "STAR GEMS", "bb": 0}, {"n": "SKY GEMS", "bb": 0}, {"n": "GREEN CHILLI", "bb": 0},
            {"n": "GREEN CHILLI 2", "bb": 0}, {"n": "MORE MAGIC APPLE", "bb": 0}, {"n": "OIAO MEI", "bb": 0}, {"n": "COIN VOLCANO", "bb": 0}, {"n": "EGYPT FIRE", "bb": 0}, {"n": "RIO GEMS", "bb": 0},
            {"n": "HIT MORE GOLD", "bb": 0}, {"n": "STICKY PIGGY", "bb": 0}, {"n": "GODDESS OF EGYPT", "bb": 0}, {"n": "BOOM! BOOM! GOLD!", "bb": 0}, {"n": "AZTEC SUN", "bb": 0}, {"n": "BOOK OF SUN", "bb": 0},
            {"n": "BUDDHA FORTUNE", "bb": 0}, {"n": "DRAGON PEARLS", "bb": 0}, {"n": "EYE OF GOLD", "bb": 0}, {"n": "GOD'S TEMPLE", "bb": 0}, {"n": "GREAT PANDA", "bb": 0}, {"n": "MAGIC APPLE", "bb": 0},
            {"n": "MOON SISTERS", "bb": 0}, {"n": "OLYMPIAN GODS", "bb": 0}, {"n": "POISONED APPLE", "bb": 0}, {"n": "SCARAB TEMPLE", "bb": 0}, {"n": "SUN OF EGYPT", "bb": 0}, {"n": "TIGER STONE", "bb": 0},
            {"n": "WOLF SAGA", "bb": 0}
        ],
        "BIGPOT GAMING": [
            {"n": "GOLDEN ERA", "bb": 0}, {"n": "SECRET OF RICHES", "bb": 0}, {"n": "LUCKY SEVEN", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}, {"n": "PIRATE KING", "bb": 0}, {"n": "DRAGON LEGEND", "bb": 0},
            {"n": "MAGIC FOREST", "bb": 0}, {"n": "CANDY POP", "bb": 0}, {"n": "NEON CITY", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0}, {"n": "VIKING GLORY", "bb": 0},
            {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "HERCULES", "bb": 0},
            {"n": "ZOMBIE ATTACK", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "CHRISTMAS JOY", "bb": 0}, {"n": "LUCKY FARM", "bb": 0}, {"n": "CASINO ROYALE", "bb": 0}, {"n": "NINJA SQUAD", "bb": 0},
            {"n": "ROBOT WARS", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0}, {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "RACING STARS", "bb": 0},
            {"n": "FRUIT SPLASH", "bb": 0}, {"n": "DIAMOND RUSH", "bb": 0}, {"n": "PANDA WARRIOR", "bb": 0}, {"n": "SKY GUARDIAN", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "WILD SAFARI", "bb": 0},
            {"n": "MAGIC SPELL", "bb": 0}, {"n": "LUCKY DICE", "bb": 0}, {"n": "GOLDEN RUSH", "bb": 0}, {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "CANDY POP", "bb": 0},
            {"n": "CASINO ROYALE", "bb": 0}, {"n": "DRAGON LEGEND", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "FRUIT SPLASH", "bb": 0},
            {"n": "GOLDEN ERA", "bb": 0}, {"n": "GOLDEN RUSH", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "HERCULES", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0},
            {"n": "LUCKY FARM", "bb": 0}, {"n": "LUCKY SEVEN", "bb": 0}, {"n": "MAGIC FOREST", "bb": 0}, {"n": "MAGIC SPELL", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "NEON CITY", "bb": 0},
            {"n": "NINJA SQUAD", "bb": 0}, {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "PIRATE KING", "bb": 0}, {"n": "RACING STARS", "bb": 0}, {"n": "ROBOT WARS", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0},
            {"n": "SECRET OF RICHES", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "VIKING GLORY", "bb": 0}, {"n": "WILD SAFARI", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}
        ],
        "HACKSAW GAMING": [
            {"n": "WANTED DEAD OR A WILD", "bb": 0}, {"n": "CHAOS CREW", "bb": 0}, {"n": "CHAOS CREW II", "bb": 0}, {"n": "HAND OF ANUBIS", "bb": 0}, {"n": "RIP CITY", "bb": 0}, {"n": "LE BANDIT", "bb": 0},
            {"n": "DORK UNIT", "bb": 0}, {"n": "STACK 'EM", "bb": 0}, {"n": "STICK 'EM", "bb": 0}, {"n": "TOSHI VIDEO CLUB", "bb": 0}, {"n": "DROP 'EM", "bb": 0}, {"n": "ROTTEN", "bb": 0},
            {"n": "GLADIATOR LEGENDS", "bb": 0}, {"n": "STORMFORGED", "bb": 0}, {"n": "THE BOWERY BOYS", "bb": 0}, {"n": "PUG LIFE", "bb": 0}, {"n": "ITERCH", "bb": 0}, {"n": "KING CARROT", "bb": 0},
            {"n": "JOKER BOMBS", "bb": 0}, {"n": "CUBES", "bb": 0}, {"n": "CUBES 2", "bb": 0}, {"n": "DOUBLE RAINBOW", "bb": 0}, {"n": "TASTY TREATS", "bb": 0}, {"n": "XPW", "bb": 0},
            {"n": "UNDEA FORTUNE", "bb": 0}, {"n": "FEAR THE DARK", "bb": 0}, {"n": "BEAST BELOW", "bb": 0}, {"n": "SLAYERS INC", "bb": 0}, {"n": "DARK SUMMONING", "bb": 0}, {"n": "BENNY THE BEER", "bb": 0},
            {"n": "2 WILD 2 DIE", "bb": 0}, {"n": "FEEL THE BEAT", "bb": 0}, {"n": "FIST OF DESTRUCTION", "bb": 0}, {"n": "DIVINE DROP", "bb": 0}, {"n": "RUSTY & CURLY", "bb": 0}, {"n": "CASH CREW", "bb": 0},
            {"n": "BEAM BOYS", "bb": 0}, {"n": "BARBARIAN STASH", "bb": 0}, {"n": "JAGGED STONES", "bb": 0}, {"n": "SIXSIXSIX", "bb": 0}, {"n": "OMICRON", "bb": 0}, {"n": "HOP'N'POP", "bb": 0},
            {"n": "FRUIT DUEL", "bb": 0}, {"n": "BORN WILD", "bb": 0}, {"n": "FOREST FORTUNE", "bb": 0}, {"n": "HARVEST WILD", "bb": 0}, {"n": "AZTEC TWIST", "bb": 0}, {"n": "MYSTERY MOTEL", "bb": 0},
            {"n": "SCRATCH BRONZE", "bb": 0}, {"n": "SCRATCH PLATINUM", "bb": 0}, {"n": "ALPHA EAGLE", "bb": 0}, {"n": "BLOODTHIRST", "bb": 0}, {"n": "BREAK BONES", "bb": 0}, {"n": "CASH QUEST", "bb": 0},
            {"n": "CASH-A-CABANA", "bb": 0}, {"n": "CAT CLANS", "bb": 0}, {"n": "DORK UNIT", "bb": 0}, {"n": "DOUBLE RAINBOW", "bb": 0}, {"n": "EGGSTRAVAGANZA", "bb": 0}, {"n": "EYE OF THE PANDA", "bb": 0},
            {"n": "FRUIT DUEL", "bb": 0}, {"n": "GLADIATOR LEGENDS", "bb": 0}, {"n": "HAND OF ANUBIS", "bb": 0}, {"n": "HARVEST WILD", "bb": 0}, {"n": "HOP'N'POP", "bb": 0}, {"n": "ITERERO", "bb": 0},
            {"n": "JELLY REELS", "bb": 0}, {"n": "KING CARROT", "bb": 0}, {"n": "POCKET ROCKETS", "bb": 0}, {"n": "PUG LIFE", "bb": 0}, {"n": "RIP CITY", "bb": 0}, {"n": "ROTTEN", "bb": 0},
            {"n": "STACK 'EM", "bb": 0}, {"n": "STICK 'EM", "bb": 0}, {"n": "TOSHI VIDEO CLUB", "bb": 0}, {"n": "WANTED DEAD OR A WILD", "bb": 0}, {"n": "WARRIOR WAYS", "bb": 0}, {"n": "WILD YIELD", "bb": 0},
            {"n": "XPW", "bb": 0}
        ],
        "FA CHAI": [
            {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHINESE NEW YEAR 2", "bb": 0}, {"n": "NIGHT MARKET", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "MAGIC BEANS", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0},
            {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "ANIMAL RACING", "bb": 0}, {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "LEGEND OF DRAGON", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0},
            {"n": "GRAND BLUE", "bb": 0}, {"n": "TREASURE CRUISE", "bb": 0}, {"n": "GLORY OF ROME", "bb": 0}, {"n": "RICH MAN", "bb": 0}, {"n": "LUCKY CLOVER", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0},
            {"n": "GOLDEN DRAGON", "bb": 0}, {"n": "KA-CHING", "bb": 0}, {"n": "PONG PONG HU", "bb": 0}, {"n": "MAHJONG WAYS 3", "bb": 0}, {"n": "FORTUNE GOD", "bb": 0}, {"n": "LUCKY WHEEL", "bb": 0},
            {"n": "DISCO NIGHT", "bb": 0}, {"n": "ANIMAL RACING", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "GOLDEN GENIE", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0}, {"n": "GRAND BLUE", "bb": 0}, {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0}, {"n": "LEGEND OF DRAGON", "bb": 0},
            {"n": "LUCKY CLOVER", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0}, {"n": "MAGIC BEANS", "bb": 0}, {"n": "NIGHT MARKET", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0},
            {"n": "RICH MAN", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0}, {"n": "TREASURE CRUISE", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}
        ],
        "JDB GAMING": [
            {"n": "BURGER SHOP", "bb": 0}, {"n": "KONGFU", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0}, {"n": "LUCKY 7", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0},
            {"n": "DRAGON MASTER", "bb": 0}, {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "KINGSMAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0},
            {"n": "FORMOSA BEAR", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0},
            {"n": "OPEN SESAME", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "MAHJONG", "bb": 0}, {"n": "BANANA SAGA", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "ZODIAC", "bb": 0},
            {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD WEST", "bb": 0}, {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "CRAZY SCIENTIST", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0},
            {"n": "MAGIC WORLD", "bb": 0}, {"n": "WONDERLAND", "bb": 0}, {"n": "HALLOWEEN PARTY", "bb": 0}, {"n": "CHRISTMAS SURPRISE", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0},
            {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "BURGER SHOP", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "DRAGON MASTER", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0},
            {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "FORMOSA BEAR", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "KONGFU", "bb": 0},
            {"n": "LUCKY 7", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "MAHJONG", "bb": 0},
            {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "OPEN SESAME", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "TREASURE BOWL", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "ZODIAC", "bb": 0}
        ],
        "PLAY'N GO": [
            {"n": "BOOK OF DEAD", "bb": 0}, {"n": "REACTOONZ", "bb": 0}, {"n": "REACTOONZ 2", "bb": 0}, {"n": "MOON PRINCESS", "bb": 1}, {"n": "MOON PRINCESS 100", "bb": 1}, {"n": "MOON PRINCESS TRINITY", "bb": 1},
            {"n": "RISE OF OLYMPUS", "bb": 0}, {"n": "RISE OF OLYMPUS 100", "bb": 0}, {"n": "GEMIX", "bb": 0}, {"n": "GEMIX 2", "bb": 0}, {"n": "FIRE JOKER", "bb": 0}, {"n": "LEGACY OF DEAD", "bb": 0},
            {"n": "TOME OF MADNESS", "bb": 0}, {"n": "HONEY RUSH", "bb": 0}, {"n": "HONEY RUSH 100", "bb": 0}, {"n": "GOLDEN TICKET", "bb": 0}, {"n": "GOLDEN TICKET 2", "bb": 0}, {"n": "SWEET ALCHEMY", "bb": 0},
            {"n": "SWEET ALCHEMY 2", "bb": 0}, {"n": "RISE OF MERLIN", "bb": 0}, {"n": "PIMPED", "bb": 0}, {"n": "XMAS JOKER", "bb": 0}, {"n": "MYSTERY JOKER", "bb": 0}, {"n": "BIG WIN CAT", "bb": 0},
            {"n": "HOT TO BURN", "bb": 0}, {"n": "BOAT BONANZA", "bb": 1}, {"n": "CLASH OF CAMELOT", "bb": 0}, {"n": "COUNT JOKULA", "bb": 0}, {"n": "DIO KILLING THE DRAGON", "bb": 0}, {"n": "CHAMPS-ELYSEES", "bb": 0},
            {"n": "CANINE CARNAGE", "bb": 0}, {"n": "USA FLIP", "bb": 0}, {"n": "SHAMROCK MINER", "bb": 0}, {"n": "WILD FALLS 2", "bb": 0}, {"n": "GRIM THE SPLITTER", "bb": 0}, {"n": "LEGACY OF INCA", "bb": 0},
            {"n": "GAME OF GLADIATORS", "bb": 0}, {"n": "SAFARI OF WEALTH", "bb": 0}, {"n": "CAT WILDE", "bb": 0}, {"n": "RICH WILDE", "bb": 0}, {"n": "AGENT DESTINY", "bb": 0}, {"n": "ANCIENT EGYPT", "bb": 0},
            {"n": "ANNIHILATOR", "bb": 0}, {"n": "AZTEC IDOLS", "bb": 0}, {"n": "AZTEC WARRIOR PRINCESS", "bb": 1}, {"n": "BAKER'S TREAT", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "7 SINS", "bb": 0},
            {"n": "ACE OF SPADES", "bb": 0}, {"n": "AGENT DESTINY", "bb": 0}, {"n": "ANCIENT EGYPT", "bb": 0}, {"n": "ANNIHILATOR", "bb": 0}, {"n": "AZTEC IDOLS", "bb": 0}, {"n": "AZTEC WARRIOR PRINCESS", "bb": 1},
            {"n": "BAKER'S TREAT", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "BEAST OF WEALTH", "bb": 0}, {"n": "BELL OF FORTUNE", "bb": 0}, {"n": "BIG WIN 777", "bb": 0}, {"n": "BIG WIN CAT", "bb": 0},
            {"n": "BLACK MAMBA", "bb": 0}, {"n": "BLAZIN' BULLFROG", "bb": 0}, {"n": "BOOK OF DEAD", "bb": 0}, {"n": "BULL IN A CHINA SHOP", "bb": 0}, {"n": "CASH PUMP", "bb": 0}, {"n": "CASH VANDAL", "bb": 0},
            {"n": "CAT WILDE", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CHAMPS-ELYSEES", "bb": 0}, {"n": "CHARLIE CHANCE", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHRONOS JOKER", "bb": 0},
            {"n": "CLASH OF CAMELOT", "bb": 0}, {"n": "CLOUD QUEST", "bb": 0}, {"n": "COPS 'N' ROBBERS", "bb": 0}, {"n": "COUNT JOKULA", "bb": 0}, {"n": "COURT OF HEARTS", "bb": 0}, {"n": "COYOTE CASH", "bb": 0},
            {"n": "CRYSTAL SUN", "bb": 0}, {"n": "DAWN OF EGYPT", "bb": 0}, {"n": "DEADLY 5", "bb": 0}, {"n": "DEMON", "bb": 0}, {"n": "DERBY WHEEL", "bb": 0}, {"n": "DIAMOND VORTEX", "bb": 0},
            {"n": "DIO KILLING THE DRAGON", "bb": 0}, {"n": "DIVINE SHOWDOWN", "bb": 0}, {"n": "DOOM OF EGYPT", "bb": 0}, {"n": "DRAGON MAIDEN", "bb": 0}, {"n": "DRAGON SHIP", "bb": 0}, {"n": "EASTER EGGS", "bb": 0},
            {"n": "EGYPTIAN FORTUNE", "bb": 0}, {"n": "ENERGOONZ", "bb": 0}, {"n": "EYE OF THE ATUM", "bb": 0}, {"n": "FACES OF FREYA", "bb": 0}, {"n": "FIRE JOKER", "bb": 0}, {"n": "FIRE JOKER FREEZE", "bb": 0},
            {"n": "FIRE TOAD", "bb": 0}, {"n": "FORGE OF FORTUNES", "bb": 0}, {"n": "FORTUNE REWIND", "bb": 0}, {"n": "FROZEN GEMS", "bb": 0}, {"n": "GAME OF GLADIATORS", "bb": 0}, {"n": "GEMIX", "bb": 0},
            {"n": "GHOST OF DEAD", "bb": 0}, {"n": "GIGANTUANZ", "bb": 0}, {"n": "GOLD KING", "bb": 0}, {"n": "GOLD TROPHY 2", "bb": 0}, {"n": "GOLD VOLCANO", "bb": 0}, {"n": "GOLDEN TICKET", "bb": 0},
            {"n": "GRIM THE SPLITTER", "bb": 0}, {"n": "GUNSLINGER", "bb": 0}, {"n": "HALLOWEEN JACK", "bb": 0}, {"n": "HAPPY HALLOWEEN", "bb": 0}, {"n": "HOLIDAY SPIRITS", "bb": 0}, {"n": "HONEY RUSH", "bb": 0},
            {"n": "HOT TO BURN", "bb": 0}, {"n": "HOTEL YETI-WAY", "bb": 0}, {"n": "HOUSE OF DOOM", "bb": 0}, {"n": "HUGO", "bb": 0}, {"n": "HUGO 2", "bb": 0}, {"n": "ICE JOKER", "bb": 0},
            {"n": "IDOL OF FORTUNE", "bb": 0}, {"n": "IMMORTAL GUILD", "bb": 0}, {"n": "INFERNO STAR", "bb": 0}, {"n": "IRON GIRL", "bb": 0}, {"n": "ISHIN", "bb": 0}, {"n": "IT'S MAGIC", "bb": 0},
            {"n": "JACKPOT POKER", "bb": 0}, {"n": "JADE MAGICIAN", "bb": 0}, {"n": "JEWEL BOX", "bb": 0}, {"n": "JOLLY ROGER", "bb": 0}, {"n": "JOLLY ROGER 2", "bb": 0}, {"n": "KISS REELS OF ROCK", "bb": 0},
            {"n": "KNIGHT'S LIFE", "bb": 0}, {"n": "KRAKEN'S SKY", "bb": 0}, {"n": "LADY OF FORTUNE", "bb": 0}, {"n": "LEGACY OF DEAD", "bb": 0}, {"n": "LEGACY OF EGYPT", "bb": 0}, {"n": "LEGACY OF INCA", "bb": 0},
            {"n": "LEPRECHAUN GOES EGYPT", "bb": 0}, {"n": "LEPRECHAUN GOES HELL", "bb": 0}, {"n": "LEPRECHAUN GOES TO WILD", "bb": 0}, {"n": "LORD MERLIN", "bb": 0}, {"n": "LOVE IS IN THE AIR", "bb": 0}, {"n": "LUCKY DIAMONDS", "bb": 0},
            {"n": "MADAME DESTINY", "bb": 0}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "MAGICAL STACKS", "bb": 0}, {"n": "MAHJONG 88", "bb": 0}, {"n": "METAL DETECTOR", "bb": 0}, {"n": "MOON PRINCESS", "bb": 1},
            {"n": "MOON PRINCESS 100", "bb": 1}, {"n": "MOON PRINCESS TRINITY", "bb": 1}, {"n": "MOUNTAIN OF WEALTH", "bb": 0}, {"n": "MUERTO EN MITLAN", "bb": 0}, {"n": "MULTIFRUIT 81", "bb": 0}, {"n": "MYSTERY JOKER", "bb": 0},
            {"n": "MYSTERY JOKER 6000", "bb": 0}, {"n": "NINJA FRUITS", "bb": 0}, {"n": "NYX", "bb": 0}, {"n": "OCTOPUS TREASURE", "bb": 0}, {"n": "ODIN: PROTECTOR OF REALMS", "bb": 0}, {"n": "PAPYRUS", "bb": 0},
            {"n": "PEARLS OF INDIA", "bb": 0}, {"n": "PERFECT GEMS", "bb": 0}, {"n": "PHOENIX REBORN", "bb": 0}, {"n": "PIGGY BANK", "bb": 0}, {"n": "PIMPED", "bb": 0}, {"n": "PIXIES VS PIRATES", "bb": 0},
            {"n": "PLANET FORTUNE", "bb": 0}, {"n": "PROSPERITY PALACE", "bb": 0}, {"n": "QUEEN'S DAY TILT", "bb": 0}, {"n": "RABBIT HOLE RICHES", "bb": 0}, {"n": "RAGING REX", "bb": 0}, {"n": "RAGING REX 2", "bb": 0},
            {"n": "RAINBOW CHARMS", "bb": 0}, {"n": "REACTOONZ", "bb": 0}, {"n": "REACTOONZ 2", "bb": 0}, {"n": "REEL STEAL", "bb": 0}, {"n": "RICH WILDE", "bb": 0}, {"n": "RISE OF DEAD", "bb": 0},
            {"n": "RISE OF MERLIN", "bb": 0}, {"n": "RISE OF OLYMPUS", "bb": 0}, {"n": "RISE OF OLYMPUS 100", "bb": 0}, {"n": "RITUAL RESURRECTION", "bb": 0}, {"n": "ROCCO GALLO", "bb": 0}, {"n": "ROCK-N-ROLLA", "bb": 0},
            {"n": "RONIN", "bb": 0}, {"n": "ROYAL MASQUERADE", "bb": 0}, {"n": "SABATON", "bb": 0}, {"n": "SAFARI OF WEALTH", "bb": 0}, {"n": "SAILS OF GOLD", "bb": 0}, {"n": "SAMURAI KEN", "bb": 0},
            {"n": "SECRET OF THE STONES", "bb": 0}, {"n": "SHAMROCK MINER", "bb": 0}, {"n": "SINS", "bb": 0}, {"n": "SMILEY'S", "bb": 0}, {"n": "SPACE RACE", "bb": 0}, {"n": "SPARKY & SHORTZ", "bb": 0},
            {"n": "SPEED CASH", "bb": 0}, {"n": "STAR BLAST", "bb": 0}, {"n": "STICKY JOKER", "bb": 0}, {"n": "STREET MAGIC", "bb": 0}, {"n": "SUPER FLIP", "bb": 0}, {"n": "SWEET ALCHEMY", "bb": 0},
            {"n": "SWEET ALCHEMY 2", "bb": 0}, {"n": "SWORD AND THE GRAIL", "bb": 0}, {"n": "TALES OF ASGARD", "bb": 0}, {"n": "TEMPLE OF WEALTH", "bb": 0}, {"n": "TESTAMENT", "bb": 0}, {"n": "THAT'S RICH", "bb": 0},
            {"n": "THE LAST SUNDOWN", "bb": 0}, {"n": "THE SWORD AND THE GRAIL", "bb": 0}, {"n": "THUNDER SCREECH", "bb": 0}, {"n": "TOME OF MADNESS", "bb": 0}, {"n": "TWISTED SISTER", "bb": 0}, {"n": "USA FLIP", "bb": 0},
            {"n": "VIKING RUNECRAFT", "bb": 0}, {"n": "WILD BLOOD", "bb": 0}, {"n": "WILD BLOOD 2", "bb": 0}, {"n": "WILD FALLS", "bb": 0}, {"n": "WILD FALLS 2", "bb": 0}, {"n": "WILD FRAMES", "bb": 0},
            {"n": "WILD MELON", "bb": 0}, {"n": "WILD NORTH", "bb": 0}, {"n": "WIN-A-BEEST", "bb": 0}, {"n": "XMAS JOKER", "bb": 0}, {"n": "XMAS MAGIC", "bb": 0}
        ]
}

PROVIDERS_DATA_2 = {
        "PRAGMATIC PLAY": [
            {"n": "STARLIGHT PRINCESS Super Scatter ", "bb": 1}, {"n": "GATES OF OLYMPUS Super Scatter ", "bb": 0}, {"n": "GATES OF OLYMPUS", "bb": 0}, {"n": "GATES OF OLYMPUS 1000", "bb": 1}, {"n": "SWEET BONANZA", "bb": 1}, {"n": "SWEET BONANZA 1000", "bb": 1},
            {"n": "SUGAR RUSH", "bb": 0}, {"n": "SUGAR RUSH 1000", "bb": 1}, {"n": "STARLIGHT PRINCESS", "bb": 1}, {"n": "STARLIGHT PRINCESS 1000", "bb": 1}, {"n": "BIG BASS BONANZA", "bb": 1}, {"n": "BIG BASS SPLASH", "bb": 0},
            {"n": "BIG BASS AMAZON XTREME", "bb": 0}, {"n": "BIG BASS FLOATS MY BOAT", "bb": 0}, {"n": "THE DOG HOUSE", "bb": 0}, {"n": "THE DOG HOUSE MEGAWAYS", "bb": 1}, {"n": "THE DOG HOUSE MULTIHOLD", "bb": 0}, {"n": "FRUIT PARTY", "bb": 0},
            {"n": "FRUIT PARTY 2", "bb": 0}, {"n": "WOLF GOLD", "bb": 0}, {"n": "MUSTANG GOLD", "bb": 0}, {"n": "GREAT RHINO MEGAWAYS", "bb": 1}, {"n": "JOHN HUNTER & THE TOMB", "bb": 0}, {"n": "CHILLI HEAT", "bb": 0},
            {"n": "AZTEC GEMS", "bb": 0}, {"n": "AZTEC GEMS DELUXE", "bb": 0}, {"n": "WILD WEST GOLD", "bb": 0}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "THE HAND OF MIDAS", "bb": 0}, {"n": "POWER OF THOR MEGAWAYS", "bb": 1},
            {"n": "BUFFALO KING", "bb": 0}, {"n": "BUFFALO KING MEGAWAYS", "bb": 1}, {"n": "JUICY FRUITS", "bb": 0}, {"n": "GEMS BONANZA", "bb": 1}, {"n": "RISE OF GIZA", "bb": 0}, {"n": "CHICKEN DROP", "bb": 0},
            {"n": "BOOK OF FALLEN", "bb": 0}, {"n": "MAGICIAN'S SECRETS", "bb": 0}, {"n": "CRYSTAL CAVERNS", "bb": 0}, {"n": "SMUGGLERS COVE", "bb": 0}, {"n": "CHRISTMAS BIG BASS BONANZA", "bb": 1}, {"n": "SANTA'S WONDERLAND", "bb": 0},
            {"n": "STAR PIRATES CODE", "bb": 0}, {"n": "MYSTIC CHIEF", "bb": 0}, {"n": "PIGGY BANK BILLS", "bb": 0}, {"n": "TREASURE WILD", "bb": 0}, {"n": "GATES OF GATOT KACA", "bb": 0}, {"n": "MOCKTAIL NIGHTS", "bb": 0},
            {"n": "SWORD OF ARES", "bb": 0}, {"n": "SHIELD OF SPARTA", "bb": 0}, {"n": "TOWERING FORTUNES", "bb": 0}, {"n": "RELEASE THE KRAKEN 2", "bb": 0}, {"n": "SPIN & SCORE", "bb": 0}, {"n": "OLD GOLD MINER", "bb": 0},
            {"n": "CANDY STARS", "bb": 0}, {"n": "BIG BASS KEEP IT REEL", "bb": 0}, {"n": "CLEOCATRA", "bb": 0}, {"n": "WILD BEACH PARTY", "bb": 0}, {"n": "QUEEN OF GODS", "bb": 0}, {"n": "ZOMBIE CARNIVAL", "bb": 0},
            {"n": "FORTUNE OF GIZA", "bb": 0}, {"n": "SPIRIT OF ADVENTURE", "bb": 0}, {"n": "CLOVER GOLD", "bb": 0}, {"n": "EYE OF CLEOPATRA", "bb": 0}, {"n": "NORTH GUARDIANS", "bb": 0}, {"n": "DRILL THAT GOLD", "bb": 0},
            {"n": "BARN FESTIVAL", "bb": 0}, {"n": "RAINBOW GOLD", "bb": 0}, {"n": "TIC TAC TAKE", "bb": 0}, {"n": "WILD DEPTHS", "bb": 0}, {"n": "GOLD PARTY", "bb": 0}, {"n": "ROCK VEGAS", "bb": 0},
            {"n": "EMPEROR CAISHEN", "bb": 0}, {"n": "LUCKY LIGHTNING", "bb": 0}, {"n": "DRAGON HOT HOLD & SPIN", "bb": 0}, {"n": "HEART OF RIO", "bb": 0}, {"n": "PANDA'S FORTUNE 2", "bb": 0}, {"n": "5 LIONS MEGAWAYS", "bb": 1},
            {"n": "BOOK OF VIKINGS", "bb": 0}, {"n": "LUCKY GRACE AND CHARM", "bb": 0}, {"n": "RISE OF SAMURAI MEGAWAYS", "bb": 1}, {"n": "CHICKEN CHASE", "bb": 0}, {"n": "WILD WEST DUELS", "bb": 0}, {"n": "MYSTERY OF THE ORIENT", "bb": 0},
            {"n": "PEAK POWER", "bb": 0}, {"n": "CLUB TROPICANA", "bb": 0}, {"n": "THE KNIGHT KING", "bb": 0}, {"n": "GODS OF GIZA", "bb": 0}, {"n": "KINGDOM OF THE DEAD", "bb": 0}, {"n": "EXCALIBUR UNLEASHED", "bb": 0},
            {"n": "JANE HUNTER", "bb": 0}, {"n": "ZEUS VS HADES", "bb": 0}, {"n": "JEWEL RUSH", "bb": 0}, {"n": "STICKY BEES", "bb": 0}, {"n": "PIRATES PUB", "bb": 0}, {"n": "FLOATING DRAGON", "bb": 0},
            {"n": "FLOATING DRAGON MEGAWAYS", "bb": 1}, {"n": "TRIPLE TIGERS", "bb": 0}, {"n": "888 DRAGONS", "bb": 0}, {"n": "MONKEY MADNESS", "bb": 0}, {"n": "MASTER JOKER", "bb": 0}, {"n": "FIRE STRIKE", "bb": 0},
            {"n": "FIRE STRIKE 2", "bb": 0}, {"n": "DIAMOND STRIKE", "bb": 0}, {"n": "EXTRA JUICY", "bb": 0}, {"n": "EXTRA JUICY MEGAWAYS", "bb": 1}, {"n": "WILD WILD RICHES", "bb": 0}, {"n": "WILD WILD RICHES MEGAWAYS", "bb": 1},
            {"n": "PYRAMID KING", "bb": 0}, {"n": "HOT TO BURN", "bb": 0}, {"n": "HOT TO BURN EXTREME", "bb": 0}, {"n": "ULTRA HOLD AND SPIN", "bb": 0}, {"n": "LUCKY, GRACE & CHARM", "bb": 0}, {"n": "EMPTY THE BANK", "bb": 0},
            {"n": "FLOATING DRAGON", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "7 PIGGIES", "bb": 0}, {"n": "888 GOLD", "bb": 0}, {"n": "ALADDIN AND THE SORCERER", "bb": 0}, {"n": "AMAZING MONEY MACHINE", "bb": 0},
            {"n": "ANCIENT EGYPT CLASSIC", "bb": 0}, {"n": "BEOWULF", "bb": 0}, {"n": "BOOK OF TUT", "bb": 0}, {"n": "BRONCO SPIRIT", "bb": 0}, {"n": "CASH BONANZA", "bb": 1}, {"n": "CASH ELEVATOR", "bb": 0},
            {"n": "CONGO CASH", "bb": 0}, {"n": "COWBOYS GOLD", "bb": 0}, {"n": "CURSE OF THE WEREWOLF", "bb": 0}, {"n": "DA VINCI'S TREASURE", "bb": 0}, {"n": "DANCE PARTY", "bb": 0}, {"n": "DAY OF DEAD", "bb": 0},
            {"n": "DIAMOND ARE FOREVER", "bb": 0}, {"n": "DRAGON KINGDOM", "bb": 0}, {"n": "DRAGON TIGER", "bb": 0}, {"n": "DWARF MINE", "bb": 0}, {"n": "EMERALD KING", "bb": 0}, {"n": "EMERALD KING JACKPOT", "bb": 0},
            {"n": "FAIRYTALE FORTUNE", "bb": 0}, {"n": "FISHIN' REELS", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "GATES OF VALHALLA", "bb": 0}, {"n": "GLOOMY GRAVEYARD", "bb": 0}, {"n": "GOLD RUSH", "bb": 0},
            {"n": "GOLD TRAIN", "bb": 0}, {"n": "GOLDEN BEAUTY", "bb": 0}, {"n": "GOLDEN OX", "bb": 0}, {"n": "GREAT RHINO", "bb": 0}, {"n": "GREAT RHINO DELUXE", "bb": 0}, {"n": "HERCULES AND PEGASUS", "bb": 0},
            {"n": "HOT SAFARI", "bb": 0}, {"n": "JADE BUTTERFLY", "bb": 0}, {"n": "JOKER KING", "bb": 0}, {"n": "JOKER'S JEWELS", "bb": 0}, {"n": "JOURNEY TO THE WEST", "bb": 0}, {"n": "JUNGLE GORILLA", "bb": 0},
            {"n": "KNIGHT HOT SPOTZ", "bb": 0}, {"n": "LEPRECHAUN CAROL", "bb": 0}, {"n": "LEPRECHAUN SONG", "bb": 0}, {"n": "LUCKY DRAGONS", "bb": 0}, {"n": "LUCKY NEW YEAR", "bb": 0}, {"n": "MASTER CHEN'S FORTUNE", "bb": 0},
            {"n": "MEDUSA STRIKE", "bb": 0}, {"n": "MONEY MOUSE", "bb": 0}, {"n": "MONKEY WARRIOR", "bb": 0}, {"n": "MOON PRINCESS", "bb": 1}, {"n": "MYSTERIOUS", "bb": 0}, {"n": "MYSTERIOUS EGYPT", "bb": 0},
            {"n": "PANDA'S FORTUNE", "bb": 0}, {"n": "PEKING LUCK", "bb": 0}, {"n": "PHOENIX FORGE", "bb": 0}, {"n": "PIXIE WINGS", "bb": 0}, {"n": "PYRAMID KING", "bb": 0}, {"n": "QUEEN OF ATLANTIS", "bb": 0},
            {"n": "QUEEN OF GOLD", "bb": 0}, {"n": "RELEASE THE KRAKEN", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "SANTA", "bb": 0}, {"n": "SCARAB QUEEN", "bb": 0}, {"n": "SEVEN PIGGIES", "bb": 0},
            {"n": "STAR BOUNTY", "bb": 0}, {"n": "STREET RACER", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "TEMPLAR TUMBLE", "bb": 0}, {"n": "THE CHAMPIONS", "bb": 0}, {"n": "THE DOG HOUSE", "bb": 0},
            {"n": "THE WILD MACHINE", "bb": 0}, {"n": "THREE STAR FORTUNE", "bb": 0}, {"n": "TREE OF RICHES", "bb": 0}, {"n": "TRIPLE DRAGONS", "bb": 0}, {"n": "TRIPLE JOKER", "bb": 0}, {"n": "VAMPIRE VS WOLVES", "bb": 0},
            {"n": "VEGAS MAGIC", "bb": 0}, {"n": "VEGAS NIGHTS", "bb": 0}, {"n": "VOODOO MAGIC", "bb": 0}, {"n": "WILD GLADIATORS", "bb": 0}, {"n": "WILD PIXIES", "bb": 0}, {"n": "WILD SPELLS", "bb": 0},
            {"n": "WILD WALKER", "bb": 0}, {"n": "WOLF GOLD", "bb": 0}
        ],
        "PG SOFT": [
            {"n": "MAHJONG WAYS", "bb": 0}, {"n": "MAHJONG WAYS 2", "bb": 0}, {"n": "LUCKY NEKO", "bb": 0}, {"n": "TREASURES OF AZTEC", "bb": 0}, {"n": "FORTUNE OX", "bb": 0}, {"n": "FORTUNE MOUSE", "bb": 0},
            {"n": "FORTUNE TIGER", "bb": 0}, {"n": "FORTUNE RABBIT", "bb": 0}, {"n": "FORTUNE DRAGON", "bb": 0}, {"n": "DRAGON HATCH", "bb": 0}, {"n": "DRAGON HATCH 2", "bb": 0}, {"n": "GATES OF GATOT KACA", "bb": 0},
            {"n": "CAISHEN WINS", "bb": 0}, {"n": "GANESHA GOLD", "bb": 0}, {"n": "WILD BANDITO", "bb": 0}, {"n": "WAYS OF THE QILIN", "bb": 0}, {"n": "DREAMS OF MACAU", "bb": 0}, {"n": "SUPERMARKET SPREE", "bb": 0},
            {"n": "ROYAL KATT", "bb": 0}, {"n": "CANDY BONANZA", "bb": 1}, {"n": "HEIST STAKES", "bb": 0}, {"n": "RISE OF APOLLO", "bb": 0}, {"n": "MERMAID RICHES", "bb": 0}, {"n": "CRYPTO GOLD", "bb": 0},
            {"n": "BALI VACATION", "bb": 0}, {"n": "OPERA DYNASTY", "bb": 0}, {"n": "GUARDIANS OF ICE & FIRE", "bb": 0}, {"n": "JACK FROST'S WINTER", "bb": 0}, {"n": "GALACTIC GEMS", "bb": 0}, {"n": "JEWELS OF PROSPERITY", "bb": 0},
            {"n": "QUEEN OF BOUNTY", "bb": 0}, {"n": "VAMPIRE'S CHARM", "bb": 0}, {"n": "SECRET OF CLEOPATRA", "bb": 0}, {"n": "GENIE'S 3 WISHES", "bb": 0}, {"n": "CIRCUS DELIGHT", "bb": 0}, {"n": "DRAGON TIGER LUCK", "bb": 0},
            {"n": "PHOENIX RISES", "bb": 0}, {"n": "WILD FIREWORKS", "bb": 0}, {"n": "EGYPT'S BOOK OF MYSTERY", "bb": 0}, {"n": "CAPTAIN'S BOUNTY", "bb": 0}, {"n": "JOURNEY TO THE WEALTH", "bb": 0}, {"n": "GEM SAVIOUR", "bb": 0},
            {"n": "GEM SAVIOUR SWORD", "bb": 0}, {"n": "PIGGY GOLD", "bb": 0}, {"n": "JUNGLE DELIGHT", "bb": 0}, {"n": "THREE MONKEYS", "bb": 0}, {"n": "EMPEROR'S FAVOUR", "bb": 0}, {"n": "MUAY THAI CHAMPION", "bb": 0},
            {"n": "THE GREAT ICESCAPE", "bb": 0}, {"n": "LEPRECHAUN RICHES", "bb": 0}, {"n": "FLIRTING SCHOLAR", "bb": 0}, {"n": "NINJA VS SAMURAI", "bb": 0}, {"n": "DRAGON LEGEND", "bb": 0}, {"n": "SANTA'S GIFT RUSH", "bb": 0},
            {"n": "BATTLEGROUND ROYALE", "bb": 0}, {"n": "ROOSTER RUMBLE", "bb": 0}, {"n": "BUTTERFLY BLOSSOM", "bb": 0}, {"n": "LUCKY PIGGY", "bb": 0}, {"n": "PROSPERITY FORTUNE TREE", "bb": 0}, {"n": "TOTEM WONDERS", "bb": 0},
            {"n": "ALCHEMY GOLD", "bb": 0}, {"n": "MIDAS FORTUNE", "bb": 0}, {"n": "BAKERY BONANZA", "bb": 1}, {"n": "RAVE PARTY FEVER", "bb": 0}, {"n": "LUXURY GOODS", "bb": 0}, {"n": "MYSTICAL SPIRITS", "bb": 0},
            {"n": "ULTIMATE STRIKER", "bb": 0}, {"n": "PINATA WINS", "bb": 0}, {"n": "SAFARI WILDS", "bb": 0}, {"n": "WEREWOLF'S HUNT", "bb": 0}, {"n": "GLADIATOR'S GLORY", "bb": 0}, {"n": "CRUISE ROYALE", "bb": 0},
            {"n": "THREE PIGLETS", "bb": 0}, {"n": "SONGKRAN SPLASH", "bb": 0}, {"n": "HAWAIIAN TIKI", "bb": 0}, {"n": "SPIRITED WONDERS", "bb": 0}, {"n": "LEGEND OF PERSEUS", "bb": 0}, {"n": "WIN WIN FISH PRAWN CRAB", "bb": 0},
            {"n": "ORIENTAL PROSPERITY", "bb": 0}, {"n": "MASK CARNIVAL", "bb": 0}, {"n": "EMOJI RICHES", "bb": 0}, {"n": "FARM INVADERS", "bb": 0}, {"n": "DESTINY OF SUN & MOON", "bb": 0}, {"n": "MAJESTIC TREASURES", "bb": 0},
            {"n": "CANDY BURST", "bb": 0}, {"n": "ASGARDIA", "bb": 0}, {"n": "BIKINI PARADISE", "bb": 0}, {"n": "DOUBLE FORTUNE", "bb": 0}, {"n": "DRAGON TIGER LUCK", "bb": 0}, {"n": "GEM SAVIOUR CONQUEST", "bb": 0},
            {"n": "HOOD VS WOLF", "bb": 0}, {"n": "HOTPOT", "bb": 0}, {"n": "ICE SCAPE", "bb": 0}, {"n": "LEGEND OF HOU YI", "bb": 0}, {"n": "MEDUSA II", "bb": 0}, {"n": "MEDUSA", "bb": 0},
            {"n": "MR. HALLOW-WIN", "bb": 0}, {"n": "PLUSHIE FRENZY", "bb": 0}, {"n": "PROSPERITY LION", "bb": 0}, {"n": "REEL LOVE", "bb": 0}, {"n": "SANTA'S GIFT RUSH", "bb": 0}, {"n": "SHAOLIN SOCCER", "bb": 0},
            {"n": "STEAMPUNK FORTUNE", "bb": 0}, {"n": "SYMBOLS OF EGYPT", "bb": 0}, {"n": "THE GREAT ICESCAPE", "bb": 0}, {"n": "TREE OF FORTUNE", "bb": 0}, {"n": "WILD FIREWORKS", "bb": 0}, {"n": "WIN WIN WON", "bb": 0}
        ],
        "JILI": [
            {"n": "BIG SMALL CASINO ROYALE", "bb": 0}, {"n": "FORTUNE GARUDA 500", "bb": 0}, {"n": "LUCKY JAGUAR 500", "bb": 0}, {"n": "POSEIDON", "bb": 0}, {"n": "SUPER ACE", "bb": 0}, {"n": "SUPER ACE DELUXE", "bb": 0},
            {"n": "GOLDEN EMPIRE", "bb": 0}, {"n": "GOLDEN EMPIRE 2", "bb": 0}, {"n": "FORTUNE GEMS", "bb": 0}, {"n": "FORTUNE GEMS 2", "bb": 0}, {"n": "FORTUNE GEMS 3", "bb": 0}, {"n": "MONEY COMING", "bb": 0},
            {"n": "MONEY COMING EXPAND", "bb": 0}, {"n": "BOXING KING", "bb": 0}, {"n": "ALI BABA", "bb": 0}, {"n": "MEGA ACE", "bb": 0}, {"n": "MAGIC LAMP", "bb": 0}, {"n": "TWIN WINS", "bb": 0},
            {"n": "FENG SHEN", "bb": 0}, {"n": "ROMA X", "bb": 0}, {"n": "ROMA X DELUXE", "bb": 0}, {"n": "DRAGON TREASURE", "bb": 0}, {"n": "CRAZY 777", "bb": 0}, {"n": "GOLDEN QUEEN", "bb": 0},
            {"n": "JUNGLE KING", "bb": 0}, {"n": "CHARGE BUFFALO", "bb": 0}, {"n": "CHARGE BUFFALO 2", "bb": 0}, {"n": "PHARAOH TREASURE", "bb": 0}, {"n": "BUBBLE BEAUTY", "bb": 0}, {"n": "CANDY BABY", "bb": 0},
            {"n": "NIGHT CITY", "bb": 0}, {"n": "SUPER RICH", "bb": 0}, {"n": "HAPPY TAXI", "bb": 0}, {"n": "WORLD CUP", "bb": 0}, {"n": "MAYAN EMPIRE", "bb": 0}, {"n": "CHIN SHI HUANG", "bb": 0},
            {"n": "GOLDEN BANK", "bb": 0}, {"n": "LUCKY GOLDBRICKS", "bb": 0}, {"n": "HYPER BURST", "bb": 0}, {"n": "PARTY NIGHT", "bb": 0}, {"n": "SEVEN SEVEN SEVEN", "bb": 0}, {"n": "WAR OF DRAGONS", "bb": 0},
            {"n": "AGENT ACE", "bb": 0}, {"n": "HOT CHILLI", "bb": 0}, {"n": "MEDUSA", "bb": 0}, {"n": "CRAZY HUNTER", "bb": 0}, {"n": "SECRET TREASURE", "bb": 0}, {"n": "TRIAL OF ADVERSITY", "bb": 0},
            {"n": "WILD PANDA", "bb": 0}, {"n": "BOOK OF GOLD", "bb": 0}, {"n": "GOD OF MARTIAL", "bb": 0}, {"n": "SAMURAI", "bb": 0}, {"n": "WILD RACER", "bb": 0}, {"n": "GOLDEN LAND", "bb": 0},
            {"n": "LUCKY LADY", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "CRAZY FA FA FA", "bb": 0}, {"n": "DRAGON & TIGER", "bb": 0}, {"n": "KA CHIN", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0},
            {"n": "WORLD CUP 2022", "bb": 0}, {"n": "GOLDEN JOKER", "bb": 0}, {"n": "CRAZY PUSHER", "bb": 0}, {"n": "BONUS HUNTER", "bb": 0}, {"n": "JILI CAISHEN", "bb": 0}, {"n": "BOOK OF MYSTERY", "bb": 0},
            {"n": "PIRATE QUEEN", "bb": 0}, {"n": "MONEY TREE", "bb": 0}, {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD FOX", "bb": 0}, {"n": "CRAZY GOLDEN BANK", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0},
            {"n": "777", "bb": 0}, {"n": "ACE OF SPADES", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "BOXING KING", "bb": 0}, {"n": "CANDY BABY", "bb": 0}, {"n": "CHARGE BUFFALO", "bb": 0},
            {"n": "CRAZY 777", "bb": 0}, {"n": "CRAZY HUNTER", "bb": 0}, {"n": "DRAGON TREASURE", "bb": 0}, {"n": "FENG SHEN", "bb": 0}, {"n": "FORTUNE GEMS", "bb": 0}, {"n": "FORTUNE TREE", "bb": 0},
            {"n": "GOLDEN EMPIRE", "bb": 0}, {"n": "GOLDEN QUEEN", "bb": 0}, {"n": "HOT CHILLI", "bb": 0}, {"n": "JUNGLE KING", "bb": 0}, {"n": "LUCKY GOLDBRICKS", "bb": 0}, {"n": "MAGIC LAMP", "bb": 0},
            {"n": "MEGA ACE", "bb": 0}, {"n": "MONEY COMING", "bb": 0}, {"n": "NIGHT CITY", "bb": 0}, {"n": "PARTY NIGHT", "bb": 0}, {"n": "PHARAOH TREASURE", "bb": 0}, {"n": "ROMA X", "bb": 0},
            {"n": "SEVEN SEVEN SEVEN", "bb": 0}, {"n": "SUPER RICH", "bb": 0}, {"n": "TWIN WINS", "bb": 0}, {"n": "WAR OF DRAGONS", "bb": 0}, {"n": "WORLD CUP", "bb": 0}
        ],
        "NOLIMIT CITY": [
            {"n": "SAN QUENTIN XWAYS", "bb": 0}, {"n": "MENTAL", "bb": 0}, {"n": "FIRE IN THE HOLE", "bb": 0}, {"n": "DAS XBOOT", "bb": 0}, {"n": "XWAYS HOARDER", "bb": 0}, {"n": "EAST COAST VS WEST COAST", "bb": 0},
            {"n": "PUNK ROCKER", "bb": 0}, {"n": "DEADWOOD", "bb": 0}, {"n": "TOMBSTONE", "bb": 0}, {"n": "TOMBSTONE RIP", "bb": 0}, {"n": "EL PASO GUNFIGHT", "bb": 0}, {"n": "BUSHIDO WAYS", "bb": 0},
            {"n": "INFECTIOUS 5", "bb": 0}, {"n": "WARRIOR GRAVEYARD", "bb": 0}, {"n": "BARBARIAN FURY", "bb": 0}, {"n": "DRAGON TRIBE", "bb": 0}, {"n": "GAELIC GOLD", "bb": 0}, {"n": "HARLEQUIN CARNIVAL", "bb": 0},
            {"n": "ICE ICE YETI", "bb": 0}, {"n": "KITCHEN DRAMA", "bb": 0}, {"n": "MANHATTAN GOES WILD", "bb": 0}, {"n": "MAYA MAGIC", "bb": 0}, {"n": "MILKY WAYS", "bb": 0}, {"n": "MONKEY'S GOLD", "bb": 0},
            {"n": "OWLS", "bb": 0}, {"n": "PIXIES VS PIRATES", "bb": 0}, {"n": "POISON EVE", "bb": 0}, {"n": "STARSTRUCK", "bb": 0}, {"n": "TESLA JOLT", "bb": 0}, {"n": "THE CREEPY CARNIVAL", "bb": 0},
            {"n": "THOR", "bb": 0}, {"n": "TRACTOR BEAM", "bb": 0}, {"n": "TURST YOURSELF", "bb": 0}, {"n": "WIXX", "bb": 0}, {"n": "HOT 4 CASH", "bb": 0}, {"n": "IMMORTAL FRUITS", "bb": 0},
            {"n": "BOOK OF SHADOWS", "bb": 0}, {"n": "BUFFALO HUNTER", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "TOMB OF NEFERTITI", "bb": 0}, {"n": "TOMB OF AKHENATEN", "bb": 0}, {"n": "FOXY WILD HEART", "bb": 0},
            {"n": "EVIL GOBLINS", "bb": 0}, {"n": "LEGION X", "bb": 0}, {"n": "TRUE GRIT REDEMPTION", "bb": 0}, {"n": "MISERY MINING", "bb": 0}, {"n": "REMEMBER GULAG", "bb": 0}, {"n": "KAREN MANEATER", "bb": 0},
            {"n": "THE RAVE", "bb": 0}, {"n": "ROAD RAGE", "bb": 0}, {"n": "UGLIEST CATCH", "bb": 0}, {"n": "NINE TO FIVE", "bb": 0}, {"n": "DEVIL'S CROSSROAD", "bb": 0}, {"n": "D-DAY", "bb": 0},
            {"n": "POSSESSED", "bb": 0}, {"n": "KENNY'S BEST", "bb": 0}, {"n": "LAND OF THE FREE", "bb": 0}, {"n": "BRICK SNAKE 2000", "bb": 0}, {"n": "FIRE IN THE HOLE 2", "bb": 0}, {"n": "WHACKED!", "bb": 0},
            {"n": "BLOOD & SHADOW", "bb": 0}, {"n": "DISTURBED", "bb": 0}, {"n": "KISS MY CHAINS", "bb": 0}, {"n": "BENJI KILLED IN VEGAS", "bb": 0}, {"n": "WALK OF SHAME", "bb": 0}, {"n": "THE CAGE", "bb": 0},
            {"n": "GLUTTONY", "bb": 0}, {"n": "THE CRYPT", "bb": 0}, {"n": "BOUNTY HUNTERS", "bb": 0}, {"n": "DJ PSYCHO", "bb": 0}, {"n": "SERIAL", "bb": 0}, {"n": "PEARL HARBOR", "bb": 0},
            {"n": "DEAD CANARY", "bb": 0}, {"n": "FOLSOM PRISON", "bb": 0}, {"n": "THE SHADOW ORDER", "bb": 0}, {"n": "WOLF RITUAL", "bb": 0}, {"n": "DRAGON TRIBE", "bb": 0}, {"n": "MANHATTAN GOES WILD", "bb": 0},
            {"n": "MAYA MAGIC", "bb": 0}, {"n": "POISON EVE", "bb": 0}
        ],
        "MICROGAMING": [
            {"n": "MEGA MOOLAH", "bb": 0}, {"n": "IMMORTAL ROMANCE", "bb": 0}, {"n": "THUNDERSTRUCK II", "bb": 0}, {"n": "9 MASKS OF FIRE", "bb": 0}, {"n": "BREAK DA BANK AGAIN", "bb": 0}, {"n": "JURASSIC PARK", "bb": 0},
            {"n": "GAME OF THRONES", "bb": 0}, {"n": "AVALON II", "bb": 0}, {"n": "BOOK OF OZ", "bb": 0}, {"n": "WHEEL OF WISHES", "bb": 0}, {"n": "ADVENTURE PALACE", "bb": 0}, {"n": "AGENT JANE BLONDE", "bb": 0},
            {"n": "ALASKAN FISHING", "bb": 0}, {"n": "ARIANA", "bb": 0}, {"n": "BASS BOSS", "bb": 0}, {"n": "BIG BAD WOLF", "bb": 0}, {"n": "BUST THE BANK", "bb": 0}, {"n": "CARNAVAL", "bb": 0},
            {"n": "COOL BUCK", "bb": 0}, {"n": "DECK THE HALLS", "bb": 0}, {"n": "DRAGONZ", "bb": 0}, {"n": "EAGLE'S WINGS", "bb": 0}, {"n": "EMPEROR OF THE SEA", "bb": 0}, {"n": "FISH PARTY", "bb": 0},
            {"n": "FOOTBALL STAR", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "FORTUNIUM", "bb": 0}, {"n": "GIRLS WITH GUNS", "bb": 0}, {"n": "GOLD FACTORY", "bb": 0}, {"n": "HALLOWEEN", "bb": 0},
            {"n": "HAPPY HOLIDAYS", "bb": 0}, {"n": "HELLBOY", "bb": 0}, {"n": "HIGHLANDER", "bb": 0}, {"n": "HITMAN", "bb": 0}, {"n": "HOT INK", "bb": 0}, {"n": "JUNGLE JIM EL DORADO", "bb": 0},
            {"n": "KATHMANDU", "bb": 0}, {"n": "KINGS OF CASH", "bb": 0}, {"n": "LADIES NITE", "bb": 0}, {"n": "LARA CROFT", "bb": 0}, {"n": "LOADED", "bb": 0}, {"n": "LOST VEGAS", "bb": 0},
            {"n": "LUCKY KOI", "bb": 0}, {"n": "LUCKY LEPRECHAUN", "bb": 0}, {"n": "LUCKY ZODIAC", "bb": 0}, {"n": "MERMAIDS MILLIONS", "bb": 0}, {"n": "PLAYBOY", "bb": 0}, {"n": "PRETTY KITTY", "bb": 0},
            {"n": "PURE PLATINUM", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "TERMINATOR 2", "bb": 0}, {"n": "TOMB RAIDER", "bb": 0}, {"n": "TREASURE NILE", "bb": 0}, {"n": "WAXY VAN GOGH", "bb": 0},
            {"n": "WICKED TALES", "bb": 0}, {"n": "WILD SCARABS", "bb": 0}, {"n": "WOLF HOWL", "bb": 0}, {"n": "AMAZING LINK ZEUS", "bb": 0}, {"n": "ANCIENT FORTUNES: ZEUS", "bb": 0}, {"n": "ASSASSIN MOON", "bb": 0},
            {"n": "AURUM CODEX", "bb": 0}, {"n": "BANANA ODYSSEY", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "BEAUTIFUL BONES", "bb": 0}, {"n": "BIG KAHUNA", "bb": 0}, {"n": "5 REEL DRIVE", "bb": 0},
            {"n": "777 ROYAL WHEEL", "bb": 0}, {"n": "A DARK MATTER", "bb": 0}, {"n": "ABSALOOTLY MAD", "bb": 0}, {"n": "AFRICAN QUEST", "bb": 0}, {"n": "AGE OF CONQUEST", "bb": 0}, {"n": "ALCHEMISTS GOLD", "bb": 0},
            {"n": "ALL WIN FC", "bb": 0}, {"n": "AMAZING LINK APOLLO", "bb": 0}, {"n": "ANCIENT FORTUNES: POSEIDON", "bb": 0}, {"n": "ARENA OF GOLD", "bb": 0}, {"n": "ARTHUR'S FORTUNE", "bb": 0}, {"n": "ATLANTIS RISING", "bb": 0},
            {"n": "AURORA WILD", "bb": 0}, {"n": "AZTEC FALLS", "bb": 0}, {"n": "BAR BAR BLACK SHEEP", "bb": 0}, {"n": "BEACH BABES", "bb": 0}, {"n": "BELIEVE IT OR NOT", "bb": 0}, {"n": "BIG TOP", "bb": 0},
            {"n": "BOOK OF ATEM", "bb": 0}, {"n": "BOOK OF CAPTAIN SILVER", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "BOOM PIRATES", "bb": 0}, {"n": "BREAK AWAY", "bb": 0}, {"n": "BREAK AWAY LUCKY WILDS", "bb": 0},
            {"n": "BULLSEYE", "bb": 0}, {"n": "BURNING DESIRE", "bb": 0}, {"n": "BUSH TELEGRAPH", "bb": 0}, {"n": "CASH OF KINGDOMS", "bb": 0}, {"n": "CASH SPLASH", "bb": 0}, {"n": "CASHVILLE", "bb": 0},
            {"n": "CAT IN VEGAS", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CENTURION", "bb": 0}, {"n": "CHICAGO GOLD", "bb": 0}
        ],
        "BNG (BOOONGO)": [
            {"n": "SUN OF EGYPT", "bb": 0}, {"n": "SUN OF EGYPT 2", "bb": 0}, {"n": "SUN OF EGYPT 3", "bb": 0}, {"n": "SUN OF EGYPT 4", "bb": 0}, {"n": "15 DRAGON PEARLS", "bb": 0}, {"n": "DRAGON PEARLS", "bb": 0},
            {"n": "MAGIC APPLE", "bb": 0}, {"n": "MAGIC APPLE 2", "bb": 0}, {"n": "TIGER JUNGLE", "bb": 0}, {"n": "HIT THE GOLD", "bb": 0}, {"n": "BLACK WOLF", "bb": 0}, {"n": "BLACK WOLF 2", "bb": 0},
            {"n": "AZTEC SUN", "bb": 0}, {"n": "GREAT PANDA", "bb": 0}, {"n": "MOON SISTERS", "bb": 0}, {"n": "BUDDHA FORTUNE", "bb": 0}, {"n": "SCARAB TEMPLE", "bb": 0}, {"n": "3 COINS", "bb": 0},
            {"n": "3 COINS EGYPT", "bb": 0}, {"n": "3 HOT CHILLIES", "bb": 0}, {"n": "WUKONG", "bb": 0}, {"n": "WOLF SAGA", "bb": 0}, {"n": "PEARL DIVER", "bb": 0}, {"n": "PEARL DIVER 2", "bb": 0},
            {"n": "QUEEN OF THE SUN", "bb": 0}, {"n": "GOLD EXPRESS", "bb": 0}, {"n": "CANDY BOOM", "bb": 0}, {"n": "GIE GIE GIE", "bb": 0}, {"n": "HAPPY FISH", "bb": 0}, {"n": "LOTUS CHARM", "bb": 0},
            {"n": "ORCHID PRINCESS", "bb": 1}, {"n": "TIGER STONE", "bb": 0}, {"n": "SUPER RICH GOD", "bb": 0}, {"n": "EYE OF GOLD", "bb": 0}, {"n": "BOOK OF SUN", "bb": 0}, {"n": "BOOK OF SUN MULTICHANCE", "bb": 0},
            {"n": "GOD'S TEMPLE", "bb": 0}, {"n": "OLYMPIAN GODS", "bb": 0}, {"n": "POISONED APPLE", "bb": 0}, {"n": "POISONED APPLE 2", "bb": 0}, {"n": "777 GEMS", "bb": 0}, {"n": "SUPREME HOT", "bb": 0},
            {"n": "STAR GEMS", "bb": 0}, {"n": "SKY GEMS", "bb": 0}, {"n": "GREEN CHILLI", "bb": 0}, {"n": "GREEN CHILLI 2", "bb": 0}, {"n": "MORE MAGIC APPLE", "bb": 0}, {"n": "OIAO MEI", "bb": 0},
            {"n": "COIN VOLCANO", "bb": 0}, {"n": "EGYPT FIRE", "bb": 0}, {"n": "RIO GEMS", "bb": 0}, {"n": "HIT MORE GOLD", "bb": 0}, {"n": "STICKY PIGGY", "bb": 0}, {"n": "GODDESS OF EGYPT", "bb": 0},
            {"n": "BOOM! BOOM! GOLD!", "bb": 0}, {"n": "AZTEC SUN", "bb": 0}, {"n": "BOOK OF SUN", "bb": 0}, {"n": "BUDDHA FORTUNE", "bb": 0}, {"n": "DRAGON PEARLS", "bb": 0}, {"n": "EYE OF GOLD", "bb": 0},
            {"n": "GOD'S TEMPLE", "bb": 0}, {"n": "GREAT PANDA", "bb": 0}, {"n": "MAGIC APPLE", "bb": 0}, {"n": "MOON SISTERS", "bb": 0}, {"n": "OLYMPIAN GODS", "bb": 0}, {"n": "POISONED APPLE", "bb": 0},
            {"n": "SCARAB TEMPLE", "bb": 0}, {"n": "SUN OF EGYPT", "bb": 0}, {"n": "TIGER STONE", "bb": 0}, {"n": "WOLF SAGA", "bb": 0}
        ],
        "BIGPOT GAMING": [
            {"n": "CRAZY HUNTER", "bb": 0}, {"n": "GOLDEN ERA", "bb": 0}, {"n": "SECRET OF RICHES", "bb": 0}, {"n": "LUCKY SEVEN", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}, {"n": "PIRATE KING", "bb": 0},
            {"n": "DRAGON LEGEND", "bb": 0}, {"n": "MAGIC FOREST", "bb": 0}, {"n": "CANDY POP", "bb": 0}, {"n": "NEON CITY", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0},
            {"n": "VIKING GLORY", "bb": 0}, {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "OCEAN'S BOUNTY", "bb": 0},
            {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "HERCULES", "bb": 0}, {"n": "ZOMBIE ATTACK", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "CHRISTMAS JOY", "bb": 0}, {"n": "LUCKY FARM", "bb": 0},
            {"n": "CASINO ROYALE", "bb": 0}, {"n": "NINJA SQUAD", "bb": 0}, {"n": "ROBOT WARS", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0},
            {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "RACING STARS", "bb": 0}, {"n": "FISHING MASTER", "bb": 0}, {"n": "FRUIT SPLASH", "bb": 0}, {"n": "DIAMOND RUSH", "bb": 0}, {"n": "PANDA WARRIOR", "bb": 0},
            {"n": "SKY GUARDIAN", "bb": 0}, {"n": "DEEP SEA", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "WILD SAFARI", "bb": 0}, {"n": "MAGIC SPELL", "bb": 0}, {"n": "LUCKY DICE", "bb": 0},
            {"n": "GOLDEN RUSH", "bb": 0}, {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "CANDY POP", "bb": 0}, {"n": "CASINO ROYALE", "bb": 0}, {"n": "CRAZY HUNTER", "bb": 0},
            {"n": "DRAGON LEGEND", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "FRUIT SPLASH", "bb": 0}, {"n": "GOLDEN ERA", "bb": 0},
            {"n": "GOLDEN RUSH", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "HERCULES", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0}, {"n": "LUCKY FARM", "bb": 0},
            {"n": "LUCKY SEVEN", "bb": 0}, {"n": "MAGIC FOREST", "bb": 0}, {"n": "MAGIC SPELL", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "NEON CITY", "bb": 0}, {"n": "NINJA SQUAD", "bb": 0},
            {"n": "OCEAN'S BOUNTY", "bb": 0}, {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "PIRATE KING", "bb": 0}, {"n": "RACING STARS", "bb": 0}, {"n": "ROBOT WARS", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0},
            {"n": "SECRET OF RICHES", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "VIKING GLORY", "bb": 0}, {"n": "WILD SAFARI", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}
        ],
        "HACKSAW GAMING": [
            {"n": "WANTED DEAD OR A WILD", "bb": 0}, {"n": "CHAOS CREW", "bb": 0}, {"n": "CHAOS CREW II", "bb": 0}, {"n": "HAND OF ANUBIS", "bb": 0}, {"n": "RIP CITY", "bb": 0}, {"n": "LE BANDIT", "bb": 0},
            {"n": "DORK UNIT", "bb": 0}, {"n": "STACK 'EM", "bb": 0}, {"n": "STICK 'EM", "bb": 0}, {"n": "TOSHI VIDEO CLUB", "bb": 0}, {"n": "DROP 'EM", "bb": 0}, {"n": "ROTTEN", "bb": 0},
            {"n": "GLADIATOR LEGENDS", "bb": 0}, {"n": "STORMFORGED", "bb": 0}, {"n": "THE BOWERY BOYS", "bb": 0}, {"n": "PUG LIFE", "bb": 0}, {"n": "ITERCH", "bb": 0}, {"n": "KING CARROT", "bb": 0},
            {"n": "JOKER BOMBS", "bb": 0}, {"n": "CUBES", "bb": 0}, {"n": "CUBES 2", "bb": 0}, {"n": "DOUBLE RAINBOW", "bb": 0}, {"n": "TASTY TREATS", "bb": 0}, {"n": "XPW", "bb": 0},
            {"n": "UNDEA FORTUNE", "bb": 0}, {"n": "FEAR THE DARK", "bb": 0}, {"n": "BEAST BELOW", "bb": 0}, {"n": "SLAYERS INC", "bb": 0}, {"n": "DARK SUMMONING", "bb": 0}, {"n": "BENNY THE BEER", "bb": 0},
            {"n": "2 WILD 2 DIE", "bb": 0}, {"n": "FEEL THE BEAT", "bb": 0}, {"n": "FIST OF DESTRUCTION", "bb": 0}, {"n": "DIVINE DROP", "bb": 0}, {"n": "RUSTY & CURLY", "bb": 0}, {"n": "CASH CREW", "bb": 0},
            {"n": "BEAM BOYS", "bb": 0}, {"n": "BARBARIAN STASH", "bb": 0}, {"n": "JAGGED STONES", "bb": 0}, {"n": "SIXSIXSIX", "bb": 0}, {"n": "OMICRON", "bb": 0}, {"n": "HOP'N'POP", "bb": 0},
            {"n": "FRUIT DUEL", "bb": 0}, {"n": "BORN WILD", "bb": 0}, {"n": "FOREST FORTUNE", "bb": 0}, {"n": "HARVEST WILD", "bb": 0}, {"n": "AZTEC TWIST", "bb": 0}, {"n": "MYSTERY MOTEL", "bb": 0},
            {"n": "SCRATCH BRONZE", "bb": 0}, {"n": "SCRATCH PLATINUM", "bb": 0}, {"n": "ALPHA EAGLE", "bb": 0}, {"n": "BLOODTHIRST", "bb": 0}, {"n": "BREAK BONES", "bb": 0}, {"n": "CASH QUEST", "bb": 0},
            {"n": "CASH-A-CABANA", "bb": 0}, {"n": "CAT CLANS", "bb": 0}, {"n": "DORK UNIT", "bb": 0}, {"n": "DOUBLE RAINBOW", "bb": 0}, {"n": "EGGSTRAVAGANZA", "bb": 0}, {"n": "EYE OF THE PANDA", "bb": 0},
            {"n": "FRUIT DUEL", "bb": 0}, {"n": "GLADIATOR LEGENDS", "bb": 0}, {"n": "HAND OF ANUBIS", "bb": 0}, {"n": "HARVEST WILD", "bb": 0}, {"n": "HOP'N'POP", "bb": 0}, {"n": "ITERERO", "bb": 0},
            {"n": "JELLY REELS", "bb": 0}, {"n": "KING CARROT", "bb": 0}, {"n": "POCKET ROCKETS", "bb": 0}, {"n": "PUG LIFE", "bb": 0}, {"n": "RIP CITY", "bb": 0}, {"n": "ROTTEN", "bb": 0},
            {"n": "STACK 'EM", "bb": 0}, {"n": "STICK 'EM", "bb": 0}, {"n": "TOSHI VIDEO CLUB", "bb": 0}, {"n": "WANTED DEAD OR A WILD", "bb": 0}, {"n": "WARRIOR WAYS", "bb": 0}, {"n": "WILD YIELD", "bb": 0},
            {"n": "XPW", "bb": 0}
        ],
        "FA CHAI": [
            {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHINESE NEW YEAR 2", "bb": 0}, {"n": "NIGHT MARKET", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "MAGIC BEANS", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}, {"n": "FORTUNE KOI", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "MONEY TREE DOZER", "bb": 0}, {"n": "COIN MANIAC", "bb": 0},
            {"n": "STAR HUNTER", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0}, {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "ANIMAL RACING", "bb": 0},
            {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "LEGEND OF DRAGON", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0}, {"n": "GRAND BLUE", "bb": 0}, {"n": "TREASURE CRUISE", "bb": 0},
            {"n": "GLORY OF ROME", "bb": 0}, {"n": "MERMAID LEGEND", "bb": 0}, {"n": "RICH MAN", "bb": 0}, {"n": "LUCKY CLOVER", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0}, {"n": "GOLDEN DRAGON", "bb": 0},
            {"n": "KA-CHING", "bb": 0}, {"n": "PONG PONG HU", "bb": 0}, {"n": "MAHJONG WAYS 3", "bb": 0}, {"n": "FORTUNE GOD", "bb": 0}, {"n": "LUCKY WHEEL", "bb": 0}, {"n": "DISCO NIGHT", "bb": 0},
            {"n": "CANDY PARTY", "bb": 0}, {"n": "JUNGLE PARTY", "bb": 0}, {"n": "CIRCUS DOZER", "bb": 0}, {"n": "LIGHTNING BOMB", "bb": 0}, {"n": "FIERCE BATTLE", "bb": 0}, {"n": "SQUID PARTY", "bb": 0},
            {"n": "ANIMAL RACING", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "COIN MANIAC", "bb": 0}, {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "FORTUNE KOI", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0}, {"n": "GRAND BLUE", "bb": 0}, {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0},
            {"n": "LEGEND OF DRAGON", "bb": 0}, {"n": "LUCKY CLOVER", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0}, {"n": "MAGIC BEANS", "bb": 0}, {"n": "MERMAID LEGEND", "bb": 0}, {"n": "MONEY TREE DOZER", "bb": 0},
            {"n": "NIGHT MARKET", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0}, {"n": "RICH MAN", "bb": 0}, {"n": "STAR HUNTER", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0},
            {"n": "TREASURE CRUISE", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}
        ],
        "JDB GAMING": [
            {"n": "BURGER SHOP", "bb": 0}, {"n": "KONGFU", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0}, {"n": "LUCKY 7", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0},
            {"n": "DRAGON MASTER", "bb": 0}, {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "KINGSMAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0},
            {"n": "FORMOSA BEAR", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0},
            {"n": "OPEN SESAME", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "MAHJONG", "bb": 0}, {"n": "BANANA SAGA", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "ZODIAC", "bb": 0},
            {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD WEST", "bb": 0}, {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "CRAZY SCIENTIST", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0},
            {"n": "MAGIC WORLD", "bb": 0}, {"n": "WONDERLAND", "bb": 0}, {"n": "HALLOWEEN PARTY", "bb": 0}, {"n": "CHRISTMAS SURPRISE", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0},
            {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "BURGER SHOP", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "DRAGON MASTER", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0},
            {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "FORMOSA BEAR", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "KONGFU", "bb": 0},
            {"n": "LUCKY 7", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "MAHJONG", "bb": 0},
            {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "OPEN SESAME", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "TREASURE BOWL", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "ZODIAC", "bb": 0}
        ],
        "PLAY'N GO": [
            {"n": "BOOK OF DEAD", "bb": 0}, {"n": "REACTOONZ", "bb": 0}, {"n": "REACTOONZ 2", "bb": 0}, {"n": "MOON PRINCESS", "bb": 1}, {"n": "MOON PRINCESS 100", "bb": 1}, {"n": "MOON PRINCESS TRINITY", "bb": 1},
            {"n": "RISE OF OLYMPUS", "bb": 0}, {"n": "RISE OF OLYMPUS 100", "bb": 0}, {"n": "GEMIX", "bb": 0}, {"n": "GEMIX 2", "bb": 0}, {"n": "FIRE JOKER", "bb": 0}, {"n": "LEGACY OF DEAD", "bb": 0},
            {"n": "TOME OF MADNESS", "bb": 0}, {"n": "HONEY RUSH", "bb": 0}, {"n": "HONEY RUSH 100", "bb": 0}, {"n": "GOLDEN TICKET", "bb": 0}, {"n": "GOLDEN TICKET 2", "bb": 0}, {"n": "SWEET ALCHEMY", "bb": 0},
            {"n": "SWEET ALCHEMY 2", "bb": 0}, {"n": "RISE OF MERLIN", "bb": 0}, {"n": "PIMPED", "bb": 0}, {"n": "XMAS JOKER", "bb": 0}, {"n": "MYSTERY JOKER", "bb": 0}, {"n": "BIG WIN CAT", "bb": 0},
            {"n": "HOT TO BURN", "bb": 0}, {"n": "BOAT BONANZA", "bb": 1}, {"n": "CLASH OF CAMELOT", "bb": 0}, {"n": "COUNT JOKULA", "bb": 0}, {"n": "DIO KILLING THE DRAGON", "bb": 0}, {"n": "CHAMPS-ELYSEES", "bb": 0},
            {"n": "CANINE CARNAGE", "bb": 0}, {"n": "USA FLIP", "bb": 0}, {"n": "SHAMROCK MINER", "bb": 0}, {"n": "WILD FALLS 2", "bb": 0}, {"n": "GRIM THE SPLITTER", "bb": 0}, {"n": "LEGACY OF INCA", "bb": 0},
            {"n": "GAME OF GLADIATORS", "bb": 0}, {"n": "SAFARI OF WEALTH", "bb": 0}, {"n": "CAT WILDE", "bb": 0}, {"n": "RICH WILDE", "bb": 0}, {"n": "AGENT DESTINY", "bb": 0}, {"n": "ANCIENT EGYPT", "bb": 0},
            {"n": "ANNIHILATOR", "bb": 0}, {"n": "AZTEC IDOLS", "bb": 0}, {"n": "AZTEC WARRIOR PRINCESS", "bb": 1}, {"n": "BAKER'S TREAT", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "7 SINS", "bb": 0},
            {"n": "ACE OF SPADES", "bb": 0}, {"n": "AGENT DESTINY", "bb": 0}, {"n": "ANCIENT EGYPT", "bb": 0}, {"n": "ANNIHILATOR", "bb": 0}, {"n": "AZTEC IDOLS", "bb": 0}, {"n": "AZTEC WARRIOR PRINCESS", "bb": 1},
            {"n": "BAKER'S TREAT", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "BEAST OF WEALTH", "bb": 0}, {"n": "BELL OF FORTUNE", "bb": 0}, {"n": "BIG WIN 777", "bb": 0}, {"n": "BIG WIN CAT", "bb": 0},
            {"n": "BLACK MAMBA", "bb": 0}, {"n": "BLAZIN' BULLFROG", "bb": 0}, {"n": "BOOK OF DEAD", "bb": 0}, {"n": "BULL IN A CHINA SHOP", "bb": 0}, {"n": "CASH PUMP", "bb": 0}, {"n": "CASH VANDAL", "bb": 0},
            {"n": "CAT WILDE", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CHAMPS-ELYSEES", "bb": 0}, {"n": "CHARLIE CHANCE", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHRONOS JOKER", "bb": 0},
            {"n": "CLASH OF CAMELOT", "bb": 0}, {"n": "CLOUD QUEST", "bb": 0}, {"n": "COPS 'N' ROBBERS", "bb": 0}, {"n": "COUNT JOKULA", "bb": 0}, {"n": "COURT OF HEARTS", "bb": 0}, {"n": "COYOTE CASH", "bb": 0},
            {"n": "CRYSTAL SUN", "bb": 0}, {"n": "DAWN OF EGYPT", "bb": 0}, {"n": "DEADLY 5", "bb": 0}, {"n": "DEMON", "bb": 0}, {"n": "DERBY WHEEL", "bb": 0}, {"n": "DIAMOND VORTEX", "bb": 0},
            {"n": "DIO KILLING THE DRAGON", "bb": 0}, {"n": "DIVINE SHOWDOWN", "bb": 0}, {"n": "DOOM OF EGYPT", "bb": 0}, {"n": "DRAGON MAIDEN", "bb": 0}, {"n": "DRAGON SHIP", "bb": 0}, {"n": "EASTER EGGS", "bb": 0},
            {"n": "EGYPTIAN FORTUNE", "bb": 0}, {"n": "ENERGOONZ", "bb": 0}, {"n": "EYE OF THE ATUM", "bb": 0}, {"n": "FACES OF FREYA", "bb": 0}, {"n": "FIRE JOKER", "bb": 0}, {"n": "FIRE JOKER FREEZE", "bb": 0},
            {"n": "FIRE TOAD", "bb": 0}, {"n": "FORGE OF FORTUNES", "bb": 0}, {"n": "FORTUNE REWIND", "bb": 0}, {"n": "FROZEN GEMS", "bb": 0}, {"n": "GAME OF GLADIATORS", "bb": 0}, {"n": "GEMIX", "bb": 0},
            {"n": "GHOST OF DEAD", "bb": 0}, {"n": "GIGANTUANZ", "bb": 0}, {"n": "GOLD KING", "bb": 0}, {"n": "GOLD TROPHY 2", "bb": 0}, {"n": "GOLD VOLCANO", "bb": 0}, {"n": "GOLDEN TICKET", "bb": 0},
            {"n": "GRIM THE SPLITTER", "bb": 0}, {"n": "GUNSLINGER", "bb": 0}, {"n": "HALLOWEEN JACK", "bb": 0}, {"n": "HAPPY HALLOWEEN", "bb": 0}, {"n": "HOLIDAY SPIRITS", "bb": 0}, {"n": "HONEY RUSH", "bb": 0},
            {"n": "HOT TO BURN", "bb": 0}, {"n": "HOTEL YETI-WAY", "bb": 0}, {"n": "HOUSE OF DOOM", "bb": 0}, {"n": "HUGO", "bb": 0}, {"n": "HUGO 2", "bb": 0}, {"n": "ICE JOKER", "bb": 0},
            {"n": "IDOL OF FORTUNE", "bb": 0}, {"n": "IMMORTAL GUILD", "bb": 0}, {"n": "INFERNO STAR", "bb": 0}, {"n": "IRON GIRL", "bb": 0}, {"n": "ISHIN", "bb": 0}, {"n": "IT'S MAGIC", "bb": 0},
            {"n": "JACKPOT POKER", "bb": 0}, {"n": "JADE MAGICIAN", "bb": 0}, {"n": "JEWEL BOX", "bb": 0}, {"n": "JOLLY ROGER", "bb": 0}, {"n": "JOLLY ROGER 2", "bb": 0}, {"n": "KISS REELS OF ROCK", "bb": 0},
            {"n": "KNIGHT'S LIFE", "bb": 0}, {"n": "KRAKEN'S SKY", "bb": 0}, {"n": "LADY OF FORTUNE", "bb": 0}, {"n": "LEGACY OF DEAD", "bb": 0}, {"n": "LEGACY OF EGYPT", "bb": 0}, {"n": "LEGACY OF INCA", "bb": 0},
            {"n": "LEPRECHAUN GOES EGYPT", "bb": 0}, {"n": "LEPRECHAUN GOES HELL", "bb": 0}, {"n": "LEPRECHAUN GOES TO WILD", "bb": 0}, {"n": "LORD MERLIN", "bb": 0}, {"n": "LOVE IS IN THE AIR", "bb": 0}, {"n": "LUCKY DIAMONDS", "bb": 0},
            {"n": "MADAME DESTINY", "bb": 0}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "MAGICAL STACKS", "bb": 0}, {"n": "MAHJONG 88", "bb": 0}, {"n": "MERMAID'S DIAMOND", "bb": 0}, {"n": "METAL DETECTOR", "bb": 0},
            {"n": "MOON PRINCESS", "bb": 1}, {"n": "MOON PRINCESS 100", "bb": 1}, {"n": "MOON PRINCESS TRINITY", "bb": 1}, {"n": "MOUNTAIN OF WEALTH", "bb": 0}, {"n": "MUERTO EN MITLAN", "bb": 0}, {"n": "MULTIFRUIT 81", "bb": 0},
            {"n": "MYSTERY JOKER", "bb": 0}, {"n": "MYSTERY JOKER 6000", "bb": 0}, {"n": "NINJA FRUITS", "bb": 0}, {"n": "NYX", "bb": 0}, {"n": "OCTOPUS TREASURE", "bb": 0}, {"n": "ODIN: PROTECTOR OF REALMS", "bb": 0},
            {"n": "PAPYRUS", "bb": 0}, {"n": "PEARLS OF INDIA", "bb": 0}, {"n": "PERFECT GEMS", "bb": 0}, {"n": "PHOENIX REBORN", "bb": 0}, {"n": "PIGGY BANK", "bb": 0}, {"n": "PIMPED", "bb": 0},
            {"n": "PIXIES VS PIRATES", "bb": 0}, {"n": "PLANET FORTUNE", "bb": 0}, {"n": "PROSPERITY PALACE", "bb": 0}, {"n": "QUEEN'S DAY TILT", "bb": 0}, {"n": "RABBIT HOLE RICHES", "bb": 0}, {"n": "RAGING REX", "bb": 0},
            {"n": "RAGING REX 2", "bb": 0}, {"n": "RAINBOW CHARMS", "bb": 0}, {"n": "REACTOONZ", "bb": 0}, {"n": "REACTOONZ 2", "bb": 0}, {"n": "REEL STEAL", "bb": 0}, {"n": "RICH WILDE", "bb": 0},
            {"n": "RISE OF DEAD", "bb": 0}, {"n": "RISE OF MERLIN", "bb": 0}, {"n": "RISE OF OLYMPUS", "bb": 0}, {"n": "RISE OF OLYMPUS 100", "bb": 0}, {"n": "RITUAL RESURRECTION", "bb": 0}, {"n": "ROCCO GALLO", "bb": 0},
            {"n": "ROCK-N-ROLLA", "bb": 0}, {"n": "RONIN", "bb": 0}, {"n": "ROYAL MASQUERADE", "bb": 0}, {"n": "SABATON", "bb": 0}, {"n": "SAFARI OF WEALTH", "bb": 0}, {"n": "SAILS OF GOLD", "bb": 0},
            {"n": "SAMURAI KEN", "bb": 0}, {"n": "SEA HUNTER", "bb": 0}, {"n": "SECRET OF THE STONES", "bb": 0}, {"n": "SHAMROCK MINER", "bb": 0}, {"n": "SINS", "bb": 0}, {"n": "SMILEY'S", "bb": 0},
            {"n": "SPACE RACE", "bb": 0}, {"n": "SPARKY & SHORTZ", "bb": 0}, {"n": "SPEED CASH", "bb": 0}, {"n": "STAR BLAST", "bb": 0}, {"n": "STICKY JOKER", "bb": 0}, {"n": "STREET MAGIC", "bb": 0},
            {"n": "SUPER FLIP", "bb": 0}, {"n": "SWEET ALCHEMY", "bb": 0}, {"n": "SWEET ALCHEMY 2", "bb": 0}, {"n": "SWORD AND THE GRAIL", "bb": 0}, {"n": "TALES OF ASGARD", "bb": 0}, {"n": "TEMPLE OF WEALTH", "bb": 0},
            {"n": "TESTAMENT", "bb": 0}, {"n": "THAT'S RICH", "bb": 0}, {"n": "THE LAST SUNDOWN", "bb": 0}, {"n": "THE SWORD AND THE GRAIL", "bb": 0}, {"n": "THUNDER SCREECH", "bb": 0}, {"n": "TOME OF MADNESS", "bb": 0},
            {"n": "TROLL HUNTERS", "bb": 0}, {"n": "TROLL HUNTERS 2", "bb": 0}, {"n": "TWISTED SISTER", "bb": 0}, {"n": "USA FLIP", "bb": 0}, {"n": "VIKING RUNECRAFT", "bb": 0}, {"n": "WILD BLOOD", "bb": 0},
            {"n": "WILD BLOOD 2", "bb": 0}, {"n": "WILD FALLS", "bb": 0}, {"n": "WILD FALLS 2", "bb": 0}, {"n": "WILD FRAMES", "bb": 0}, {"n": "WILD MELON", "bb": 0}, {"n": "WILD NORTH", "bb": 0},
            {"n": "WIN-A-BEEST", "bb": 0}, {"n": "XMAS JOKER", "bb": 0}, {"n": "XMAS MAGIC", "bb": 0}
        ]
}

PROVIDERS_DATA_3 = {
        "PRAGMATIC PLAY": [
            {"n": "STARLIGHT PRINCESS Super Scatter ", "bb": 1}, {"n": "GATES OF OLYMPUS Super Scatter ", "bb": 1}, {"n": "GATES OF OLYMPUS", "bb": 1}, {"n": "GATES OF OLYMPUS 1000", "bb": 1}, {"n": "SWEET BONANZA", "bb": 1}, {"n": "SWEET BONANZA 1000", "bb": 1},
            {"n": "SUGAR RUSH", "bb": 1}, {"n": "SUGAR RUSH 1000", "bb": 1}, {"n": "STARLIGHT PRINCESS", "bb": 1}, {"n": "STARLIGHT PRINCESS 1000", "bb": 1}, {"n": "BIG BASS BONANZA", "bb": 1}, {"n": "BIG BASS SPLASH", "bb": 1},
            {"n": "BIG BASS AMAZON XTREME", "bb": 1}, {"n": "BIG BASS FLOATS MY BOAT", "bb": 1}, {"n": "THE DOG HOUSE", "bb": 1}, {"n": "THE DOG HOUSE MEGAWAYS", "bb": 1}, {"n": "THE DOG HOUSE MULTIHOLD", "bb": 1}, {"n": "FRUIT PARTY", "bb": 1},
            {"n": "FRUIT PARTY 2", "bb": 1}, {"n": "WOLF GOLD", "bb": 0}, {"n": "MUSTANG GOLD", "bb": 0}, {"n": "GREAT RHINO MEGAWAYS", "bb": 1}, {"n": "JOHN HUNTER & THE TOMB", "bb": 0}, {"n": "CHILLI HEAT", "bb": 0},
            {"n": "AZTEC GEMS", "bb": 0}, {"n": "AZTEC GEMS DELUXE", "bb": 0}, {"n": "WILD WEST GOLD", "bb": 1}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "THE HAND OF MIDAS", "bb": 1}, {"n": "POWER OF THOR MEGAWAYS", "bb": 1},
            {"n": "BUFFALO KING", "bb": 0}, {"n": "BUFFALO KING MEGAWAYS", "bb": 1}, {"n": "JUICY FRUITS", "bb": 1}, {"n": "GEMS BONANZA", "bb": 1}, {"n": "RISE OF GIZA", "bb": 1}, {"n": "CHICKEN DROP", "bb": 1},
            {"n": "BOOK OF FALLEN", "bb": 1}, {"n": "MAGICIAN'S SECRETS", "bb": 1}, {"n": "CRYSTAL CAVERNS", "bb": 1}, {"n": "SMUGGLERS COVE", "bb": 1}, {"n": "CHRISTMAS BIG BASS BONANZA", "bb": 0}, {"n": "SANTA'S WONDERLAND", "bb": 0},
            {"n": "STAR PIRATES CODE", "bb": 0}, {"n": "MYSTIC CHIEF", "bb": 0}, {"n": "PIGGY BANK BILLS", "bb": 0}, {"n": "TREASURE WILD", "bb": 0}, {"n": "GATES OF GATOT KACA", "bb": 1}, {"n": "MOCKTAIL NIGHTS", "bb": 0},
            {"n": "SWORD OF ARES", "bb": 1}, {"n": "SHIELD OF SPARTA", "bb": 1}, {"n": "TOWERING FORTUNES", "bb": 0}, {"n": "RELEASE THE KRAKEN 2", "bb": 1}, {"n": "SPIN & SCORE", "bb": 0}, {"n": "OLD GOLD MINER", "bb": 0},
            {"n": "CANDY STARS", "bb": 1}, {"n": "BIG BASS KEEP IT REEL", "bb": 1}, {"n": "CLEOCATRA", "bb": 1}, {"n": "WILD BEACH PARTY", "bb": 1}, {"n": "QUEEN OF GODS", "bb": 0}, {"n": "ZOMBIE CARNIVAL", "bb": 1},
            {"n": "FORTUNE OF GIZA", "bb": 0}, {"n": "SPIRIT OF ADVENTURE", "bb": 0}, {"n": "CLOVER GOLD", "bb": 0}, {"n": "EYE OF CLEOPATRA", "bb": 0}, {"n": "NORTH GUARDIANS", "bb": 1}, {"n": "DRILL THAT GOLD", "bb": 0},
            {"n": "BARN FESTIVAL", "bb": 1}, {"n": "RAINBOW GOLD", "bb": 1}, {"n": "TIC TAC TAKE", "bb": 1}, {"n": "WILD DEPTHS", "bb": 0}, {"n": "GOLD PARTY", "bb": 0}, {"n": "ROCK VEGAS", "bb": 0},
            {"n": "EMPEROR CAISHEN", "bb": 0}, {"n": "LUCKY LIGHTNING", "bb": 0}, {"n": "DRAGON HOT HOLD & SPIN", "bb": 0}, {"n": "HEART OF RIO", "bb": 0}, {"n": "PANDA'S FORTUNE 2", "bb": 0}, {"n": "5 LIONS MEGAWAYS", "bb": 1},
            {"n": "BOOK OF VIKINGS", "bb": 0}, {"n": "LUCKY GRACE AND CHARM", "bb": 0}, {"n": "RISE OF SAMURAI MEGAWAYS", "bb": 1}, {"n": "CHICKEN CHASE", "bb": 0}, {"n": "WILD WEST DUELS", "bb": 1}, {"n": "MYSTERY OF THE ORIENT", "bb": 1},
            {"n": "PEAK POWER", "bb": 1}, {"n": "CLUB TROPICANA", "bb": 1}, {"n": "THE KNIGHT KING", "bb": 1}, {"n": "GODS OF GIZA", "bb": 1}, {"n": "KINGDOM OF THE DEAD", "bb": 1}, {"n": "EXCALIBUR UNLEASHED", "bb": 1},
            {"n": "JANE HUNTER", "bb": 0}, {"n": "ZEUS VS HADES", "bb": 1}, {"n": "JEWEL RUSH", "bb": 1}, {"n": "STICKY BEES", "bb": 1}, {"n": "PIRATES PUB", "bb": 1}, {"n": "FLOATING DRAGON", "bb": 0},
            {"n": "FLOATING DRAGON MEGAWAYS", "bb": 1}, {"n": "TRIPLE TIGERS", "bb": 0}, {"n": "888 DRAGONS", "bb": 0}, {"n": "MONKEY MADNESS", "bb": 0}, {"n": "MASTER JOKER", "bb": 0}, {"n": "FIRE STRIKE", "bb": 0},
            {"n": "FIRE STRIKE 2", "bb": 0}, {"n": "DIAMOND STRIKE", "bb": 0}, {"n": "EXTRA JUICY", "bb": 0}, {"n": "EXTRA JUICY MEGAWAYS", "bb": 1}, {"n": "WILD WILD RICHES", "bb": 0}, {"n": "WILD WILD RICHES MEGAWAYS", "bb": 1},
            {"n": "PYRAMID KING", "bb": 0}, {"n": "HOT TO BURN", "bb": 0}, {"n": "HOT TO BURN EXTREME", "bb": 0}, {"n": "ULTRA HOLD AND SPIN", "bb": 0}, {"n": "LUCKY, GRACE & CHARM", "bb": 0}, {"n": "EMPTY THE BANK", "bb": 0},
            {"n": "FLOATING DRAGON", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "7 PIGGIES", "bb": 0}, {"n": "888 GOLD", "bb": 0}, {"n": "ALADDIN AND THE SORCERER", "bb": 0}, {"n": "AMAZING MONEY MACHINE", "bb": 0},
            {"n": "ANCIENT EGYPT CLASSIC", "bb": 0}, {"n": "BEOWULF", "bb": 0}, {"n": "BOOK OF TUT", "bb": 0}, {"n": "BRONCO SPIRIT", "bb": 0}, {"n": "CASH BONANZA", "bb": 0}, {"n": "CASH ELEVATOR", "bb": 0},
            {"n": "CONGO CASH", "bb": 0}, {"n": "COWBOYS GOLD", "bb": 0}, {"n": "CURSE OF THE WEREWOLF", "bb": 0}, {"n": "DA VINCI'S TREASURE", "bb": 0}, {"n": "DANCE PARTY", "bb": 0}, {"n": "DAY OF DEAD", "bb": 0},
            {"n": "DIAMOND ARE FOREVER", "bb": 0}, {"n": "DRAGON KINGDOM", "bb": 0}, {"n": "DRAGON TIGER", "bb": 0}, {"n": "DWARF MINE", "bb": 0}, {"n": "EMERALD KING", "bb": 0}, {"n": "EMERALD KING JACKPOT", "bb": 0},
            {"n": "FAIRYTALE FORTUNE", "bb": 0}, {"n": "FISHIN' REELS", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "GATES OF VALHALLA", "bb": 1}, {"n": "GLOOMY GRAVEYARD", "bb": 0}, {"n": "GOLD RUSH", "bb": 0},
            {"n": "GOLD TRAIN", "bb": 0}, {"n": "GOLDEN BEAUTY", "bb": 0}, {"n": "GOLDEN OX", "bb": 0}, {"n": "GREAT RHINO", "bb": 0}, {"n": "GREAT RHINO DELUXE", "bb": 0}, {"n": "HERCULES AND PEGASUS", "bb": 0},
            {"n": "HOT SAFARI", "bb": 0}, {"n": "JADE BUTTERFLY", "bb": 0}, {"n": "JOKER KING", "bb": 0}, {"n": "JOKER'S JEWELS", "bb": 0}, {"n": "JOURNEY TO THE WEST", "bb": 0}, {"n": "JUNGLE GORILLA", "bb": 0},
            {"n": "KNIGHT HOT SPOTZ", "bb": 1}, {"n": "LEPRECHAUN CAROL", "bb": 0}, {"n": "LEPRECHAUN SONG", "bb": 0}, {"n": "LUCKY DRAGONS", "bb": 0}, {"n": "LUCKY NEW YEAR", "bb": 0}, {"n": "MASTER CHEN'S FORTUNE", "bb": 0},
            {"n": "MEDUSA STRIKE", "bb": 0}, {"n": "MONEY MOUSE", "bb": 0}, {"n": "MONKEY WARRIOR", "bb": 0}, {"n": "MOON PRINCESS", "bb": 0}, {"n": "MYSTERIOUS", "bb": 0}, {"n": "MYSTERIOUS EGYPT", "bb": 0},
            {"n": "PANDA'S FORTUNE", "bb": 0}, {"n": "PEKING LUCK", "bb": 0}, {"n": "PHOENIX FORGE", "bb": 0}, {"n": "PIXIE WINGS", "bb": 0}, {"n": "PYRAMID KING", "bb": 0}, {"n": "QUEEN OF ATLANTIS", "bb": 0},
            {"n": "QUEEN OF GOLD", "bb": 0}, {"n": "RELEASE THE KRAKEN", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "SANTA", "bb": 0}, {"n": "SCARAB QUEEN", "bb": 0}, {"n": "SEVEN PIGGIES", "bb": 0},
            {"n": "STAR BOUNTY", "bb": 0}, {"n": "STREET RACER", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "TEMPLAR TUMBLE", "bb": 1}, {"n": "THE CHAMPIONS", "bb": 0}, {"n": "THE DOG HOUSE", "bb": 0},
            {"n": "THE WILD MACHINE", "bb": 0}, {"n": "THREE STAR FORTUNE", "bb": 0}, {"n": "TREE OF RICHES", "bb": 0}, {"n": "TRIPLE DRAGONS", "bb": 0}, {"n": "TRIPLE JOKER", "bb": 0}, {"n": "VAMPIRE VS WOLVES", "bb": 0},
            {"n": "VEGAS MAGIC", "bb": 0}, {"n": "VEGAS NIGHTS", "bb": 0}, {"n": "VOODOO MAGIC", "bb": 0}, {"n": "WILD GLADIATORS", "bb": 0}, {"n": "WILD PIXIES", "bb": 0}, {"n": "WILD SPELLS", "bb": 0},
            {"n": "WILD WALKER", "bb": 0}, {"n": "WOLF GOLD", "bb": 0}
        ],
        "PG SOFT": [
            {"n": "MAHJONG WAYS", "bb": 0}, {"n": "MAHJONG WAYS 2", "bb": 0}, {"n": "LUCKY NEKO", "bb": 0}, {"n": "TREASURES OF AZTEC", "bb": 0}, {"n": "FORTUNE OX", "bb": 0}, {"n": "FORTUNE MOUSE", "bb": 0},
            {"n": "FORTUNE TIGER", "bb": 0}, {"n": "FORTUNE RABBIT", "bb": 0}, {"n": "FORTUNE DRAGON", "bb": 0}, {"n": "DRAGON HATCH", "bb": 0}, {"n": "DRAGON HATCH 2", "bb": 0}, {"n": "GATES OF GATOT KACA", "bb": 1},
            {"n": "CAISHEN WINS", "bb": 0}, {"n": "GANESHA GOLD", "bb": 0}, {"n": "WILD BANDITO", "bb": 0}, {"n": "WAYS OF THE QILIN", "bb": 0}, {"n": "DREAMS OF MACAU", "bb": 0}, {"n": "SUPERMARKET SPREE", "bb": 1},
            {"n": "ROYAL KATT", "bb": 0}, {"n": "CANDY BONANZA", "bb": 1}, {"n": "HEIST STAKES", "bb": 0}, {"n": "RISE OF APOLLO", "bb": 1}, {"n": "MERMAID RICHES", "bb": 1}, {"n": "CRYPTO GOLD", "bb": 1},
            {"n": "BALI VACATION", "bb": 1}, {"n": "OPERA DYNASTY", "bb": 1}, {"n": "GUARDIANS OF ICE & FIRE", "bb": 1}, {"n": "JACK FROST'S WINTER", "bb": 1}, {"n": "GALACTIC GEMS", "bb": 0}, {"n": "JEWELS OF PROSPERITY", "bb": 1},
            {"n": "QUEEN OF BOUNTY", "bb": 0}, {"n": "VAMPIRE'S CHARM", "bb": 1}, {"n": "SECRET OF CLEOPATRA", "bb": 1}, {"n": "GENIE'S 3 WISHES", "bb": 1}, {"n": "CIRCUS DELIGHT", "bb": 1}, {"n": "DRAGON TIGER LUCK", "bb": 0},
            {"n": "PHOENIX RISES", "bb": 1}, {"n": "WILD FIREWORKS", "bb": 1}, {"n": "EGYPT'S BOOK OF MYSTERY", "bb": 1}, {"n": "CAPTAIN'S BOUNTY", "bb": 0}, {"n": "JOURNEY TO THE WEALTH", "bb": 0}, {"n": "GEM SAVIOUR", "bb": 0},
            {"n": "GEM SAVIOUR SWORD", "bb": 0}, {"n": "PIGGY GOLD", "bb": 0}, {"n": "JUNGLE DELIGHT", "bb": 0}, {"n": "THREE MONKEYS", "bb": 0}, {"n": "EMPEROR'S FAVOUR", "bb": 0}, {"n": "MUAY THAI CHAMPION", "bb": 0},
            {"n": "THE GREAT ICESCAPE", "bb": 0}, {"n": "LEPRECHAUN RICHES", "bb": 1}, {"n": "FLIRTING SCHOLAR", "bb": 0}, {"n": "NINJA VS SAMURAI", "bb": 0}, {"n": "DRAGON LEGEND", "bb": 0}, {"n": "SANTA'S GIFT RUSH", "bb": 0},
            {"n": "BATTLEGROUND ROYALE", "bb": 1}, {"n": "ROOSTER RUMBLE", "bb": 1}, {"n": "BUTTERFLY BLOSSOM", "bb": 1}, {"n": "LUCKY PIGGY", "bb": 1}, {"n": "PROSPERITY FORTUNE TREE", "bb": 1}, {"n": "TOTEM WONDERS", "bb": 0},
            {"n": "ALCHEMY GOLD", "bb": 1}, {"n": "MIDAS FORTUNE", "bb": 1}, {"n": "BAKERY BONANZA", "bb": 1}, {"n": "RAVE PARTY FEVER", "bb": 1}, {"n": "LUXURY GOODS", "bb": 0}, {"n": "MYSTICAL SPIRITS", "bb": 1},
            {"n": "ULTIMATE STRIKER", "bb": 0}, {"n": "PINATA WINS", "bb": 1}, {"n": "SAFARI WILDS", "bb": 1}, {"n": "WEREWOLF'S HUNT", "bb": 1}, {"n": "GLADIATOR'S GLORY", "bb": 1}, {"n": "CRUISE ROYALE", "bb": 1},
            {"n": "THREE PIGLETS", "bb": 0}, {"n": "SONGKRAN SPLASH", "bb": 1}, {"n": "HAWAIIAN TIKI", "bb": 1}, {"n": "SPIRITED WONDERS", "bb": 0}, {"n": "LEGEND OF PERSEUS", "bb": 0}, {"n": "WIN WIN FISH PRAWN CRAB", "bb": 0},
            {"n": "ORIENTAL PROSPERITY", "bb": 0}, {"n": "MASK CARNIVAL", "bb": 0}, {"n": "EMOJI RICHES", "bb": 0}, {"n": "FARM INVADERS", "bb": 0}, {"n": "DESTINY OF SUN & MOON", "bb": 0}, {"n": "MAJESTIC TREASURES", "bb": 0},
            {"n": "CANDY BURST", "bb": 0}, {"n": "ASGARDIA", "bb": 0}, {"n": "BIKINI PARADISE", "bb": 0}, {"n": "DOUBLE FORTUNE", "bb": 0}, {"n": "DRAGON TIGER LUCK", "bb": 0}, {"n": "GEM SAVIOUR CONQUEST", "bb": 0},
            {"n": "HOOD VS WOLF", "bb": 0}, {"n": "HOTPOT", "bb": 0}, {"n": "ICE SCAPE", "bb": 0}, {"n": "LEGEND OF HOU YI", "bb": 0}, {"n": "MEDUSA II", "bb": 0}, {"n": "MEDUSA", "bb": 0},
            {"n": "MR. HALLOW-WIN", "bb": 0}, {"n": "PLUSHIE FRENZY", "bb": 0}, {"n": "PROSPERITY LION", "bb": 0}, {"n": "REEL LOVE", "bb": 0}, {"n": "SANTA'S GIFT RUSH", "bb": 0}, {"n": "SHAOLIN SOCCER", "bb": 0},
            {"n": "STEAMPUNK FORTUNE", "bb": 0}, {"n": "SYMBOLS OF EGYPT", "bb": 0}, {"n": "THE GREAT ICESCAPE", "bb": 0}, {"n": "TREE OF FORTUNE", "bb": 0}, {"n": "WILD FIREWORKS", "bb": 1}, {"n": "WIN WIN WON", "bb": 0}
        ],
        "JILI": [
            {"n": "BIG SMALL CASINO ROYALE", "bb": 0}, {"n": "FORTUNE GARUDA 500", "bb": 0}, {"n": "LUCKY JAGUAR 500", "bb": 0}, {"n": "POSEIDON", "bb": 0}, {"n": "SUPER ACE", "bb": 0}, {"n": "SUPER ACE DELUXE", "bb": 0},
            {"n": "GOLDEN EMPIRE", "bb": 0}, {"n": "GOLDEN EMPIRE 2", "bb": 0}, {"n": "FORTUNE GEMS", "bb": 0}, {"n": "FORTUNE GEMS 2", "bb": 0}, {"n": "FORTUNE GEMS 3", "bb": 0}, {"n": "MONEY COMING", "bb": 0},
            {"n": "MONEY COMING EXPAND", "bb": 0}, {"n": "BOXING KING", "bb": 0}, {"n": "ALI BABA", "bb": 0}, {"n": "MEGA ACE", "bb": 0}, {"n": "MAGIC LAMP", "bb": 0}, {"n": "TWIN WINS", "bb": 0},
            {"n": "FENG SHEN", "bb": 0}, {"n": "ROMA X", "bb": 0}, {"n": "ROMA X DELUXE", "bb": 0}, {"n": "DRAGON TREASURE", "bb": 0}, {"n": "CRAZY 777", "bb": 0}, {"n": "GOLDEN QUEEN", "bb": 0},
            {"n": "JUNGLE KING", "bb": 0}, {"n": "CHARGE BUFFALO", "bb": 0}, {"n": "CHARGE BUFFALO 2", "bb": 0}, {"n": "PHARAOH TREASURE", "bb": 0}, {"n": "BUBBLE BEAUTY", "bb": 0}, {"n": "CANDY BABY", "bb": 0},
            {"n": "NIGHT CITY", "bb": 0}, {"n": "SUPER RICH", "bb": 0}, {"n": "HAPPY TAXI", "bb": 0}, {"n": "WORLD CUP", "bb": 0}, {"n": "MAYAN EMPIRE", "bb": 0}, {"n": "CHIN SHI HUANG", "bb": 0},
            {"n": "GOLDEN BANK", "bb": 0}, {"n": "LUCKY GOLDBRICKS", "bb": 0}, {"n": "HYPER BURST", "bb": 0}, {"n": "PARTY NIGHT", "bb": 0}, {"n": "SEVEN SEVEN SEVEN", "bb": 0}, {"n": "WAR OF DRAGONS", "bb": 0},
            {"n": "AGENT ACE", "bb": 0}, {"n": "HOT CHILLI", "bb": 0}, {"n": "MEDUSA", "bb": 0}, {"n": "CRAZY HUNTER", "bb": 0}, {"n": "SECRET TREASURE", "bb": 0}, {"n": "TRIAL OF ADVERSITY", "bb": 0},
            {"n": "WILD PANDA", "bb": 0}, {"n": "BOOK OF GOLD", "bb": 0}, {"n": "GOD OF MARTIAL", "bb": 0}, {"n": "SAMURAI", "bb": 0}, {"n": "WILD RACER", "bb": 0}, {"n": "GOLDEN LAND", "bb": 0},
            {"n": "LUCKY LADY", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "CRAZY FA FA FA", "bb": 0}, {"n": "DRAGON & TIGER", "bb": 0}, {"n": "KA CHIN", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0},
            {"n": "WORLD CUP 2022", "bb": 0}, {"n": "GOLDEN JOKER", "bb": 0}, {"n": "CRAZY PUSHER", "bb": 0}, {"n": "BONUS HUNTER", "bb": 0}, {"n": "JILI CAISHEN", "bb": 0}, {"n": "BOOK OF MYSTERY", "bb": 0},
            {"n": "PIRATE QUEEN", "bb": 0}, {"n": "MONEY TREE", "bb": 0}, {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD FOX", "bb": 0}, {"n": "CRAZY GOLDEN BANK", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0},
            {"n": "777", "bb": 0}, {"n": "ACE OF SPADES", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "BOXING KING", "bb": 0}, {"n": "CANDY BABY", "bb": 0}, {"n": "CHARGE BUFFALO", "bb": 0},
            {"n": "CRAZY 777", "bb": 0}, {"n": "CRAZY HUNTER", "bb": 0}, {"n": "DRAGON TREASURE", "bb": 0}, {"n": "FENG SHEN", "bb": 0}, {"n": "FORTUNE GEMS", "bb": 0}, {"n": "FORTUNE TREE", "bb": 0},
            {"n": "GOLDEN EMPIRE", "bb": 0}, {"n": "GOLDEN QUEEN", "bb": 0}, {"n": "HOT CHILLI", "bb": 0}, {"n": "JUNGLE KING", "bb": 0}, {"n": "LUCKY GOLDBRICKS", "bb": 0}, {"n": "MAGIC LAMP", "bb": 0},
            {"n": "MEGA ACE", "bb": 0}, {"n": "MONEY COMING", "bb": 0}, {"n": "NIGHT CITY", "bb": 0}, {"n": "PARTY NIGHT", "bb": 0}, {"n": "PHARAOH TREASURE", "bb": 0}, {"n": "ROMA X", "bb": 0},
            {"n": "SEVEN SEVEN SEVEN", "bb": 0}, {"n": "SUPER RICH", "bb": 0}, {"n": "TWIN WINS", "bb": 0}, {"n": "WAR OF DRAGONS", "bb": 0}, {"n": "WORLD CUP", "bb": 0}
        ],
        "NOLIMIT CITY": [
            {"n": "SAN QUENTIN XWAYS", "bb": 1}, {"n": "MENTAL", "bb": 1}, {"n": "FIRE IN THE HOLE", "bb": 1}, {"n": "DAS XBOOT", "bb": 1}, {"n": "XWAYS HOARDER", "bb": 1}, {"n": "EAST COAST VS WEST COAST", "bb": 1},
            {"n": "PUNK ROCKER", "bb": 1}, {"n": "DEADWOOD", "bb": 1}, {"n": "TOMBSTONE", "bb": 0}, {"n": "TOMBSTONE RIP", "bb": 1}, {"n": "EL PASO GUNFIGHT", "bb": 1}, {"n": "BUSHIDO WAYS", "bb": 1},
            {"n": "INFECTIOUS 5", "bb": 1}, {"n": "WARRIOR GRAVEYARD", "bb": 1}, {"n": "BARBARIAN FURY", "bb": 1}, {"n": "DRAGON TRIBE", "bb": 1}, {"n": "GAELIC GOLD", "bb": 0}, {"n": "HARLEQUIN CARNIVAL", "bb": 1},
            {"n": "ICE ICE YETI", "bb": 0}, {"n": "KITCHEN DRAMA", "bb": 0}, {"n": "MANHATTAN GOES WILD", "bb": 0}, {"n": "MAYA MAGIC", "bb": 0}, {"n": "MILKY WAYS", "bb": 0}, {"n": "MONKEY'S GOLD", "bb": 0},
            {"n": "OWLS", "bb": 0}, {"n": "PIXIES VS PIRATES", "bb": 0}, {"n": "POISON EVE", "bb": 0}, {"n": "STARSTRUCK", "bb": 0}, {"n": "TESLA JOLT", "bb": 0}, {"n": "THE CREEPY CARNIVAL", "bb": 0},
            {"n": "THOR", "bb": 0}, {"n": "TRACTOR BEAM", "bb": 0}, {"n": "TURST YOURSELF", "bb": 0}, {"n": "WIXX", "bb": 0}, {"n": "HOT 4 CASH", "bb": 0}, {"n": "IMMORTAL FRUITS", "bb": 0},
            {"n": "BOOK OF SHADOWS", "bb": 1}, {"n": "BUFFALO HUNTER", "bb": 1}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "TOMB OF NEFERTITI", "bb": 0}, {"n": "TOMB OF AKHENATEN", "bb": 0}, {"n": "FOXY WILD HEART", "bb": 0},
            {"n": "EVIL GOBLINS", "bb": 1}, {"n": "LEGION X", "bb": 1}, {"n": "TRUE GRIT REDEMPTION", "bb": 1}, {"n": "MISERY MINING", "bb": 1}, {"n": "REMEMBER GULAG", "bb": 1}, {"n": "KAREN MANEATER", "bb": 1},
            {"n": "THE RAVE", "bb": 1}, {"n": "ROAD RAGE", "bb": 1}, {"n": "UGLIEST CATCH", "bb": 1}, {"n": "NINE TO FIVE", "bb": 1}, {"n": "DEVIL'S CROSSROAD", "bb": 1}, {"n": "D-DAY", "bb": 1},
            {"n": "POSSESSED", "bb": 1}, {"n": "KENNY'S BEST", "bb": 0}, {"n": "LAND OF THE FREE", "bb": 1}, {"n": "BRICK SNAKE 2000", "bb": 1}, {"n": "FIRE IN THE HOLE 2", "bb": 1}, {"n": "WHACKED!", "bb": 1},
            {"n": "BLOOD & SHADOW", "bb": 1}, {"n": "DISTURBED", "bb": 1}, {"n": "KISS MY CHAINS", "bb": 0}, {"n": "BENJI KILLED IN VEGAS", "bb": 1}, {"n": "WALK OF SHAME", "bb": 1}, {"n": "THE CAGE", "bb": 1},
            {"n": "GLUTTONY", "bb": 1}, {"n": "THE CRYPT", "bb": 1}, {"n": "BOUNTY HUNTERS", "bb": 1}, {"n": "DJ PSYCHO", "bb": 0}, {"n": "SERIAL", "bb": 1}, {"n": "PEARL HARBOR", "bb": 1},
            {"n": "DEAD CANARY", "bb": 1}, {"n": "FOLSOM PRISON", "bb": 1}, {"n": "THE SHADOW ORDER", "bb": 0}, {"n": "WOLF RITUAL", "bb": 0}, {"n": "DRAGON TRIBE", "bb": 1}, {"n": "MANHATTAN GOES WILD", "bb": 0},
            {"n": "MAYA MAGIC", "bb": 0}, {"n": "POISON EVE", "bb": 0}
        ],
        "MICROGAMING": [
            {"n": "MEGA MOOLAH", "bb": 0}, {"n": "IMMORTAL ROMANCE", "bb": 0}, {"n": "THUNDERSTRUCK II", "bb": 0}, {"n": "9 MASKS OF FIRE", "bb": 0}, {"n": "BREAK DA BANK AGAIN", "bb": 0}, {"n": "JURASSIC PARK", "bb": 0},
            {"n": "GAME OF THRONES", "bb": 0}, {"n": "AVALON II", "bb": 0}, {"n": "BOOK OF OZ", "bb": 0}, {"n": "WHEEL OF WISHES", "bb": 0}, {"n": "ADVENTURE PALACE", "bb": 0}, {"n": "AGENT JANE BLONDE", "bb": 0},
            {"n": "ALASKAN FISHING", "bb": 0}, {"n": "ARIANA", "bb": 0}, {"n": "BASS BOSS", "bb": 0}, {"n": "BIG BAD WOLF", "bb": 0}, {"n": "BUST THE BANK", "bb": 0}, {"n": "CARNAVAL", "bb": 0},
            {"n": "COOL BUCK", "bb": 0}, {"n": "DECK THE HALLS", "bb": 0}, {"n": "DRAGONZ", "bb": 0}, {"n": "EAGLE'S WINGS", "bb": 0}, {"n": "EMPEROR OF THE SEA", "bb": 0}, {"n": "FISH PARTY", "bb": 0},
            {"n": "FOOTBALL STAR", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "FORTUNIUM", "bb": 0}, {"n": "GIRLS WITH GUNS", "bb": 0}, {"n": "GOLD FACTORY", "bb": 0}, {"n": "HALLOWEEN", "bb": 0},
            {"n": "HAPPY HOLIDAYS", "bb": 0}, {"n": "HELLBOY", "bb": 0}, {"n": "HIGHLANDER", "bb": 0}, {"n": "HITMAN", "bb": 0}, {"n": "HOT INK", "bb": 0}, {"n": "JUNGLE JIM EL DORADO", "bb": 0},
            {"n": "KATHMANDU", "bb": 0}, {"n": "KINGS OF CASH", "bb": 0}, {"n": "LADIES NITE", "bb": 0}, {"n": "LARA CROFT", "bb": 0}, {"n": "LOADED", "bb": 0}, {"n": "LOST VEGAS", "bb": 0},
            {"n": "LUCKY KOI", "bb": 0}, {"n": "LUCKY LEPRECHAUN", "bb": 0}, {"n": "LUCKY ZODIAC", "bb": 0}, {"n": "MERMAIDS MILLIONS", "bb": 0}, {"n": "PLAYBOY", "bb": 0}, {"n": "PRETTY KITTY", "bb": 0},
            {"n": "PURE PLATINUM", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "TERMINATOR 2", "bb": 0}, {"n": "TOMB RAIDER", "bb": 0}, {"n": "TREASURE NILE", "bb": 0}, {"n": "WAXY VAN GOGH", "bb": 0},
            {"n": "WICKED TALES", "bb": 0}, {"n": "WILD SCARABS", "bb": 0}, {"n": "WOLF HOWL", "bb": 0}, {"n": "AMAZING LINK ZEUS", "bb": 0}, {"n": "ANCIENT FORTUNES: ZEUS", "bb": 0}, {"n": "ASSASSIN MOON", "bb": 0},
            {"n": "AURUM CODEX", "bb": 0}, {"n": "BANANA ODYSSEY", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "BEAUTIFUL BONES", "bb": 0}, {"n": "BIG KAHUNA", "bb": 0}, {"n": "5 REEL DRIVE", "bb": 0},
            {"n": "777 ROYAL WHEEL", "bb": 0}, {"n": "A DARK MATTER", "bb": 0}, {"n": "ABSALOOTLY MAD", "bb": 0}, {"n": "AFRICAN QUEST", "bb": 0}, {"n": "AGE OF CONQUEST", "bb": 0}, {"n": "ALCHEMISTS GOLD", "bb": 0},
            {"n": "ALL WIN FC", "bb": 0}, {"n": "AMAZING LINK APOLLO", "bb": 0}, {"n": "ANCIENT FORTUNES: POSEIDON", "bb": 0}, {"n": "ARENA OF GOLD", "bb": 0}, {"n": "ARTHUR'S FORTUNE", "bb": 0}, {"n": "ATLANTIS RISING", "bb": 0},
            {"n": "AURORA WILD", "bb": 0}, {"n": "AZTEC FALLS", "bb": 0}, {"n": "BAR BAR BLACK SHEEP", "bb": 0}, {"n": "BEACH BABES", "bb": 0}, {"n": "BELIEVE IT OR NOT", "bb": 0}, {"n": "BIG TOP", "bb": 0},
            {"n": "BOOK OF ATEM", "bb": 0}, {"n": "BOOK OF CAPTAIN SILVER", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "BOOM PIRATES", "bb": 0}, {"n": "BREAK AWAY", "bb": 0}, {"n": "BREAK AWAY LUCKY WILDS", "bb": 0},
            {"n": "BULLSEYE", "bb": 0}, {"n": "BURNING DESIRE", "bb": 0}, {"n": "BUSH TELEGRAPH", "bb": 0}, {"n": "CASH OF KINGDOMS", "bb": 0}, {"n": "CASH SPLASH", "bb": 0}, {"n": "CASHVILLE", "bb": 0},
            {"n": "CAT IN VEGAS", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CENTURION", "bb": 0}, {"n": "CHICAGO GOLD", "bb": 0}
        ],
        "BNG (BOOONGO)": [
            {"n": "SUN OF EGYPT", "bb": 0}, {"n": "SUN OF EGYPT 2", "bb": 0}, {"n": "SUN OF EGYPT 3", "bb": 0}, {"n": "SUN OF EGYPT 4", "bb": 0}, {"n": "15 DRAGON PEARLS", "bb": 0}, {"n": "DRAGON PEARLS", "bb": 0},
            {"n": "MAGIC APPLE", "bb": 0}, {"n": "MAGIC APPLE 2", "bb": 0}, {"n": "TIGER JUNGLE", "bb": 0}, {"n": "HIT THE GOLD", "bb": 0}, {"n": "BLACK WOLF", "bb": 0}, {"n": "BLACK WOLF 2", "bb": 0},
            {"n": "AZTEC SUN", "bb": 0}, {"n": "GREAT PANDA", "bb": 0}, {"n": "MOON SISTERS", "bb": 0}, {"n": "BUDDHA FORTUNE", "bb": 0}, {"n": "SCARAB TEMPLE", "bb": 0}, {"n": "3 COINS", "bb": 0},
            {"n": "3 COINS EGYPT", "bb": 0}, {"n": "3 HOT CHILLIES", "bb": 0}, {"n": "WUKONG", "bb": 0}, {"n": "WOLF SAGA", "bb": 0}, {"n": "PEARL DIVER", "bb": 0}, {"n": "PEARL DIVER 2", "bb": 0},
            {"n": "QUEEN OF THE SUN", "bb": 0}, {"n": "GOLD EXPRESS", "bb": 0}, {"n": "CANDY BOOM", "bb": 0}, {"n": "GIE GIE GIE", "bb": 0}, {"n": "HAPPY FISH", "bb": 0}, {"n": "LOTUS CHARM", "bb": 0},
            {"n": "ORCHID PRINCESS", "bb": 0}, {"n": "TIGER STONE", "bb": 0}, {"n": "SUPER RICH GOD", "bb": 0}, {"n": "EYE OF GOLD", "bb": 0}, {"n": "BOOK OF SUN", "bb": 0}, {"n": "BOOK OF SUN MULTICHANCE", "bb": 0},
            {"n": "GOD'S TEMPLE", "bb": 0}, {"n": "OLYMPIAN GODS", "bb": 0}, {"n": "POISONED APPLE", "bb": 0}, {"n": "POISONED APPLE 2", "bb": 0}, {"n": "777 GEMS", "bb": 0}, {"n": "SUPREME HOT", "bb": 0},
            {"n": "STAR GEMS", "bb": 0}, {"n": "SKY GEMS", "bb": 0}, {"n": "GREEN CHILLI", "bb": 0}, {"n": "GREEN CHILLI 2", "bb": 0}, {"n": "MORE MAGIC APPLE", "bb": 0}, {"n": "OIAO MEI", "bb": 0},
            {"n": "COIN VOLCANO", "bb": 0}, {"n": "EGYPT FIRE", "bb": 0}, {"n": "RIO GEMS", "bb": 0}, {"n": "HIT MORE GOLD", "bb": 0}, {"n": "STICKY PIGGY", "bb": 0}, {"n": "GODDESS OF EGYPT", "bb": 0},
            {"n": "BOOM! BOOM! GOLD!", "bb": 0}, {"n": "AZTEC SUN", "bb": 0}, {"n": "BOOK OF SUN", "bb": 0}, {"n": "BUDDHA FORTUNE", "bb": 0}, {"n": "DRAGON PEARLS", "bb": 0}, {"n": "EYE OF GOLD", "bb": 0},
            {"n": "GOD'S TEMPLE", "bb": 0}, {"n": "GREAT PANDA", "bb": 0}, {"n": "MAGIC APPLE", "bb": 0}, {"n": "MOON SISTERS", "bb": 0}, {"n": "OLYMPIAN GODS", "bb": 0}, {"n": "POISONED APPLE", "bb": 0},
            {"n": "SCARAB TEMPLE", "bb": 0}, {"n": "SUN OF EGYPT", "bb": 0}, {"n": "TIGER STONE", "bb": 0}, {"n": "WOLF SAGA", "bb": 0}
        ],
        "BIGPOT GAMING": [
            {"n": "CRAZY HUNTER", "bb": 0}, {"n": "GOLDEN ERA", "bb": 0}, {"n": "SECRET OF RICHES", "bb": 0}, {"n": "LUCKY SEVEN", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}, {"n": "PIRATE KING", "bb": 0},
            {"n": "DRAGON LEGEND", "bb": 0}, {"n": "MAGIC FOREST", "bb": 0}, {"n": "CANDY POP", "bb": 0}, {"n": "NEON CITY", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0},
            {"n": "VIKING GLORY", "bb": 0}, {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "OCEAN'S BOUNTY", "bb": 0},
            {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "HERCULES", "bb": 0}, {"n": "ZOMBIE ATTACK", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "CHRISTMAS JOY", "bb": 0}, {"n": "LUCKY FARM", "bb": 0},
            {"n": "CASINO ROYALE", "bb": 0}, {"n": "NINJA SQUAD", "bb": 0}, {"n": "ROBOT WARS", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0},
            {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "RACING STARS", "bb": 0}, {"n": "FISHING MASTER", "bb": 0}, {"n": "FRUIT SPLASH", "bb": 0}, {"n": "DIAMOND RUSH", "bb": 0}, {"n": "PANDA WARRIOR", "bb": 0},
            {"n": "SKY GUARDIAN", "bb": 0}, {"n": "DEEP SEA", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "WILD SAFARI", "bb": 0}, {"n": "MAGIC SPELL", "bb": 0}, {"n": "LUCKY DICE", "bb": 0},
            {"n": "GOLDEN RUSH", "bb": 0}, {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "CANDY POP", "bb": 0}, {"n": "CASINO ROYALE", "bb": 0}, {"n": "CRAZY HUNTER", "bb": 0},
            {"n": "DRAGON LEGEND", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "FRUIT SPLASH", "bb": 0}, {"n": "GOLDEN ERA", "bb": 0},
            {"n": "GOLDEN RUSH", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "HERCULES", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0}, {"n": "LUCKY FARM", "bb": 0},
            {"n": "LUCKY SEVEN", "bb": 0}, {"n": "MAGIC FOREST", "bb": 0}, {"n": "MAGIC SPELL", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "NEON CITY", "bb": 0}, {"n": "NINJA SQUAD", "bb": 0},
            {"n": "OCEAN'S BOUNTY", "bb": 0}, {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "PIRATE KING", "bb": 0}, {"n": "RACING STARS", "bb": 0}, {"n": "ROBOT WARS", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0},
            {"n": "SECRET OF RICHES", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "VIKING GLORY", "bb": 0}, {"n": "WILD SAFARI", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}
        ],
        "HACKSAW GAMING": [
            {"n": "WANTED DEAD OR A WILD", "bb": 1}, {"n": "CHAOS CREW", "bb": 1}, {"n": "CHAOS CREW II", "bb": 1}, {"n": "HAND OF ANUBIS", "bb": 1}, {"n": "RIP CITY", "bb": 1}, {"n": "LE BANDIT", "bb": 1},
            {"n": "DORK UNIT", "bb": 1}, {"n": "STACK 'EM", "bb": 1}, {"n": "STICK 'EM", "bb": 0}, {"n": "TOSHI VIDEO CLUB", "bb": 0}, {"n": "DROP 'EM", "bb": 0}, {"n": "ROTTEN", "bb": 1},
            {"n": "GLADIATOR LEGENDS", "bb": 1}, {"n": "STORMFORGED", "bb": 1}, {"n": "THE BOWERY BOYS", "bb": 1}, {"n": "PUG LIFE", "bb": 1}, {"n": "ITERCH", "bb": 0}, {"n": "KING CARROT", "bb": 1},
            {"n": "JOKER BOMBS", "bb": 1}, {"n": "CUBES", "bb": 0}, {"n": "CUBES 2", "bb": 0}, {"n": "DOUBLE RAINBOW", "bb": 1}, {"n": "TASTY TREATS", "bb": 0}, {"n": "XPW", "bb": 0},
            {"n": "UNDEA FORTUNE", "bb": 0}, {"n": "FEAR THE DARK", "bb": 1}, {"n": "BEAST BELOW", "bb": 1}, {"n": "SLAYERS INC", "bb": 1}, {"n": "DARK SUMMONING", "bb": 1}, {"n": "BENNY THE BEER", "bb": 0},
            {"n": "2 WILD 2 DIE", "bb": 1}, {"n": "FEEL THE BEAT", "bb": 0}, {"n": "FIST OF DESTRUCTION", "bb": 0}, {"n": "DIVINE DROP", "bb": 0}, {"n": "RUSTY & CURLY", "bb": 1}, {"n": "CASH CREW", "bb": 1},
            {"n": "BEAM BOYS", "bb": 1}, {"n": "BARBARIAN STASH", "bb": 0}, {"n": "JAGGED STONES", "bb": 0}, {"n": "SIXSIXSIX", "bb": 1}, {"n": "OMICRON", "bb": 0}, {"n": "HOP'N'POP", "bb": 0},
            {"n": "FRUIT DUEL", "bb": 0}, {"n": "BORN WILD", "bb": 0}, {"n": "FOREST FORTUNE", "bb": 0}, {"n": "HARVEST WILD", "bb": 0}, {"n": "AZTEC TWIST", "bb": 0}, {"n": "MYSTERY MOTEL", "bb": 0},
            {"n": "SCRATCH BRONZE", "bb": 0}, {"n": "SCRATCH PLATINUM", "bb": 0}, {"n": "ALPHA EAGLE", "bb": 1}, {"n": "BLOODTHIRST", "bb": 1}, {"n": "BREAK BONES", "bb": 0}, {"n": "CASH QUEST", "bb": 0},
            {"n": "CASH-A-CABANA", "bb": 0}, {"n": "CAT CLANS", "bb": 0}, {"n": "DORK UNIT", "bb": 1}, {"n": "DOUBLE RAINBOW", "bb": 1}, {"n": "EGGSTRAVAGANZA", "bb": 0}, {"n": "EYE OF THE PANDA", "bb": 0},
            {"n": "FRUIT DUEL", "bb": 0}, {"n": "GLADIATOR LEGENDS", "bb": 1}, {"n": "HAND OF ANUBIS", "bb": 1}, {"n": "HARVEST WILD", "bb": 0}, {"n": "HOP'N'POP", "bb": 0}, {"n": "ITERERO", "bb": 0},
            {"n": "JELLY REELS", "bb": 0}, {"n": "KING CARROT", "bb": 1}, {"n": "POCKET ROCKETS", "bb": 0}, {"n": "PUG LIFE", "bb": 1}, {"n": "RIP CITY", "bb": 1}, {"n": "ROTTEN", "bb": 1},
            {"n": "STACK 'EM", "bb": 1}, {"n": "STICK 'EM", "bb": 0}, {"n": "TOSHI VIDEO CLUB", "bb": 0}, {"n": "WANTED DEAD OR A WILD", "bb": 1}, {"n": "WARRIOR WAYS", "bb": 0}, {"n": "WILD YIELD", "bb": 0},
            {"n": "XPW", "bb": 0}
        ],
        "FA CHAI": [
            {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHINESE NEW YEAR 2", "bb": 0}, {"n": "NIGHT MARKET", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "MAGIC BEANS", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}, {"n": "FORTUNE KOI", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "MONEY TREE DOZER", "bb": 0}, {"n": "COIN MANIAC", "bb": 0},
            {"n": "STAR HUNTER", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0}, {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "ANIMAL RACING", "bb": 0},
            {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "LEGEND OF DRAGON", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0}, {"n": "GRAND BLUE", "bb": 0}, {"n": "TREASURE CRUISE", "bb": 0},
            {"n": "GLORY OF ROME", "bb": 0}, {"n": "MERMAID LEGEND", "bb": 0}, {"n": "RICH MAN", "bb": 0}, {"n": "LUCKY CLOVER", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0}, {"n": "GOLDEN DRAGON", "bb": 0},
            {"n": "KA-CHING", "bb": 0}, {"n": "PONG PONG HU", "bb": 0}, {"n": "MAHJONG WAYS 3", "bb": 0}, {"n": "FORTUNE GOD", "bb": 0}, {"n": "LUCKY WHEEL", "bb": 0}, {"n": "DISCO NIGHT", "bb": 0},
            {"n": "CANDY PARTY", "bb": 0}, {"n": "JUNGLE PARTY", "bb": 0}, {"n": "CIRCUS DOZER", "bb": 0}, {"n": "LIGHTNING BOMB", "bb": 0}, {"n": "FIERCE BATTLE", "bb": 0}, {"n": "SQUID PARTY", "bb": 0},
            {"n": "ANIMAL RACING", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "COIN MANIAC", "bb": 0}, {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "FORTUNE KOI", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0}, {"n": "GRAND BLUE", "bb": 0}, {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0},
            {"n": "LEGEND OF DRAGON", "bb": 0}, {"n": "LUCKY CLOVER", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0}, {"n": "MAGIC BEANS", "bb": 0}, {"n": "MERMAID LEGEND", "bb": 0}, {"n": "MONEY TREE DOZER", "bb": 0},
            {"n": "NIGHT MARKET", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0}, {"n": "RICH MAN", "bb": 0}, {"n": "STAR HUNTER", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0},
            {"n": "TREASURE CRUISE", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}
        ],
        "JDB GAMING": [
            {"n": "BURGER SHOP", "bb": 0}, {"n": "KONGFU", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0}, {"n": "LUCKY 7", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0},
            {"n": "DRAGON MASTER", "bb": 0}, {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "KINGSMAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0},
            {"n": "FORMOSA BEAR", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0},
            {"n": "OPEN SESAME", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "MAHJONG", "bb": 0}, {"n": "BANANA SAGA", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "ZODIAC", "bb": 0},
            {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD WEST", "bb": 0}, {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "CRAZY SCIENTIST", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0},
            {"n": "MAGIC WORLD", "bb": 0}, {"n": "WONDERLAND", "bb": 0}, {"n": "HALLOWEEN PARTY", "bb": 0}, {"n": "CHRISTMAS SURPRISE", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0},
            {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "BURGER SHOP", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "DRAGON MASTER", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0},
            {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "FORMOSA BEAR", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "KONGFU", "bb": 0},
            {"n": "LUCKY 7", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "MAHJONG", "bb": 0},
            {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "OPEN SESAME", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "TREASURE BOWL", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "ZODIAC", "bb": 0}
        ],
        "PLAY'N GO": [
            {"n": "BOOK OF DEAD", "bb": 0}, {"n": "REACTOONZ", "bb": 0}, {"n": "REACTOONZ 2", "bb": 0}, {"n": "MOON PRINCESS", "bb": 0}, {"n": "MOON PRINCESS 100", "bb": 0}, {"n": "MOON PRINCESS TRINITY", "bb": 0},
            {"n": "RISE OF OLYMPUS", "bb": 0}, {"n": "RISE OF OLYMPUS 100", "bb": 0}, {"n": "GEMIX", "bb": 0}, {"n": "GEMIX 2", "bb": 0}, {"n": "FIRE JOKER", "bb": 0}, {"n": "LEGACY OF DEAD", "bb": 0},
            {"n": "TOME OF MADNESS", "bb": 0}, {"n": "HONEY RUSH", "bb": 0}, {"n": "HONEY RUSH 100", "bb": 0}, {"n": "GOLDEN TICKET", "bb": 0}, {"n": "GOLDEN TICKET 2", "bb": 0}, {"n": "SWEET ALCHEMY", "bb": 0},
            {"n": "SWEET ALCHEMY 2", "bb": 0}, {"n": "RISE OF MERLIN", "bb": 0}, {"n": "PIMPED", "bb": 0}, {"n": "XMAS JOKER", "bb": 0}, {"n": "MYSTERY JOKER", "bb": 0}, {"n": "BIG WIN CAT", "bb": 0},
            {"n": "HOT TO BURN", "bb": 0}, {"n": "BOAT BONANZA", "bb": 0}, {"n": "CLASH OF CAMELOT", "bb": 0}, {"n": "COUNT JOKULA", "bb": 0}, {"n": "DIO KILLING THE DRAGON", "bb": 0}, {"n": "CHAMPS-ELYSEES", "bb": 0},
            {"n": "CANINE CARNAGE", "bb": 0}, {"n": "USA FLIP", "bb": 0}, {"n": "SHAMROCK MINER", "bb": 0}, {"n": "WILD FALLS 2", "bb": 0}, {"n": "GRIM THE SPLITTER", "bb": 0}, {"n": "LEGACY OF INCA", "bb": 0},
            {"n": "GAME OF GLADIATORS", "bb": 0}, {"n": "SAFARI OF WEALTH", "bb": 0}, {"n": "CAT WILDE", "bb": 0}, {"n": "RICH WILDE", "bb": 0}, {"n": "AGENT DESTINY", "bb": 0}, {"n": "ANCIENT EGYPT", "bb": 0},
            {"n": "ANNIHILATOR", "bb": 0}, {"n": "AZTEC IDOLS", "bb": 0}, {"n": "AZTEC WARRIOR PRINCESS", "bb": 0}, {"n": "BAKER'S TREAT", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "7 SINS", "bb": 0},
            {"n": "ACE OF SPADES", "bb": 0}, {"n": "AGENT DESTINY", "bb": 0}, {"n": "ANCIENT EGYPT", "bb": 0}, {"n": "ANNIHILATOR", "bb": 0}, {"n": "AZTEC IDOLS", "bb": 0}, {"n": "AZTEC WARRIOR PRINCESS", "bb": 0},
            {"n": "BAKER'S TREAT", "bb": 0}, {"n": "BATTLE ROYAL", "bb": 0}, {"n": "BEAST OF WEALTH", "bb": 0}, {"n": "BELL OF FORTUNE", "bb": 0}, {"n": "BIG WIN 777", "bb": 0}, {"n": "BIG WIN CAT", "bb": 0},
            {"n": "BLACK MAMBA", "bb": 0}, {"n": "BLAZIN' BULLFROG", "bb": 0}, {"n": "BOOK OF DEAD", "bb": 0}, {"n": "BULL IN A CHINA SHOP", "bb": 0}, {"n": "CASH PUMP", "bb": 0}, {"n": "CASH VANDAL", "bb": 0},
            {"n": "CAT WILDE", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CHAMPS-ELYSEES", "bb": 0}, {"n": "CHARLIE CHANCE", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHRONOS JOKER", "bb": 0},
            {"n": "CLASH OF CAMELOT", "bb": 0}, {"n": "CLOUD QUEST", "bb": 0}, {"n": "COPS 'N' ROBBERS", "bb": 0}, {"n": "COUNT JOKULA", "bb": 0}, {"n": "COURT OF HEARTS", "bb": 0}, {"n": "COYOTE CASH", "bb": 0},
            {"n": "CRYSTAL SUN", "bb": 0}, {"n": "DAWN OF EGYPT", "bb": 0}, {"n": "DEADLY 5", "bb": 0}, {"n": "DEMON", "bb": 0}, {"n": "DERBY WHEEL", "bb": 0}, {"n": "DIAMOND VORTEX", "bb": 0},
            {"n": "DIO KILLING THE DRAGON", "bb": 0}, {"n": "DIVINE SHOWDOWN", "bb": 0}, {"n": "DOOM OF EGYPT", "bb": 0}, {"n": "DRAGON MAIDEN", "bb": 0}, {"n": "DRAGON SHIP", "bb": 0}, {"n": "EASTER EGGS", "bb": 0},
            {"n": "EGYPTIAN FORTUNE", "bb": 0}, {"n": "ENERGOONZ", "bb": 0}, {"n": "EYE OF THE ATUM", "bb": 0}, {"n": "FACES OF FREYA", "bb": 0}, {"n": "FIRE JOKER", "bb": 0}, {"n": "FIRE JOKER FREEZE", "bb": 0},
            {"n": "FIRE TOAD", "bb": 0}, {"n": "FORGE OF FORTUNES", "bb": 0}, {"n": "FORTUNE REWIND", "bb": 0}, {"n": "FROZEN GEMS", "bb": 0}, {"n": "GAME OF GLADIATORS", "bb": 0}, {"n": "GEMIX", "bb": 0},
            {"n": "GHOST OF DEAD", "bb": 0}, {"n": "GIGANTUANZ", "bb": 0}, {"n": "GOLD KING", "bb": 0}, {"n": "GOLD TROPHY 2", "bb": 0}, {"n": "GOLD VOLCANO", "bb": 0}, {"n": "GOLDEN TICKET", "bb": 0},
            {"n": "GRIM THE SPLITTER", "bb": 0}, {"n": "GUNSLINGER", "bb": 0}, {"n": "HALLOWEEN JACK", "bb": 0}, {"n": "HAPPY HALLOWEEN", "bb": 0}, {"n": "HOLIDAY SPIRITS", "bb": 0}, {"n": "HONEY RUSH", "bb": 0},
            {"n": "HOT TO BURN", "bb": 0}, {"n": "HOTEL YETI-WAY", "bb": 0}, {"n": "HOUSE OF DOOM", "bb": 0}, {"n": "HUGO", "bb": 0}, {"n": "HUGO 2", "bb": 0}, {"n": "ICE JOKER", "bb": 0},
            {"n": "IDOL OF FORTUNE", "bb": 0}, {"n": "IMMORTAL GUILD", "bb": 0}, {"n": "INFERNO STAR", "bb": 0}, {"n": "IRON GIRL", "bb": 0}, {"n": "ISHIN", "bb": 0}, {"n": "IT'S MAGIC", "bb": 0},
            {"n": "JACKPOT POKER", "bb": 0}, {"n": "JADE MAGICIAN", "bb": 0}, {"n": "JEWEL BOX", "bb": 0}, {"n": "JOLLY ROGER", "bb": 0}, {"n": "JOLLY ROGER 2", "bb": 0}, {"n": "KISS REELS OF ROCK", "bb": 0},
            {"n": "KNIGHT'S LIFE", "bb": 0}, {"n": "KRAKEN'S SKY", "bb": 0}, {"n": "LADY OF FORTUNE", "bb": 0}, {"n": "LEGACY OF DEAD", "bb": 0}, {"n": "LEGACY OF EGYPT", "bb": 0}, {"n": "LEGACY OF INCA", "bb": 0},
            {"n": "LEPRECHAUN GOES EGYPT", "bb": 0}, {"n": "LEPRECHAUN GOES HELL", "bb": 0}, {"n": "LEPRECHAUN GOES TO WILD", "bb": 0}, {"n": "LORD MERLIN", "bb": 0}, {"n": "LOVE IS IN THE AIR", "bb": 0}, {"n": "LUCKY DIAMONDS", "bb": 0},
            {"n": "MADAME DESTINY", "bb": 0}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "MAGICAL STACKS", "bb": 0}, {"n": "MAHJONG 88", "bb": 0}, {"n": "MERMAID'S DIAMOND", "bb": 0}, {"n": "METAL DETECTOR", "bb": 0},
            {"n": "MOON PRINCESS", "bb": 0}, {"n": "MOON PRINCESS 100", "bb": 0}, {"n": "MOON PRINCESS TRINITY", "bb": 0}, {"n": "MOUNTAIN OF WEALTH", "bb": 0}, {"n": "MUERTO EN MITLAN", "bb": 0}, {"n": "MULTIFRUIT 81", "bb": 0},
            {"n": "MYSTERY JOKER", "bb": 0}, {"n": "MYSTERY JOKER 6000", "bb": 0}, {"n": "NINJA FRUITS", "bb": 0}, {"n": "NYX", "bb": 0}, {"n": "OCTOPUS TREASURE", "bb": 0}, {"n": "ODIN: PROTECTOR OF REALMS", "bb": 0},
            {"n": "PAPYRUS", "bb": 0}, {"n": "PEARLS OF INDIA", "bb": 0}, {"n": "PERFECT GEMS", "bb": 0}, {"n": "PHOENIX REBORN", "bb": 0}, {"n": "PIGGY BANK", "bb": 0}, {"n": "PIMPED", "bb": 0},
            {"n": "PIXIES VS PIRATES", "bb": 0}, {"n": "PLANET FORTUNE", "bb": 0}, {"n": "PROSPERITY PALACE", "bb": 0}, {"n": "QUEEN'S DAY TILT", "bb": 0}, {"n": "RABBIT HOLE RICHES", "bb": 0}, {"n": "RAGING REX", "bb": 0},
            {"n": "RAGING REX 2", "bb": 0}, {"n": "RAINBOW CHARMS", "bb": 0}, {"n": "REACTOONZ", "bb": 0}, {"n": "REACTOONZ 2", "bb": 0}, {"n": "REEL STEAL", "bb": 0}, {"n": "RICH WILDE", "bb": 0},
            {"n": "RISE OF DEAD", "bb": 0}, {"n": "RISE OF MERLIN", "bb": 0}, {"n": "RISE OF OLYMPUS", "bb": 0}, {"n": "RISE OF OLYMPUS 100", "bb": 0}, {"n": "RITUAL RESURRECTION", "bb": 0}, {"n": "ROCCO GALLO", "bb": 0},
            {"n": "ROCK-N-ROLLA", "bb": 0}, {"n": "RONIN", "bb": 0}, {"n": "ROYAL MASQUERADE", "bb": 0}, {"n": "SABATON", "bb": 0}, {"n": "SAFARI OF WEALTH", "bb": 0}, {"n": "SAILS OF GOLD", "bb": 0},
            {"n": "SAMURAI KEN", "bb": 0}, {"n": "SEA HUNTER", "bb": 0}, {"n": "SECRET OF THE STONES", "bb": 0}, {"n": "SHAMROCK MINER", "bb": 0}, {"n": "SINS", "bb": 0}, {"n": "SMILEY'S", "bb": 0},
            {"n": "SPACE RACE", "bb": 0}, {"n": "SPARKY & SHORTZ", "bb": 0}, {"n": "SPEED CASH", "bb": 0}, {"n": "STAR BLAST", "bb": 0}, {"n": "STICKY JOKER", "bb": 0}, {"n": "STREET MAGIC", "bb": 0},
            {"n": "SUPER FLIP", "bb": 0}, {"n": "SWEET ALCHEMY", "bb": 0}, {"n": "SWEET ALCHEMY 2", "bb": 0}, {"n": "SWORD AND THE GRAIL", "bb": 0}, {"n": "TALES OF ASGARD", "bb": 0}, {"n": "TEMPLE OF WEALTH", "bb": 0},
            {"n": "TESTAMENT", "bb": 0}, {"n": "THAT'S RICH", "bb": 0}, {"n": "THE LAST SUNDOWN", "bb": 0}, {"n": "THE SWORD AND THE GRAIL", "bb": 0}, {"n": "THUNDER SCREECH", "bb": 0}, {"n": "TOME OF MADNESS", "bb": 0},
            {"n": "TROLL HUNTERS", "bb": 0}, {"n": "TROLL HUNTERS 2", "bb": 0}, {"n": "TWISTED SISTER", "bb": 0}, {"n": "USA FLIP", "bb": 0}, {"n": "VIKING RUNECRAFT", "bb": 0}, {"n": "WILD BLOOD", "bb": 0},
            {"n": "WILD BLOOD 2", "bb": 0}, {"n": "WILD FALLS", "bb": 0}, {"n": "WILD FALLS 2", "bb": 0}, {"n": "WILD FRAMES", "bb": 0}, {"n": "WILD MELON", "bb": 0}, {"n": "WILD NORTH", "bb": 0},
            {"n": "WIN-A-BEEST", "bb": 0}, {"n": "XMAS JOKER", "bb": 0}, {"n": "XMAS MAGIC", "bb": 0}
        ]
}

PROVIDERS_DATA = {
    "BINGOPLUS ": DEFAULT_PROVIDERS_DATA,
    "AGILA CLUB": PROVIDERS_DATA_2,
    "PLAYTIME": PROVIDERS_DATA_2,
    "JILIBET": PROVIDERS_DATA_2,
    "TIKLUCK (new)": PROVIDERS_DATA_2,
    "GD ENEMERALD": PROVIDERS_DATA_3,
    "MACALLAN77": PROVIDERS_DATA_2,
    "INFERNO PLAY": PROVIDERS_DATA_2,
    "BUGATTI PLAY ": PROVIDERS_DATA_2,
    "MASERATI PLAY": PROVIDERS_DATA_2,
    "LOTUS PLAY": PROVIDERS_DATA_2,
    "LAMBO PLAY": DEFAULT_PROVIDERS_DATA
}
SIGNALS = [
    "ðŸŸ¢\n10 Normal Spins -> 30 Turbo Spins",
    "ðŸŸ¡\n5 Quick Spins -> 15 Normal Spins",
    "ðŸ”¥\n30 Turbo Spins then Buy Bonus",
    "ðŸš€\n10 Turbo Spins -> 10 Quick Spins -> 5 Normal Spins then Buy Bonus",
    "ðŸ’Ž\n20 Normal Spins then Add 1 peso bet and Buy Bonus",
    "âš¡\n50 Turbo Spins (Low Stake)",
    "â­\n8 Normal Spins -> 15 Quick Spins -> 10 Turbo Spins",
    "ðŸ€\n7 Normal Spins -> 7 Turbo Spins -> 7 Quick Spins then Buy Bonus",
    "ðŸŽ°\n15 Normal Spins -> 20 Turbo Spins -> 5 Quick Spins",
    "ðŸŽ¡\n12 Quick Spins -> 12 Normal Spins -> 12 Turbo Spins",
    "ðŸŒŠ\n25 Turbo Spins -> 10 Normal Spins",
    "ðŸŒ‹\n5 Normal Spins -> 5 Quick Spins -> 5 Turbo Spins -> Buy Bonus",
    "ðŸŒ™\n40 Turbo Spins (Medium Stake)",
    "â˜€ï¸\n10 Normal Spins -> 10 Turbo Spins -> 10 Quick Spins",
    "ðŸ‰\n18 Turbo Spins -> 12 Normal Spins",
    "ðŸ¦\n30 Quick Spins",
    "ðŸ\n9 Normal Spins -> 18 Turbo Spins -> 9 Quick Spins",
    "ðŸ¦…\n15 Turbo Spins -> 15 Quick Spins",
    "ðŸ¦„\n22 Normal Spins -> 11 Turbo Spins",
    "ðŸŒˆ\n7 Turbo Spins -> 7 Normal Spins -> 7 Quick Spins -> 7 Turbo Spins",
    "âš¡\n50 Quick Spins",
    "â„ï¸\n20 Turbo Spins -> 20 Normal Spins",
    "ðŸŒµ\n10 Quick Spins -> 20 Turbo Spins",
    "ðŸ°\n15 Normal Spins -> 15 Turbo Spins",
    "ðŸ´â€â˜ ï¸\n30 Turbo Spins -> Buy Bonus",
    "ðŸ›¸\n10 Turbo Spins -> 10 Quick Spins -> 10 Normal Spins",
    "ðŸ§ª\n5 Normal Spins -> 10 Turbo Spins -> 15 Quick Spins",
    "ðŸ¥Š\n20 Quick Spins -> 10 Turbo Spins",
    "ðŸŽï¸\n60 Turbo Spins",
    "ðŸ¹\n12 Normal Spins -> 24 Turbo Spins",
    "ðŸ•¯ï¸\n15 Quick Spins -> 15 Normal Spins",
    "ðŸ’Ž\n10 Turbo Spins -> 10 Quick Spins -> 10 Normal Spins -> Buy Bonus",
    "ðŸ’\n20 Normal Spins -> 10 Turbo Spins",
    "ðŸ‹\n30 Quick Spins",
    "ðŸ‡\n15 Turbo Spins -> 15 Quick Spins",
    "ðŸ‰\n25 Normal Spins",
    "ðŸ””\n10 Normal Spins -> 20 Turbo Spins",
    "ðŸƒ\n15 Quick Spins -> 15 Turbo Spins",
    "ðŸ‘‘\n5 Normal Spins -> 5 Quick Spins -> 5 Turbo Spins -> 5 Normal Spins",
    "ðŸ’°\n40 Turbo Spins",
    "ðŸ¦\n20 Quick Spins -> 20 Turbo Spins",
    "ðŸ’Ž\n10 Normal Spins -> 30 Quick Spins",
    "ðŸ•µï¸\n15 Turbo Spins -> 15 Normal Spins",
    "ðŸ§™\n10 Quick Spins -> 10 Turbo Spins -> 10 Normal Spins",
    "ðŸ§š\n25 Turbo Spins",
    "ðŸ§œ\n12 Normal Spins -> 12 Quick Spins",
    "ðŸ§ž\n30 Turbo Spins -> Buy Bonus",
    "ðŸ§›\n20 Quick Spins -> 10 Normal Spins",
    "ðŸº\n15 Turbo Spins -> 15 Quick Spins -> 15 Normal Spins",
    "ðŸ¦Š\n15 Normal Spins -> 15 Turbo Spins -> 15 Quick Spins",
    "ðŸ”¥\n10 Normal Spins -> 20 Quick Spins -> Buy Bonus",
    "ðŸ’Ž\n30 Quick Spins -> Buy Bonus",
    "ðŸš€\n15 Normal Spins -> Buy Bonus",
    "ðŸŒ€\n15 Turbo Spins -> 15 Normal Spins",
    "ðŸŒŒ\n20 Quick Spins -> 10 Turbo Spins -> 20 Normal Spins",
    "âš¡\n35 Turbo Spins -> 5 Quick Spins",
    "ðŸŒªï¸\n10 Normal -> 20 Quick -> 10 Turbo",
    "â˜„ï¸\n45 Turbo Spins",
    "ðŸŒ \n8 Normal -> 8 Quick -> 8 Turbo -> 8 Normal",
    "ðŸŒŠ\n25 Quick Spins -> 25 Turbo Spins",
    "ðŸ”¥\n15 Normal -> 30 Turbo",
    "ðŸ§Š\n30 Quick -> 10 Normal",
    "ðŸƒ\n50 Normal Spins (Low Stake)",
    "ðŸŽ\n12 Quick -> 12 Turbo -> 12 Normal",
    "ðŸŽ‹\n20 Turbo -> 20 Quick",
    "ðŸ®\n15 Normal -> 15 Quick -> 15 Turbo",
    "â›©ï¸\n33 Turbo Spins",
    "ðŸ§§\n10 Normal -> 10 Quick -> 10 Turbo -> 10 Normal",
    "ðŸ¯\n40 Quick Spins",
    "ðŸŽ´\n18 Turbo -> 18 Normal",
    "ðŸŽ\n22 Quick -> 11 Turbo",
    "ðŸ”ï¸\n10 Normal -> 40 Turbo",
    "ðŸŒ‹\n30 Quick -> 30 Turbo",
    "ðŸœï¸\n15 Normal -> 15 Turbo -> 15 Quick",
    "ðŸï¸\n25 Turbo -> 25 Normal",
    "ðŸžï¸\n20 Quick -> 20 Normal",
    "ðŸŒ‰\n12 Turbo -> 12 Quick -> 12 Normal -> 12 Turbo",
    "ðŸŒƒ\n55 Turbo Spins",
    "ðŸ™ï¸\n15 Quick -> 45 Turbo",
    "ðŸŽ¡\n10 Normal -> 10 Quick -> 10 Turbo -> 10 Quick -> 10 Normal",
    "ðŸŽ \n30 Normal -> 30 Quick",
    "ðŸŽ¢\n20 Turbo -> 10 Quick -> 20 Turbo",
    "ðŸš‚\n50 Turbo Spins",
    "ðŸŒ™\n20 Normal Spins -> 10 Turbo Spins -> 15 Quick Spins",
    "ðŸ…\n8 Turbo Spins -> 12 Quick Spins -> 8 Turbo Spins -> 8 Normal Spins",
    "ðŸ¦…\n14 Normal Spins -> 28 Turbo Spins",
    "ðŸ¦‚\n30 Quick Spins -> 20 Normal Spins -> Buy Bonus",
    "ðŸ’Ž\n16 Turbo Spins -> 16 Normal Spins",
    "ðŸŒ‹\n25 Normal Spins -> 25 Turbo Spins",
    "ðŸŒ²\n10 Turbo Spins -> 15 Normal Spins -> 20 Quick Spins",
    "ðŸƒ\n35 Quick Spins -> 15 Normal Spins",
    "ðŸ˜\n5 Normal Spins -> 15 Quick Spins -> 25 Turbo Spins -> 5 Normal Spins",
    "ðŸ¦ˆ\n40 Turbo Spins -> 10 Normal Spins",
    "ðŸ™\n18 Quick Spins -> 18 Turbo Spins",
    "ðŸ‰\n12 Normal Spins -> 24 Turbo Spins -> 12 Quick Spins",
    "ðŸ¼\n20 Normal Spins -> 20 Quick Spins",
    "ðŸ€\n7 Turbo Spins -> 14 Quick Spins -> 21 Normal Spins",
    "ðŸŒˆ\n30 Turbo Spins -> 30 Normal Spins",
    "âš¡\n15 Quick Spins -> 15 Normal Spins -> 15 Turbo Spins",
    "ðŸš‚\n50 Quick Spins",
    "ðŸš€\n22 Turbo Spins -> 11 Normal Spins",
    "ðŸŒ\n10 Normal Spins -> 30 Quick Spins -> 10 Turbo Spins",
    "ðŸŒ \n45 Turbo Spins (Medium Stake)",
    "ðŸŒž\n20 Quick Spins -> 10 Normal Spins -> 20 Turbo Spins",
    "ðŸ¦‡\n30 Normal Spins",
    "ðŸ•¸ï¸\n15 Turbo Spins -> 30 Normal Spins",
    "ðŸ”®\n5 Quick Spins -> 5 Turbo Spins -> 5 Normal Spins -> Buy Bonus",
    "ðŸ§ª\n12 Normal Spins -> 12 Turbo Spins -> 12 Quick Spins -> 12 Normal Spins",
    "ðŸ—ï¸\n40 Normal Spins",
    "ðŸ§²\n18 Turbo Spins -> 18 Quick Spins -> 18 Normal Spins",
    "ðŸŽ­\n25 Turbo Spins -> 25 Normal Spins",
    "ðŸŽ©\n10 Quick Spins -> 20 Turbo Spins",
    "ðŸƒ\n15 Normal Spins -> 10 Quick Spins -> 15 Turbo Spins",
    "ðŸ°\n20 Normal Spins -> 20 Turbo Spins",
    "ðŸ‘‘\n50 Normal Spins -> Buy Bonus",
    "ðŸ¹\n30 Quick Spins -> 30 Normal Spins",
    "âš”ï¸\n15 Turbo Spins -> 15 Normal Spins -> Buy Bonus",
    "ðŸ›¡ï¸\n40 Turbo Spins -> 20 Normal Spins",
    "ðŸº\n10 Normal Spins -> 10 Turbo Spins -> 10 Normal Spins -> 10 Quick Spins",
    "ðŸ›ï¸\n25 Turbo Spins -> 15 Quick Spins -> 10 Normal Spins",
    "ðŸ“œ\n20 Quick Spins -> 40 Normal Spins",
    "ðŸª\n15 Normal Spins -> 30 Quick Spins",
    "ðŸ\n10 Turbo Spins -> 5 Quick Spins -> 15 Normal Spins -> 10 Turbo Spins",
    "ðŸ¦‚\n45 Normal Spins",
    "ðŸ¦œ\n12 Quick Spins -> 24 Normal Spins",
    "ðŸ¦\n30 Turbo Spins -> 10 Quick Spins -> 10 Normal Spins",
    "ðŸŠ\n20 Normal Spins -> 15 Turbo Spins -> 5 Quick Spins -> 10 Normal Spins",
    "ðŸ¦“\n15 Turbo Spins -> 15 Quick Spins -> 30 Normal Spins",
    "ðŸ¦’\n35 Normal Spins -> 15 Turbo Spins",
    "ðŸ˜\n25 Quick Spins -> 25 Normal Spins",
    "ðŸš™\n10 Normal Spins -> 20 Turbo Spins -> 30 Quick Spins",
    "ðŸ§­\n16 Normal Spins -> 16 Turbo Spins -> 16 Quick Spins",
    "ðŸ—ºï¸\n8 Quick Spins -> 8 Normal Spins -> 8 Turbo Spins -> 8 Normal Spins"
]

# ================= ANIMATION LOGIC =================
def system_startup_animation(chat_id, message_id):
    # Professional Startup Animation
    steps = [
        "âš™ï¸ <b>INITIALIZING SYSTEM...</b>",
        "ðŸ§¬ <b>LOADING MODULES...</b>",
        "ðŸ” <b>BYPASSING SECURITY...</b>",
        "ðŸ“¡ <b>CONNECTING TO DATABASE...</b>",
        "âœ… <b>SYSTEM READY</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.8)
        except: pass

def logout_animation(chat_id, message_id):
    steps = [
        "ðŸ”´ <b>LOGGING OUT...</b>",
        "ðŸ”´ <b>DISCONNECTING FROM SERVER...</b>",
        "ðŸ”´ <b>CLEARING SESSION DATA...</b>",
        "ðŸ”´ <b>SESSION TERMINATED.</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.6)
        except: pass

def reset_animation(chat_id, message_id):
    steps = [
        "ðŸ”„ <b>REBOOTING SYSTEM...</b>",
        "ðŸ”„ <b>WIPING TEMPORARY CACHE...</b>",
        "ðŸ”„ <b>RECALIBRATING RNG SENSORS...</b>",
        "ðŸ”„ <b>HARD RESET COMPLETE.</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.6)
        except: pass

def display_provider_games(chat_id, uid, provider_name):
    user_sessions[uid]["provider"] = provider_name
    display_games = PROVIDERS_DATA.get(provider_name, [])

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("ðŸ”™ BACK"))
    kb.add(*[types.KeyboardButton(g) for g in display_games])

    msg = bot.send_message(chat_id, f"ðŸŽ° <b>{provider_name}</b>\nShowing {len(display_games)} Games Available:", reply_markup=kb, parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id

def live_encoding_animation(chat_id, message_id, uid, selected_casino, session_id):
    # Recreate the inline keyboard so it stays visible during animation
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(
        types.InlineKeyboardButton("ðŸ‘ï¸ SHOW PATTERN", callback_data="show_pattern"),
        types.InlineKeyboardButton("ðŸ”„ Re-Generate Pattern", callback_data="run_gen"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO GAMES", callback_data="change_game"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO PROVIDERS", callback_data="open_menu"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO CASINOS", callback_data="change_platform")
    )

    # Initial Delay with Message
    try:
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        bot.edit_message_text(
            f"{res_text}\n\nâš ï¸ <b>INITIATING INJECTION PROTOCOL...</b>", 
            chat_id, message_id, parse_mode="HTML", reply_markup=inline_kb
        )
    except: pass
    time.sleep(1.5)

    # Professional "Hacking" Frames
    frames = [
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â–¡â–¡â–¡â–¡â–¡â–¡â–¡â–¡â–¡] 10%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â–¡â–¡â–¡â–¡â–¡â–¡â–¡] 30%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â–¡â–¡â–¡â–¡â–¡] 50%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â– â– â–¡â–¡â–¡] 70%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â– â– â– â– â–¡] 90%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â– â– â– â– â– ] 100%</code>",
        f"ðŸŸ¢ <b>SIGNAL LIVE & SYNCED</b>",
        f"ðŸŸ¢ <b>STATUS: ACTIVE & SECURE</b>",
        f"ðŸŸ¢ <b>RNG DATA STREAMING...</b>"
    ]
    
    for frame in frames:
        if uid not in user_sessions or user_sessions[uid].get("encoding") == False or user_sessions[uid].get("encoding_id") != session_id:
            break
        try:
            res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n{frame}",
                parse_mode="HTML",
                reply_markup=inline_kb
            )
        except Exception as e:
            break 
        time.sleep(1.0)

    # After animation ends, set encoding to false so it doesn't try to update again
    if uid in user_sessions and user_sessions[uid].get("encoding_id") == session_id:
        user_sessions[uid]["encoding"] = False

# ================= HELPERS =================
def delete_user_past_msg(chat_id, uid):
    if user_sessions.get(uid, {}).get("last_msg"):
        try: 
            bot.delete_message(chat_id, user_sessions[uid]["last_msg"])
        except: 
            pass

# Handlers removed to avoid duplication with multi-casino logic
# Old main_menu, show_games, pick_game moved to App.tsx generation

# ================= ADMIN COMMANDS =================
@bot.message_handler(commands=["protect"])
def protect_toggle_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    new_val = not PROTECT_CONTENT
    save_protect_setting(new_val)
    status = "ENABLED (Bawal i-copy at i-forward)" if new_val else "DISABLED (Pwede nang i-copy/i-forward)"
    bot.send_message(admin_id_val, f"ðŸ‘®â€â™‚ï¸ <b>PROTECT CONTENT TOGGLED</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nStatus: <b>{status}</b>", parse_mode="HTML")

@bot.message_handler(commands=["protecton"])
def protect_on_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    save_protect_setting(True)
    bot.send_message(admin_id_val, "ðŸ‘®â€â™‚ï¸ <b>PROTECT CONTENT ENABLED</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nHindi na pwedeng i-copy o i-forward ang mga messages ng bot.", parse_mode="HTML")

@bot.message_handler(commands=["protectoff"])
def protect_off_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    save_protect_setting(False)
    bot.send_message(admin_id_val, "ðŸ‘®â€â™‚ï¸ <b>PROTECT CONTENT DISABLED</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nPwede nang i-copy, i-save at i-forward ang mga messages.", parse_mode="HTML")

@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
        
    if message.from_user.id != admin_id_val: return
    total = len(user_ids)
    bot.send_message(admin_id_val, f"ðŸ“Š <b>BOT STATISTICS</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ‘¥ <b>Total Users:</b> {total}", parse_mode="HTML")

@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
        
    if message.from_user.id != admin_id_val: 
         return
    
    # Notify admin that broadcast is starting
    status_msg = bot.send_message(admin_id_val, "ðŸ›° <b>Broadcasting started...</b>", parse_mode="HTML")
    
    target_msg = None
    text_to_send = None
    if message.reply_to_message:
        target_msg = message.reply_to_message
    else:
        command_parts = message.text.split(None, 1)
        if len(command_parts) < 2:
            bot.edit_message_text("âŒ <b>Usage:</b>\n1. Reply to any message with <code>/broadcast</code>\n2. <code>/broadcast Your message here</code>", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
            return
        text_to_send = command_parts[1]

    # Run broadcast in a separate thread to avoid blocking the bot
    import threading
    def run_broadcast():
        success = 0
        failed = 0
        all_uids = list(user_ids)
        total = len(all_uids)
        
        for i, uid in enumerate(all_uids):
            if uid == admin_id_val: continue
            try:
                if target_msg:
                    # copy_message with protect_content
                    bot.copy_message(uid, message.chat.id, target_msg.message_id, protect_content=PROTECT_CONTENT)
                else:
                    # send_message with protect_content
                    bot.send_message(uid, text_to_send, parse_mode="HTML", protect_content=PROTECT_CONTENT)
                success += 1
            except Exception as e:
                # Handle rate limits if needed (429)
                if hasattr(e, 'error_code') and e.error_code == 429:
                    import time
                    time.sleep(2) # Basic wait for rate limit
                failed += 1
            
            # Periodic update for admin every 100 users or at the end
            if (i + 1) % 100 == 0 or (i + 1) == total:
                try:
                    progress = (
                        f"ðŸ›° <b>Broadcasting...</b>\n"
                        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                        f"ðŸ‘¥ <b>Processed:</b> {i+1}/{total}\n"
                        f"âœ… <b>Success:</b> {success}\n"
                        f"âŒ <b>Failed:</b> {failed}"
                    )
                    bot.edit_message_text(progress, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
                except: pass
            
            # Tiny delay to avoid aggressive flooding
            import time
            time.sleep(0.05)
            
        final_report = (
            f"ðŸ“¢ <b>BROADCAST REPORT</b>\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"âœ… <b>Success:</b> {success}\n"
            f"âŒ <b>Failed:</b> {failed}\n"
            f"ðŸ‘¥ <b>Total Users:</b> {total}"
        )
        try:
            bot.edit_message_text(final_report, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
        except:
            bot.send_message(admin_id_val, final_report, parse_mode="HTML")

    threading.Thread(target=run_broadcast, daemon=True).start()

# ================= HANDLERS =================
@bot.message_handler(commands=["AgilaClub"])
def agilaclub_cmd(message):
    uid = message.from_user.id
    
    # Check if new for Admin Notification
    is_new = uid not in user_ids
    save_user(uid)
    
    # Delete previous bot message to keep chat clean
    delete_user_past_msg(message.chat.id, uid)
    
    if uid not in user_sessions:
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": True}
    else:
        user_sessions[uid]["is_logged_in"] = True

    # Notify Admin ONLY if truly new session
    if is_new:
        try:
            admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
            if admin_id_val:
                username_str = f" (@{message.from_user.username})" if message.from_user.username else ""
                bot.send_message(admin_id_val, f"ðŸ†• <b>NEW USER STARTED BOT</b>\nUser: {message.from_user.first_name}{username_str}\nID: <code>{uid}</code>", parse_mode="HTML")
        except: pass

    # Find the matching "AGILA CLUB" casino in CASINO_DATA
    selected_casino = "AGILA CLUB"
    for c in CASINO_DATA.keys():
        if "AGILA" in c.upper().replace(" ", ""):
            selected_casino = c
            break
            
    user_sessions[uid]["casino"] = selected_casino
    
    # Show SYSTEM CHECK animation
    msg = bot.send_message(message.chat.id, "âš™ï¸ <b>SYSTEM CHECK...</b>", parse_mode="HTML")
    system_startup_animation(message.chat.id, msg.message_id)
    try:
        bot.delete_message(message.chat.id, msg.message_id)
    except:
        pass
        
    main_menu(message.chat.id, uid)

@bot.message_handler(commands=["start"])
def start_cmd(message):
    uid = message.from_user.id
    
    # Check if new for Admin Notification
    is_new = uid not in user_ids
    save_user(uid)
    
    # Delete previous bot message to keep chat clean
    delete_user_past_msg(message.chat.id, uid)
    
    if uid not in user_sessions:
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": False}

    # Notify Admin ONLY if truly new session
    if is_new:
        try:
            admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
            if admin_id_val:
                username_str = f" (@{message.from_user.username})" if message.from_user.username else ""
                bot.send_message(admin_id_val, f"ðŸ†• <b>NEW USER STARTED BOT</b>\nUser: {message.from_user.first_name}{username_str}\nID: <code>{uid}</code>", parse_mode="HTML")
        except: pass

    # INTRO SCREEN (Always show this)
    user_fullname = (f"{message.from_user.first_name} {message.from_user.last_name}".strip() if message.from_user.last_name else message.from_user.first_name)
    
    teleclaw_thinking(message.chat.id, "Working", duration=2)

    caption = (
        f"Magandang araw, {user_fullname}!\n\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "ðŸ›¡ï¸ <b>ð’ð‹ðŽð“ ð‰ð€ð‚ðŠððŽð“ ð‘ð„ð€ðƒð„ð‘ ð¯5.5 (ð‹ðˆð•ð„ ð”ððƒð€ð“ð„)</b>\n\n"
        "Welcome to the most advanced <b>RNG Pattern Recognition & Seed Audit System</b>. Ang aming upgraded deep-learning architecture ay sumusuporta sa real-time seed analysis at live platform accuracy auditing.\n\n"
        "ðŸ“Š <b>ð™‡ð™žð™«ð™š ð™ð™‰ð™‚ ð™Žð™šð™šð™™ ð˜¼ð™ªð™™ð™žð™©:</b> Nasusuri ang real-time accuracy metrics at server response bago magsimula.\n"
        "ðŸ”¹ <b>ð™ð™šð™–ð™¡-ð™ð™žð™¢ð™š ð™Žð™šð™šð™™ ð™ð™§ð™–ð™˜ð™ ð™žð™£ging:</b> Pagbasa ng live RNG sequences na may active session synchronization.\n"
        "ðŸ”¹ <b>ð˜¿ð™®ð™£ð™–ð™¢ð™žð™˜ ð™‹ð™–ð™©ð™©ð™šð™§ð™£ ð™„ð™£ð™Ÿð™šð™˜ð™©ð™žð™¤ð™£:</b> Nagbibigay ng pinakamainam na spin sequences na may 99.8% precision rate.\n\n"
        "ðŸš€ <b>Pindutin ang Start JACKPOT READER upang tignan ang live na datos at i-initialize ang system...</b>"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not user_sessions[uid].get("is_logged_in"):
        kb.add(
            types.InlineKeyboardButton("ðŸš€ Start JACKPOT READER", callback_data="user_login")
        )
    else:
        kb.add(types.InlineKeyboardButton("ðŸš€ INITIALIZE SYSTEM", callback_data="intro_proceed"))

    kb.add(types.InlineKeyboardButton("â“ How to use the system?", callback_data="how_to_use"))

    try:
        msg = bot.send_photo(message.chat.id, INTRO_IMAGE_URL, caption=caption, reply_markup=kb, parse_mode="HTML")
    except:
        msg = bot.send_message(message.chat.id, caption, reply_markup=kb, parse_mode="HTML")

    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "how_to_use")
def handle_how_to_use(call):
    uid = call.from_user.id
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    delete_user_past_msg(call.message.chat.id, uid)
    
    teleclaw_thinking(call.message.chat.id, "Working", duration=2, call_id=call.id)
    
    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("ðŸ”™ BACK TO HOME", callback_data="back_to_home")
    )
    
    how_to_use_text = (
        "ðŸ“ˆ <b>SYSTEM INTEGRATION & OPERATIONS GUIDE</b>\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "Upang matiyak ang pinakamataas na accuracy rate at optimal seed synchronization, mangyaring sundin ang opisyal at propesyonal na pamamaraan ng ating tracking software:\n\n"
        "1ï¸âƒ£ <b>PERFORM LIVE RNG AUDIT</b>\n"
        "â€¢ I-click ang <b>Start JACKPOT READER</b> sa pangunahing screen.\n"
        "â€¢ Pindutin ang ðŸ“Š <b>CHECK LIVE RNG ANALYSIS</b> upang masuri ang kasalukuyang flow accuracy at system stability metrics, bago mag-click sa <b>PROCEED TO SYSTEM</b>.\n\n"
        "2ï¸âƒ£ <b>PLATFORM SELECTION (CASINO DATABASE)</b>\n"
        "â€¢ Piliin ang iyong nilalaruang verified Casino Platform sa listahan upang ma-load ng aming AI engine ang tamang live seed configuration na angkop sa server parameters.\n\n"
        "3ï¸âƒ£ <b>PLATFORM SYNCHRONIZATION (LOGIN/REGISTER)</b>\n"
        "â€¢ Gamitin ang <b>LOG IN TO START</b> upang buksan ang opisyal at secure-linked system portal.\n"
        "â€¢ <i>Paalala:</i> Napakahalagang gumamit ng system link upang direktang magka-cohere at maisabay ng aming server-side seed reader ang pattern cycle sa mismong active session ng iyong account.\n\n"
        "4ï¸âƒ£ <b>MODULE ARCHITECTURE & GAME SELECTION</b>\n"
        "â€¢ Pagkatapos ma-synchronize ng session, magbalik sa Bot at pindutin ang <b>PROCEED TO SYSTEM</b>.\n"
        "â€¢ Piliin ang iyong nais na Provider at i-select ang partikular na laro na iyong sinisimulan.\n\n"
        "5ï¸âƒ£ <b>DEPLOY PATTERN SEQUENCE</b>\n"
        "â€¢ Pindutin ang <b>SHOW PATTERN</b> upang ma-evaluate ang real-time RTP rate at tamang timing (e.g., Quick Spin, Turbo, o Manual Spacing).\n"
        "â€¢ Sundin nang tumpak ang algorithmic sequence upang maidirekta ang RNG seeds patunud sa high-probability jackpot trigger zones.\n\n"
        "ðŸ›¡ï¸ <b>STANDARD SAFETY & PERFORMANCE PROTOCOLS:</b>\n"
        "â€¢ Huwag ibahagi ang iyong active tracker telemetry upang mapanatili the server seed integrity.\n"
        "â€¢ Kung nagbago ang rhythm ng server, gamitin ang <b>Re-Generate Pattern</b> upang makuha ang pinaka-updated na state mapping na lapat sa pinakabagong platform response.\n"
        "â€¢ Mangyaring huwag gumamit ng VPN proxies upang maiwasan ang latency lag at disconnection sa pagitan ng system reader at game server.\n\n"
        "ðŸ’¬ Para sa mga karagdagang gabay, live analysis updates, at suporta, makipag-ugnayan sa aming opisyal na community portal: ðŸ‘‡\n"
        "ðŸ‘‰ https://t.me/helpslotswinbot"
    )
    msg = bot.send_message(call.message.chat.id, how_to_use_text, reply_markup=kb, parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "back_to_home")
def back_to_home(call):
    uid = call.from_user.id
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    delete_user_past_msg(call.message.chat.id, uid)
    
    teleclaw_thinking(call.message.chat.id, "Working", duration=1, call_id=call.id)
    
    # We simulate a "message" object for start_cmd
    class FakeMsg:
        def __init__(self, m):
            self.chat = m.chat
            self.from_user = m.from_user
            self.text = "/start"
            self.message_id = m.message_id
    
    start_cmd(FakeMsg(call.message))

@bot.callback_query_handler(func=lambda c: c.data == "user_login")
def handle_user_login(call):
    uid = call.from_user.id
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    delete_user_past_msg(call.message.chat.id, uid)
    
    teleclaw_thinking(call.message.chat.id, "Hacking", duration=2, call_id=call.id)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("ðŸ“Š CHECK LIVE RNG ANALYSIS", url="https://t.me/Helpslotwinbot/livernganalysis"),
        types.InlineKeyboardButton("ðŸš€ PROCEED TO SYSTEM", callback_data="user_login_proceed"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO HOME", callback_data="back_to_home")
    )
    
    caption = (
        "ðŸ“Š <b>REAL-TIME SEED ACCURACY AUDIT</b>\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "Bago simulan ang system tracking mechanics, mangyaring suriin muna ang live RNG metrics ng mga verified platforms na may mataas na win rate at optimal accuracy levels.\n\n"
        "I-click ang <b>CHECK LIVE RNG ANALYSIS</b> sa ibaba, at pagkatapos ay piliin ang <b>PROCEED TO SYSTEM</b> upang magpatuloy."
    )
    msg = bot.send_message(call.message.chat.id, caption, reply_markup=kb, parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "user_login_proceed")
def handle_user_login_proceed(call):
    uid = call.from_user.id
    user_sessions[uid]["is_logged_in"] = True
    
    teleclaw_thinking(call.message.chat.id, "Working", duration=2, call_id=call.id)
    
    # Loading animation
    msg = bot.send_message(call.message.chat.id, "â³ <b>INITIALIZING SYSTEM...</b>", parse_mode="HTML")
    time.sleep(1)
    bot.edit_message_text("â³ <b>LOADING MODULES...</b>", call.message.chat.id, msg.message_id, parse_mode="HTML")
    time.sleep(1)
    bot.delete_message(call.message.chat.id, msg.message_id)
    
    # Proceed to casino selection
    choose_casino_platform(call)

@bot.callback_query_handler(func=lambda c: c.data == "intro_proceed")
def choose_casino_platform(call):
    uid = call.from_user.id
    
    # Check if logged in
    if not user_sessions.get(uid, {}).get("is_logged_in"):
        bot.answer_callback_query(call.id, "âš ï¸ You need to log in first!", show_alert=True)
        return

    delete_user_past_msg(call.message.chat.id, uid)

    teleclaw_thinking(call.message.chat.id, "Working", duration=2, call_id=call.id)

    kb = types.InlineKeyboardMarkup()
    col1_buttons = []
    col2_buttons = []
    col3_buttons = []
    
    layouts = {"BINGOPLUS ":2,"AGILA CLUB":2,"PLAYTIME":2,"JILIBET":2,"TIKLUCK (new)":2,"GD ENEMERALD":2,"MACALLAN77":2,"INFERNO PLAY":2,"BUGATTI PLAY ":2,"MASERATI PLAY":2,"LOTUS PLAY":2,"LAMBO PLAY":2}
    
    for casino in CASINO_DATA.keys():
        layout_cols = layouts.get(casino, 1)
        btn = types.InlineKeyboardButton(f"ðŸ› {casino}", callback_data=f"set_casino_{casino}")
        if layout_cols == 3:
            col3_buttons.append(btn)
        elif layout_cols == 2:
            col2_buttons.append(btn)
        else:
            col1_buttons.append(btn)
    
    # Add 1 Column buttons
    for btn in col1_buttons:
        kb.row(btn)
    
    # Add 2 Column buttons in pairs
    for i in range(0, len(col2_buttons), 2):
        kb.row(*col2_buttons[i:i+2])
    
    # Add 3 Column buttons in triples
    for i in range(0, len(col3_buttons), 3):
        kb.row(*col3_buttons[i:i+3])
    
    kb.add(types.InlineKeyboardButton("ðŸ”™ BACK TO HOME", callback_data="back_to_home"))

    msg = bot.send_message(call.message.chat.id, "ðŸ— <b>SELECT PLATFORM DATABASE</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nChoose your Casino Platform to load the correct RNG configuration:", reply_markup=kb, parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_casino_"))
def confirm_casino_selection(call):
    uid = call.from_user.id
    selected_casino = call.data.replace("set_casino_", "")
    user_sessions[uid]["casino"] = selected_casino

    reg_link = CASINO_DATA.get(selected_casino, "https://google.com")
    delete_user_past_msg(call.message.chat.id, uid)

    teleclaw_thinking(call.message.chat.id, "Hacking", duration=3, call_id=call.id)

    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("ðŸ” LOG IN TO START", url=reg_link),
        types.InlineKeyboardButton("ðŸš€ PROCEED TO SYSTEM", callback_data="open_menu"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO CASINOS", callback_data="intro_proceed")
    )
    
    welcome_text = (
        f"ðŸ› <b>PLATFORM SELECTED: {selected_casino}</b>\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "To initialize the <b>RNG Synchronization Protocol</b>, please follow these steps:\n\n"
        "1ï¸âƒ£ Click the <b>Log in to Start</b> button below to open the secure portal.\n"
        "2ï¸âƒ£ Log in or Register your account on the official platform.\n"
        "3ï¸âƒ£ Once logged in, return to this bot and click <b>PROCEED TO SYSTEM</b>.\n\n"
        "âš ï¸ <b>SYSTEM NOTE:</b> The AI algorithm only synchronizes with active sessions detected through our encrypted link. Failure to use the link may result in inaccurate signal patterns."
    )
    msg = bot.send_message(call.message.chat.id, welcome_text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    user_sessions[uid]["last_msg"] = msg.message_id

# show_pattern moved to App.tsx

@bot.message_handler(func=lambda m: m.text == "ðŸ”„ Re-Generate Pattern")
def regenerate_btn(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    
    # Improved 5-second generation animation
    msg = bot.send_message(chat_id, "ðŸ”„ <b>INITIALIZING...</b>\n<code>[â–¯â–¯â–¯â–¯â–¯â–¯â–¯â–¯â–¯â–¯] 0%</code>", parse_mode="HTML")
    
    steps = [
        {"icon": "ðŸ“¡", "text": "Connecting to Servers..."},
        {"icon": "ðŸ§¬", "text": "Extracting RNG Seed Data..."},
        {"icon": "ðŸ›°", "text": "Matching Pattern Database..."},
        {"icon": "ðŸ§ ", "text": "Neural Network Processing..."},
        {"icon": "âœ…", "text": "Signal Generation Complete!"}
    ]

    for idx, step in enumerate(steps):
        p_bar = ["â– " if i <= int((idx/4)*9) else "â–¯" for i in range(10)]
        status_text = (
            f"<b>{step['icon']} <code>{step['text']}</code></b>\n"
            f"<code>[{''.join(p_bar)}] {int((idx/4)*100)}%</code>"
        )
        try:
            bot.edit_message_text(status_text, chat_id, msg.message_id, parse_mode="HTML")
            time.sleep(1) # Total 5 seconds for 5 steps
        except: pass
    
    bot.delete_message(chat_id, msg.message_id)
    
    run_gen_logic(chat_id, message.message_id, message.from_user, user_sessions[uid].get("casino", "UNKNOWN"), user_sessions[uid].get("game", "UNKNOWN"), user_sessions[uid].get("provider", "UNKNOWN"))

@bot.callback_query_handler(func=lambda c: c.data == "change_game")
def change_game_callback(call):
    uid = call.from_user.id
    provider = user_sessions[uid].get("provider")
    if not provider:
        bot.answer_callback_query(call.id, "âš ï¸ Provider not found!", show_alert=True)
        main_menu(call.message.chat.id, uid)
        return
    
    user_sessions[uid]["encoding"] = False
    user_sessions[uid]["encoding_id"] = None
    delete_user_past_msg(call.message.chat.id, uid)
    display_provider_games(call.message.chat.id, uid, provider)

@bot.callback_query_handler(func=lambda c: c.data == "change_platform")
def change_platform_callback(call):
    uid = call.from_user.id
    user_sessions[uid]["encoding"] = False
    user_sessions[uid]["encoding_id"] = None
    
    # Logout animation
    logout_animation(call.message.chat.id, call.message.message_id)
    time.sleep(0.5)
    
    # Clear session but keep logged in
    user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": True}
    choose_casino_platform(call)

@bot.callback_query_handler(func=lambda c: c.data == "reset_system")
def reset_system_callback(call):
    uid = call.from_user.id
    
    # Reset animation
    reset_animation(call.message.chat.id, call.message.message_id)
    time.sleep(0.5)
    
    user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": True}
    choose_casino_platform(call)

@bot.callback_query_handler(func=lambda c: c.data == "open_menu")
def trigger_menu(call):
    uid = call.from_user.id
    delete_user_past_msg(call.message.chat.id, uid)
    
    # SYSTEM CHECK ANIMATION
    msg = bot.send_message(call.message.chat.id, "âš™ï¸ <b>SYSTEM CHECK...</b>", parse_mode="HTML")
    system_startup_animation(call.message.chat.id, msg.message_id)
    bot.delete_message(call.message.chat.id, msg.message_id)
    
    main_menu(call.message.chat.id, uid)

# Old show_games removed

@bot.message_handler(func=lambda m: m.text == "ðŸ”™ BACK")
def back_to_prov(message): 
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    main_menu(message.chat.id, message.from_user.id)

# Old pick_game removed

def run_gen_logic(chat_id, message_id, user_obj, casino, game, provider):
    uid = user_obj.id if hasattr(user_obj, 'id') else user_obj
    if (time.time() - user_sessions[uid].get("last_gen_time", 0)) < 20:
        bot.send_message(chat_id, "âš ï¸ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...")
        return

    user_sessions[uid]["last_gen_time"] = time.time()
    
    # NOTIFY ADMIN OF GENERATION
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
        if admin_id_val:
            name = ""
            username = ""
            if hasattr(user_obj, 'first_name'):
                name = user_obj.first_name + (f" {user_obj.last_name}" if user_obj.last_name else "")
                username = f" (@{user_obj.username})" if user_obj.username else ""
            bot.send_message(admin_id_val, f"ðŸ“Š <b>SIGNAL GENERATED</b>\nUser: {name}{username} (<code>{uid}</code>)\nðŸ› <b>Casino:</b> {casino}\nðŸŽ® <b>Provider:</b> {provider}\nðŸŽ° <b>Game:</b> {game}", parse_mode="HTML")
    except: pass

    steps = [
        {"icon": "ðŸ“¡", "text": "Connecting to Servers..."},
        {"icon": "ðŸ§¬", "text": "Extracting RNG Seed Data..."},
        {"icon": "ðŸ›°", "text": "Matching Pattern Database..."},
        {"icon": "ðŸ§ ", "text": "Neural Network Processing..."},
        {"icon": "âœ…", "text": "Signal Generation Complete!"}
    ]

    for idx, step in enumerate(steps):
        p_bar = ["â– " if i <= int((idx/4)*9) else "â–¯" for i in range(10)]
        status_text = (
            f"<b>{step['icon']} <code>{step['text']}</code></b>\n"
            f"<code>[{''.join(p_bar)}] {int((idx/4)*100)}%</code>"
        )
        try:
            bot.edit_message_text(status_text, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.7)
        except: pass

    try: bot.delete_message(chat_id, message_id)
    except: pass

    # Delete last generated messages
    if user_sessions[uid].get("last_msg"):
        try: bot.delete_message(chat_id, user_sessions[uid]["last_msg"])
        except: pass
    if user_sessions[uid].get("last_kb_msg"):
        try: bot.delete_message(chat_id, user_sessions[uid]["last_kb_msg"])
        except: pass

    ph_now = datetime.utcnow() + timedelta(hours=8)
    v_until = (ph_now + timedelta(minutes=random.randint(30, 45))).strftime("%I:%M %p")

    fake_id = str(uuid.uuid4())[:8].upper()

    if "PG" in provider.upper():
        valid_signals = [s for s in SIGNALS if "Turbo" not in s]
    else:
        valid_signals = SIGNALS
    
    if not valid_signals:
        valid_signals = SIGNALS
    
    result_text = (
        f"ðŸ“¡ <b>SIGNAL DETECTED</b> <code>#{fake_id}</code>\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"ðŸŽ¯ <b>Target:</b> {game}\n"
        f"ðŸŽ° <b>Provider:</b> {provider}\n"
        f"ðŸ“Š <b>Probability:</b> {random.uniform(96, 99):.2f}%\n"
        f"âš¡ <b>Volatility:</b> <tg-spoiler>HIGH</tg-spoiler>\n"
        f"ðŸ” <b>Server Hash:</b> <code>{str(uuid.uuid4())[:16]}...</code>\n"
        f"â° <b>Valid Until:</b> {v_until}\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"ðŸ’¡ <i>Click the button below to reveal the injection pattern.</i>"
    )

    user_sessions[uid]["result_text"] = result_text
    user_sessions[uid]["pattern"] = random.choice(valid_signals)
    user_sessions[uid]["encoding"] = True 
    session_id = str(uuid.uuid4())
    user_sessions[uid]["encoding_id"] = session_id
    
    # Inline buttons for everything
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(
        types.InlineKeyboardButton("ðŸ‘ï¸ SHOW PATTERN", callback_data="show_pattern"),
        types.InlineKeyboardButton("ðŸ”„ Re-Generate Pattern", callback_data="run_gen"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO GAMES", callback_data="change_game"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO PROVIDERS", callback_data="open_menu"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO CASINOS", callback_data="change_platform")
    )
    
    # Remove any lingering ReplyKeyboardMarkup
    remove_kb = types.ReplyKeyboardRemove()
    
    # Send message with all inline buttons and remove old keyboard
    msg = bot.send_message(chat_id, result_text, reply_markup=inline_kb, parse_mode="HTML")
    
    # Send a hidden message to remove the keyboard, then delete it
    del_msg = bot.send_message(chat_id, "âš™ï¸ Updating controls...", reply_markup=remove_kb)
    try: bot.delete_message(chat_id, del_msg.message_id)
    except: pass
    
    user_sessions[uid]["last_msg"] = msg.message_id
    user_sessions[uid]["last_kb_msg"] = None # No separate keyboard message

    # Start the live encoding animation thread
    t = threading.Thread(target=live_encoding_animation, args=(chat_id, msg.message_id, uid, casino, session_id))
    t.daemon = True
    t.start()

@bot.callback_query_handler(func=lambda c: c.data == "run_gen")
def run_gen(call):
    uid = call.from_user.id
    
    # Check if we are regenerating from an existing message
    if call.message.text and "SIGNAL DETECTED" in call.message.text:
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        msg = bot.send_message(call.message.chat.id, "Generating Pattern ðŸ”ƒ. please wait...")
        message_id = msg.message_id
    else:
        try:
            msg = bot.edit_message_text("Generating Pattern ðŸ”ƒ. please wait...", call.message.chat.id, call.message.message_id)
            message_id = msg.message_id
        except:
            msg = bot.send_message(call.message.chat.id, "Generating Pattern ðŸ”ƒ. please wait...")
            message_id = msg.message_id
        
    run_gen_logic(
        call.message.chat.id, 
        message_id, 
        call.from_user, 
        user_sessions[uid].get("casino", "UNKNOWN"), 
        user_sessions[uid].get("game", "UNKNOWN"), 
        user_sessions[uid].get("provider", "UNKNOWN")
    )

# ================= TOP GAMES COMMAND =================
top_games_cache = {}
TOP_GAMES_CACHE_DURATION = 6 * 3600 # 6 hours

def get_or_generate_top_games(matched_casino):
    current_time = time.time()
    
    # Check cache
    if matched_casino in top_games_cache:
        cache_data = top_games_cache[matched_casino]
        if current_time - cache_data["timestamp"] < TOP_GAMES_CACHE_DURATION:
            return cache_data["games"]
            
    # Generate new top games
    preferred_providers = ["PRAGMATIC", "JILI", "PG SOFT", "PG", "PGSOFT"]
    
    pragmatic_games = []
    jili_games = []
    pg_games = []
    other_games = []
    
    casino_providers = PROVIDERS_DATA.get(matched_casino, {})
    for provider, games in casino_providers.items():
        prov_upper = provider.upper()
        for g in games:
            game_name = g.get("n", str(g)) if isinstance(g, dict) else str(g)
            game_data = {"name": game_name, "provider": provider}
            
            if "PRAGMATIC" in prov_upper:
                pragmatic_games.append(game_data)
            elif "JILI" in prov_upper:
                jili_games.append(game_data)
            elif "PG" in prov_upper or "PGSOFT" in prov_upper:
                pg_games.append(game_data)
            else:
                other_games.append(game_data)
                
    all_games = pragmatic_games + jili_games + pg_games + other_games
    if not all_games:
        return []
        
    num_games = min(10, len(all_games))
    selected_games = []
    
    # We want a mix. Let's try to get up to 2 from pragmatic, 2 from jili, 2 from pg, rest from others
    def pick_games(pool, count):
        if not pool: return []
        k = min(count, len(pool))
        picked = random.sample(pool, k)
        for p in picked: pool.remove(p)
        return picked

    selected_games.extend(pick_games(pragmatic_games, 2))
    selected_games.extend(pick_games(jili_games, 2))
    selected_games.extend(pick_games(pg_games, 2))
    
    # Fill remaining from anywhere
    remaining_pool = pragmatic_games + jili_games + pg_games + other_games
    needed = num_games - len(selected_games)
    if needed > 0 and remaining_pool:
        selected_games.extend(pick_games(remaining_pool, needed))
        
    random.shuffle(selected_games)
    
    games_with_rtp = []
    for g in selected_games:
        rtp = random.uniform(92.0, 99.9)
        games_with_rtp.append({
            "name": g["name"],
            "provider": g["provider"],
            "rtp": round(rtp, 1)
        })
        
    top_games_cache[matched_casino] = {
        "timestamp": current_time,
        "games": games_with_rtp
    }
    return games_with_rtp

@bot.message_handler(commands=["winrate"])
def winrate_cmd(message):
    try:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("ðŸ“Š CHECK LIVE RNG ANALYSIS", url="https://t.me/Helpslotwinbot/livernganalysis")
        )
        caption = (
            "ðŸ“Š <b>REAL-TIME SEED ACCURACY AUDIT</b>\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "I-click ang button sa ibaba upang masuri ang live RNG metrics at win rate analysis:"
        )
        bot.send_message(message.chat.id, caption, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        print(f"Error in winrate_cmd: {e}")

@bot.message_handler(commands=["howtouse"])
def howtouse_cmd(message):
    try:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("â“ How to use the system?", callback_data="how_to_use")
        )
        caption = (
            "â“ <b>SYSTEM OPERATION GUIDE</b>\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "I-click ang button sa ibaba upang mabasa ang kumpletong gabay sa paggamit ng system:"
        )
        bot.send_message(message.chat.id, caption, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        print(f"Error in howtouse_cmd: {e}")

@bot.message_handler(commands=["topgames"])
def send_topgames_casinos_menu(message):
    try:
        kb = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for casino in CASINO_DATA.keys():
            buttons.append(types.InlineKeyboardButton(text=f"ðŸŽ° {casino}", callback_data=f"tgcas:{casino}"))
        kb.add(*buttons)
        bot.send_message(message.chat.id, "ðŸ”¥ <b>TOP 10 GAMES MENU</b> ðŸ”¥\n\nPumili ng Casino platform upang makita ang Top 10 recommended winning games:", parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        print(f"Error in topgames menu: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tgcas:"))
def handle_topgames_casino_select(call):
    try:
        matched_casino = call.data.split("tgcas:")[1]
        cached_games = get_or_generate_top_games(matched_casino)
        if not cached_games:
            bot.answer_callback_query(call.id, "âŒ No games available.", show_alert=True)
            return
            
        reply_text = f"ðŸ”¥ <b>TOP 10 GAMES FOR {matched_casino}</b> ðŸ”¥\n\n"
        for i, game in enumerate(cached_games, 1):
            reply_text += f"{i}.) <b>{game['name']}</b>\n<blockquote>ðŸ“ˆ {game['rtp']}% RTP</blockquote>\n<i>{game['provider']}</i>\n\n"
        reply_text += f"â³ <i>Valid for next 6 hours.</i>"
        
        bot.send_message(call.message.chat.id, reply_text, parse_mode="HTML")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Error in topgames callback: {e}")

@bot.message_handler(regexp=r"^/topgames_(.+)$")
def handle_topgames(message):
    try:
        command = message.text.split()[0]
        casino_key = command.replace("/topgames_", "").upper()
        
        matched_casino = None
        for c in CASINO_DATA.keys():
            if c.replace(" ", "").upper() == casino_key or c.replace(" ", "_").upper() == casino_key:
                matched_casino = c
                break
                
        if not matched_casino:
            bot.send_message(message.chat.id, f"âŒ <b>Casino not found.</b>", parse_mode="HTML")
            return
            
        cached_games = get_or_generate_top_games(matched_casino)
        if not cached_games:
            bot.send_message(message.chat.id, f"âŒ <b>No games available.</b>", parse_mode="HTML")
            return
            
        reply_text = f"ðŸ”¥ <b>TOP 10 GAMES FOR {matched_casino}</b> ðŸ”¥\n\n"
        for i, game in enumerate(cached_games, 1):
            reply_text += f"{i}.) <b>{game['name']}</b>\n<blockquote>ðŸ“ˆ {game['rtp']}% RTP</blockquote>\n<i>{game['provider']}</i>\n\n"
        reply_text += f"â³ <i>Valid for next 6 hours.</i>"
        bot.send_message(message.chat.id, reply_text, parse_mode="HTML")
        
    except Exception as e:
        print(f"Error in topgames: {e}")

@bot.message_handler(commands=["help"])
def help_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0

    help_text = "ðŸ“– <b>AVAILABLE COMMANDS</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
    help_text += "ðŸš€ /start - Open Signal Dashboard\n"
    help_text += "ðŸŽ® /topgames - Select Casino & View Top 10 Games\n"
    help_text += "ðŸ“Š /winrate - Check Live RNG Analysis\n"
    help_text += "â“ /howtouse - System operations guide"
        
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

    if message.from_user.id == admin_id_val:
        admin_text = "ðŸ›  <b>ADMIN PANEL HELP</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        admin_text += "ðŸ“Š /stats - Show user statistics\n"
        admin_text += "ðŸ“¢ /broadcast - Broadcast msg to all users\n"
        admin_text += "ðŸ“‚ /backup_users - Export user database\n"
        admin_text += "ðŸ“¥ /restore_users - (Reply to file) Restore database\n"
        admin_text += "ðŸŽ® /top5 & /top10 - Game recommendations"
        bot.send_message(message.chat.id, admin_text, parse_mode="HTML")



# ================= OVERRIDDEN LOGIC FOR MULTI-CASINO PROVIDERS =================
def display_provider_games(chat_id, uid, provider_name):
    user_sessions[uid]["provider"] = provider_name
    selected_casino = user_sessions[uid].get("casino")
    games_list = PROVIDERS_DATA.get(selected_casino, {}).get(provider_name, [])
    # games_list is now a list of dicts like {"n": "Game", "bb": 1}
    display_names = [g["n"] for g in games_list]

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("ðŸ”™ BACK TO PROVIDERS"))
    kb.add(*[types.KeyboardButton(n) for n in display_names])

    msg = bot.send_message(chat_id, f"ðŸŽ° <b>{provider_name}</b>\nShowing {len(display_names)} Games Available:", reply_markup=kb, parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id

def back_to_providers_reply(message):
    uid = message.from_user.id
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    delete_user_past_msg(message.chat.id, uid)
    main_menu(message.chat.id, uid)

def main_menu(chat_id, uid):
    delete_user_past_msg(chat_id, uid)
    
    selected_casino = user_sessions[uid].get("casino")
    providers_list = list(PROVIDERS_DATA.get(selected_casino, {}).keys())
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("ðŸ”™ BACK TO CASINOS"))
    kb.add(*[types.KeyboardButton(p) for p in providers_list])
    msg = bot.send_message(chat_id, "âš™ï¸ <b>MAIN CONTROL PANEL:</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nSelect your preferred Slot Provider to begin analysis:", reply_markup=kb, parse_mode="HTML")
    if uid not in user_sessions:
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": selected_casino}
    user_sessions[uid]["last_msg"] = msg.message_id
    user_sessions[uid]["encoding"] = False

def back_to_casinos_handler(message):
    uid = message.from_user.id
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    delete_user_past_msg(message.chat.id, uid)
    # Reset casino and go back
    user_sessions[uid]["casino"] = None
    
    # We simulate a "call" object for choose_casino_platform
    class FakeCall:
        def __init__(self, m):
            self.message = m
            self.from_user = m.from_user
    
    choose_casino_platform(FakeCall(message))

def run_gen_logic(chat_id, message_id, user_obj, casino, game_name, provider):
    uid = user_obj.id
    if (time.time() - user_sessions[uid].get("last_gen_time", 0)) < 20:
        bot.send_message(chat_id, "âš ï¸ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...")
        return

    user_sessions[uid]["last_gen_time"] = time.time()
    
    # Wait and animate the "Generating Pattern..." message
    base_text = "Generating Pattern ðŸ”ƒ. please wait"
    for i in range(5):
        dots = "." * ((i % 3) + 1)
        try:
            bot.edit_message_text(f"{base_text}{dots}", chat_id, message_id)
        except:
            pass
        time.sleep(1)

    # Notify Admin
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
        if admin_id_val:
            name = user_obj.first_name + (f" {user_obj.last_name}" if user_obj.last_name else "")
            username = f" (@{user_obj.username})" if user_obj.username else ""
            bot.send_message(admin_id_val, f"ðŸ“Š <b>SIGNAL GENERATED</b>\nUser: {name}{username} (<code>{uid}</code>)\nðŸ› <b>Casino:</b> {casino}\nðŸŽ® <b>Provider:</b> {provider}\nðŸŽ° <b>Game:</b> {game_name}", parse_mode="HTML")
    except: pass

    # Delete the generating message before showing result
    try: bot.delete_message(chat_id, message_id)
    except: pass

    # Find if game has Buy Bonus
    has_bb = False
    provider_games = PROVIDERS_DATA.get(casino, {}).get(provider, [])
    for g in provider_games:
        if g["n"] == game_name:
            has_bb = (g.get("bb", 0) == 1)
            break

    # Filtering signals
    if has_bb:
        # Include Buy Bonus signals
        valid_signals = SIGNALS
    else:
        # Exclude Buy Bonus signals
        valid_signals = [s for s in SIGNALS if "Buy Bonus" not in s]
    
    if "PG" in provider.upper():
        valid_signals = [s for s in valid_signals if "Turbo" not in s]
    
    if not valid_signals: valid_signals = SIGNALS

    # Logic to ensure patterns don't repeat until all are used
    if "used_signals" not in user_sessions[uid]:
        user_sessions[uid]["used_signals"] = []
    
    # We use valid_signals (filtered) as our base
    available = [s for s in valid_signals if s not in user_sessions[uid]["used_signals"]]
    
    # If no available signals in the filtered list haven't been used, reset the tracker for this filter
    if not available:
        # We only clear the ones that match CURRENT filtering to avoid clearing everything if they switch games
        # But to keep it simple and robust as requested (exhaust all then repeat):
        user_sessions[uid]["used_signals"] = [s for s in user_sessions[uid]["used_signals"] if s not in valid_signals]
        available = valid_signals
    
    selected_pattern = random.choice(available)
    user_sessions[uid]["used_signals"].append(selected_pattern)

    # Result data
    ph_now = datetime.utcnow() + timedelta(hours=8)
    v_until = (ph_now + timedelta(minutes=random.randint(30, 45))).strftime("%I:%M %p")
    fake_id = str(uuid.uuid4())[:8].upper()

    user_sessions[uid]["result_text"] = f"ðŸ“¡ <b>SIGNAL DETECTED</b> <code>#{fake_id}</code>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸŽ¯ <b>Target:</b> <i><b>{game_name}</b></i>\nðŸŽ° <b>Provider:</b> <i>{provider}</i>\nðŸ“Š <b>Probability:</b> <i>{random.uniform(96, 99):.2f}%</i>\nâš¡ <b>Volatility:</b> <i>HIGH</i>\nâ° <b>Valid Until:</b> <i>{v_until}</i>"
    user_sessions[uid]["status_text"] = f"ðŸŸ¢ <b>STATUS:</b> <code>LIVE SYNC ACTIVE</code>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ <i>Login to casino first before following pattern.</i>"
    user_sessions[uid]["pattern"] = selected_pattern
    user_sessions[uid]["encoding"] = True 
    session_id = str(uuid.uuid4())
    user_sessions[uid]["encoding_id"] = session_id

    # Initially send without buttons and status to allow animation to reveal them later
    msg = bot.send_message(chat_id, user_sessions[uid]["result_text"], parse_mode="HTML")
    threading.Thread(target=live_encoding_animation, args=(chat_id, msg.message_id, uid, casino, session_id)).start()

def pick_game(message):
    uid = message.from_user.id
    game_name = message.text.strip()
    
    # Ensure session exists
    if uid not in user_sessions:
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None}

    # Try to find the casino and provider for this game if not set correctly
    current_casino = user_sessions[uid].get("casino")
    current_prov = user_sessions[uid].get("provider")
    
    found = False
    # Check if game exists in current casino first
    if current_casino in PROVIDERS_DATA:
        for p_name, games in PROVIDERS_DATA[current_casino].items():
            if any(g["n"].strip().upper() == game_name.upper() for g in games):
                user_sessions[uid]["provider"] = p_name
                # Ensure we use the exact name from data
                actual_game = next(g["n"] for g in games if g["n"].strip().upper() == game_name.upper())
                game_name = actual_game
                found = True
                break
    
    # If not found in current casino, search all casinos
    if not found:
        for c_name, c_data in PROVIDERS_DATA.items():
            for p_name, games in c_data.items():
                if any(g["n"].strip().upper() == game_name.upper() for g in games):
                    user_sessions[uid]["casino"] = c_name
                    user_sessions[uid]["provider"] = p_name
                    actual_game = next(g["n"] for g in games if g["n"].strip().upper() == game_name.upper())
                    game_name = actual_game
                    found = True
                    break
            if found: break

    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    delete_user_past_msg(message.chat.id, uid)
    user_sessions[uid]["game"] = game_name
    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("ðŸš€ ANALYZE RNG SEED", callback_data="run_gen"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO GAMES", callback_data="change_game"),
        types.InlineKeyboardButton("ðŸ”™ BACK TO PROVIDERS", callback_data="open_menu")
    )
    msg = bot.send_message(message.chat.id, f"ðŸŽ¯ <b>SELECTED:</b> <b>{game_name}</b>\nClick below to start RNG sync.", reply_markup=kb, parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id

def show_games(message):
    uid = message.from_user.id
    provider_name = message.text.strip()
    
    # Ensure session exists
    if uid not in user_sessions:
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None}

    # Find the casino for this provider if not set
    current_casino = user_sessions[uid].get("casino")
    
    # Case-insensitive check for provider
    found_prov = False
    if current_casino in PROVIDERS_DATA:
        for p_name in PROVIDERS_DATA[current_casino].keys():
            if p_name.strip().upper() == provider_name.upper():
                provider_name = p_name
                found_prov = True
                break
    
    if not found_prov:
        for c_name, c_data in PROVIDERS_DATA.items():
            for p_name in c_data.keys():
                if p_name.strip().upper() == provider_name.upper():
                    user_sessions[uid]["casino"] = c_name
                    provider_name = p_name
                    found_prov = True
                    break
            if found_prov: break

    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    delete_user_past_msg(message.chat.id, uid)
    display_provider_games(message.chat.id, uid, provider_name)

def live_encoding_animation(chat_id, message_id, uid, selected_casino, session_id):
    # Initial Delay with Message
    try:
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        bot.edit_message_text(
            f"{res_text}\n\nâš ï¸ <b>INITIATING INJECTION PROTOCOL...</b>", 
            chat_id, message_id, parse_mode="HTML"
        )
    except: pass
    time.sleep(1.5)

    frames = [
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â–¡â–¡â–¡â–¡â–¡â–¡â–¡â–¡â–¡] 10%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â–¡â–¡â–¡â–¡â–¡â–¡â–¡] 30%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â–¡â–¡â–¡â–¡â–¡] 50%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â– â– â–¡â–¡â–¡] 70%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â– â– â– â– â–¡] 90%</code>",
        f"â³ <b>SYNCING DATA TO {selected_casino}</b>\n<code>[â– â– â– â– â– â– â– â– â– â– ] 100%</code>"
    ]
    
    for frame in frames:
        if uid not in user_sessions or user_sessions[uid].get("encoding") == False or user_sessions[uid].get("encoding_id") != session_id:
            break
        try:
            res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n{frame}",
                parse_mode="HTML"
            )
        except Exception as e:
            break 
        time.sleep(1.0)

    # FINAL STEP: Show Status and Buttons after animation
    if uid in user_sessions and user_sessions[uid].get("encoding_id") == session_id:
        user_sessions[uid]["encoding"] = False
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        status_footer = user_sessions[uid].get("status_text", "")
        
        inline_kb = types.InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            types.InlineKeyboardButton("ðŸ‘ï¸ REVEAL INJECTION PATTERN", callback_data="show_pattern"), 
            types.InlineKeyboardButton("ðŸ”„ Re-Sync RNG Data", callback_data="run_gen"), 
            types.InlineKeyboardButton("ðŸ”™ BACK TO GAMES", callback_data="change_game"),
            types.InlineKeyboardButton("ðŸ”™ BACK TO PROVIDERS", callback_data="open_menu"),
            types.InlineKeyboardButton("ðŸ”™ BACK TO CASINOS", callback_data="change_platform")
        )
        
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n{status_footer}",
                parse_mode="HTML",
                reply_markup=inline_kb
            )
        except: pass

@bot.callback_query_handler(func=lambda c: c.data == "show_pattern")
def show_pattern_callback(call):
    uid = call.from_user.id
    if uid not in user_sessions:
        bot.answer_callback_query(call.id, "âŒ Session expired. Please /start again.", show_alert=True)
        return
    game = user_sessions[uid].get("game", "UNKNOWN")
    pattern = user_sessions[uid].get("pattern", "No pattern available.")
    # Requested alert format: Game: (Game Name) | Pattern: (Pattern)
    bot.answer_callback_query(call.id, f"Game: {game}\nPattern: {pattern}", show_alert=True)

# Centralized message handler to avoid conflicts and ensure new games/providers are caught
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def handle_text_messages(message):
    uid = message.from_user.id
    text = message.text.strip()
    
    # Handlers for specific navigation buttons
    if text == "ðŸ”™ BACK TO PROVIDERS":
        return back_to_providers_reply(message)
    if text == "ðŸ”™ BACK TO CASINOS":
        return back_to_casinos_handler(message)
    if text == "ðŸ”™ BACK":
        # Check if we should go to providers or casinos based on where we are
        if uid in user_sessions and user_sessions[uid].get("provider"):
            return back_to_prov(message)
        return back_to_casinos_handler(message)
    if text == "ðŸ”„ Re-Generate Pattern" or text == "ðŸ”„ Re-Sync RNG Data":
        return regenerate_btn(message)

    # Check if text is a Provider Name
    is_provider = False
    for cas_data in PROVIDERS_DATA.values():
        if any(p_name.strip().upper() == text.upper() for p_name in cas_data.keys()):
            is_provider = True
            break
    if is_provider:
        return show_games(message)
        
    # Check if text is a Game Name
    is_game = False
    for cas_data in PROVIDERS_DATA.values():
        for provider_games in cas_data.values():
            if any(g.get("n").strip().upper() == text.upper() for g in provider_games):
                is_game = True
                break
        if is_game: break
    if is_game:
        return pick_game(message)

@bot.message_handler(commands=["top5", "top10"])
def top_games_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0
    
    if message.from_user.id != admin_id_val:
        return

    import random
    from datetime import datetime, timedelta
    num = 5 if message.text.startswith("/top5") else 10
    # Adjust to Philippine Time (UTC+8)
    now_pht = datetime.utcnow() + timedelta(hours=8)
    now_str = now_pht.strftime("%B %d, %Y âœ¨")
    
    header = f"<b>RECOMMENDED FOR TODAY!</b>\n({now_str})\n\n<b>PLATFORM with Exact SEED:</b>\n"
    
    casinos = list(PROVIDERS_DATA.keys())
    # Limit number of casinos to avoid long messages and satisfy user request
    # For /top10, pick 4. For /top5, pick 5.
    limit = 4 if num == 10 else 5
    display_casinos = random.sample(casinos, min(limit, len(casinos)))

    icons = ["ðŸ”¥", "ðŸ’¯", "ðŸ’°", "ðŸ‘‘", "ðŸ’Ž", "âš¡", "âœ¨", "ðŸŒŸ", "ðŸ”¥"]
    
    platform_list = "<blockquote>"
    for i, cas in enumerate(display_casinos):
        icon = icons[i % len(icons)]
        # Bold Sans Serif for "Heavy Bold"
        styled_cas = "".join([chr(ord(c) + 120211) if 'A' <= (c := c_raw.upper()) <= 'Z' else c for c_raw in cas])
        platform_list += f"{icon} <b>{styled_cas}</b>\n"
    platform_list += "</blockquote>"
    
    platform_list += "____\n\n"
    
    body = ""
    for i, cas in enumerate(display_casinos):
        icon = icons[i % len(icons)]
        # Bold Sans Serif for "Heavy Bold"
        styled_cas = "".join([chr(ord(c) + 120211) if 'A' <= (c := c_raw.upper()) <= 'Z' else c for c_raw in cas])
        
        # Collect all games for this casino by using the cache/generator
        cached_games = get_or_generate_top_games(cas)
        
        if not cached_games: continue
        
        sample_size = min(num, len(cached_games))
        selected = cached_games[:sample_size]
        
        body += f"{icon} <b>{styled_cas}</b>\n"
        body += f"ðŸŽ® Top {sample_size} Winning Games:\n"
        
        for idx, g_info in enumerate(selected):
            body += f"<blockquote>{idx+1}. <i><b>{g_info['name']}</b></i> â€” <i>{g_info['rtp']}% RTP</i>\n(<i>{g_info['provider']}</i>)</blockquote>\n"
        
        body += "______\n\n"
        
    footer = "Luxury isnâ€™t slowâ€¦ it strikes.\nDon't forget to use <b>SYSTEM JACKPOT READER</b> ðŸ’¯\nClick /start or Send it here to initialize system âœ…\n\n#TopWinningGames #HighStakes\n\n<i>Play Responsibly âœ…</i>"
    
    final_msg = header + platform_list + body + footer
    
    # Send message, handling potential length issues
    if len(final_msg) > 4096:
        for i in range(0, len(final_msg), 4096):
            try: bot.send_message(message.chat.id, final_msg[i:i+4096], parse_mode="HTML")
            except: pass
    else:
        try: bot.send_message(message.chat.id, final_msg, parse_mode="HTML")
        except: pass

@bot.message_handler(commands=["backup_users", "back_users"])
def backup_users_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    # If using Turso, we sync to the file first
    if "db_manager" in globals():
        try:
            current_users = db_manager.get_all_users()
            with open(USER_IDS_FILE, "w") as f:
                for uid in current_users:
                    f.write(f"{uid}\n")
        except: pass

    if os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, "rb") as f:
            bot.send_document(admin_id_val, f, caption=f"ðŸ“‚ <b>User Database Backup</b>\nTotal: {len(user_ids)}", parse_mode="HTML")
    else:
        bot.send_message(admin_id_val, "âŒ <b>Backup failed:</b> <code>users.txt</code> not found.")

@bot.message_handler(commands=["restore_users"])
def restore_users_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.send_message(admin_id_val, "âŒ <b>Usage:</b> Reply to a <code>users.txt</code> file with <code>/restore_users</code>")
        return
    
    file_info = bot.get_file(message.reply_to_message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open(USER_IDS_FILE, "wb") as f:
        f.write(downloaded_file)
    
    # If using Turso, sync the restored file to the database
    if "db_manager" in globals():
        try:
            ids_to_add = []
            with open(USER_IDS_FILE, "r") as f:
                for line in f:
                    u_id = line.strip()
                    if u_id and u_id.isdigit():
                        ids_to_add.append(int(u_id))
            if ids_to_add:
                db_manager.add_users_batch(ids_to_add)
        except: pass

    load_users() # Refresh global user_ids set
    bot.send_message(admin_id_val, f"âœ… <b>Database restored!</b> Total users: {len(user_ids)}")


def start_bot():
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            print("ðŸš€ BOT POLLING STARTED...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Bot Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # In direct execution, start bot in background and run Flask in main thread
    t = Thread(target=start_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get('PORT', 10000))
    print(f"ðŸ“¡ SERVER STARTING ON PORT {port}...")
    app.run(host='0.0.0.0', port=port)
else:
    # If imported (e.g. by gunicorn), start bot in background
    t = Thread(target=start_bot)
    t.daemon = True
    t.start()