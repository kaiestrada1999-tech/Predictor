# -*- coding: utf-8 -*-
import telebot
import random
import time
import os
import threading
import uuid
import html
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
    "AGILA CLUB": "https://efj8j.agclub1.com/register.html",
    "HAHA777": "https://5bset.6014102.com/register.html",
    "TIKLUCK": "https://pkj11.bugattiplay.net/register.html",
    "JILIBET": "https://4pgja.fortuneplaygaming.pro/register.html",
    "BUGATTI PLAY": "https://m3kzq.quantumbbc.fun/register.html"
}

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)

# ================= SECURITY CONFIG & OVERRIDES =================
PROTECT_CONTENT = False
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

def _safe_chunk_text(text, max_len=3000):
    if not text:
        return [""]
    try:
        utf16_len = len(text.encode('utf-16-le')) // 2
    except:
        utf16_len = len(text)
    if utf16_len <= max_len:
        return [text]

    chunks = []
    lines = text.splitlines()
    current_chunk = ""

    for line in lines:
        test_chunk = (current_chunk + chr(10) + line) if current_chunk else line
        try:
            chunk_len = len(test_chunk.encode('utf-16-le')) // 2
        except:
            chunk_len = len(test_chunk)

        if chunk_len <= max_len:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            try:
                line_len = len(line.encode('utf-16-le')) // 2
            except:
                line_len = len(line)

            if line_len > max_len:
                words = line.split(" ")
                for word in words:
                    test_sub = current_chunk + (" " if current_chunk else "") + word
                    try:
                        sub_len = len(test_sub.encode('utf-16-le')) // 2
                    except:
                        sub_len = len(test_sub)
                    if sub_len <= max_len:
                        current_chunk = test_sub
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = word
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)
    return chunks if chunks else [text]

_orig_send_message = bot.send_message
def _secure_send_message(chat_id, text, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)

    text_str = str(text) if text is not None else ""
    try:
        utf16_len = len(text_str.encode('utf-16-le')) // 2
    except:
        utf16_len = len(text_str)

    if utf16_len <= 3800:
        try:
            return _orig_send_message(chat_id, text, **kwargs)
        except Exception as e:
            if "MESSAGE_TOO_LONG" not in str(e):
                raise

    # Split into safe chunks if too long or if MESSAGE_TOO_LONG occurred
    chunks = _safe_chunk_text(text_str, max_len=3000)
    last_msg = None
    for idx, chunk in enumerate(chunks):
        chunk_kwargs = dict(kwargs)
        if idx < len(chunks) - 1 and 'reply_markup' in chunk_kwargs:
            del chunk_kwargs['reply_markup']
        try:
            last_msg = _orig_send_message(chat_id, chunk, **chunk_kwargs)
        except Exception as err:
            if 'parse_mode' in chunk_kwargs:
                chunk_kwargs.pop('parse_mode', None)
                try:
                    last_msg = _orig_send_message(chat_id, chunk, **chunk_kwargs)
                except:
                    pass
            else:
                raise err
    return last_msg
bot.send_message = _secure_send_message

_orig_send_photo = bot.send_photo
def _secure_send_photo(chat_id, photo, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    if 'caption' in kwargs and kwargs['caption']:
        cap = str(kwargs['caption'])
        try:
            cap_len = len(cap.encode('utf-16-le')) // 2
        except:
            cap_len = len(cap)
        if cap_len > 1024:
            kwargs['caption'] = cap[:1020] + "..."
    # Auto-open binary file if string path to existing local file (e.g. 'banner.jpg') is provided
    if isinstance(photo, str) and not photo.startswith(('http://', 'https://')):
        if os.path.exists(photo):
            with open(photo, 'rb') as pf:
                return _orig_send_photo(chat_id, pf, **kwargs)
    return _orig_send_photo(chat_id, photo, **kwargs)
bot.send_photo = _secure_send_photo

def send_menu_bubble(chat_id, text, reply_markup=None, photo=None, parse_mode="HTML"):
    """
    Sends message + buttons in a SINGLE container/bubble.
    If photo is provided (used exclusively on /start), sends send_photo with caption and reply_markup in 1 call.
    Otherwise (all other menus), sends send_message with text and reply_markup in 1 call (NO PHOTO).
    """
    target_photo = photo if (photo is not None and str(photo).strip() != "") else None
    caption_text = str(text) if text is not None else ""
    if target_photo:
        # Telegram Bot API media caption limit is 1024 characters
        clean_caption = caption_text if len(caption_text) <= 1024 else caption_text[:1020] + "..."
        try:
            if isinstance(target_photo, str) and not target_photo.startswith(('http://', 'https://')):
                if os.path.exists(target_photo):
                    with open(target_photo, 'rb') as pf:
                        return bot.send_photo(
                            chat_id=chat_id,
                            photo=pf,
                            caption=clean_caption,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode
                        )
            return bot.send_photo(
                chat_id=chat_id,
                photo=target_photo,
                caption=clean_caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            print(f"send_photo fallback to single send_message bubble: {e}")
            return bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    return bot.send_message(
        chat_id=chat_id,
        text=caption_text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )

_orig_send_document = bot.send_document
def _secure_send_document(chat_id, document, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    if 'caption' in kwargs and kwargs['caption']:
        cap = str(kwargs['caption'])
        try:
            cap_len = len(cap.encode('utf-16-le')) // 2
        except:
            cap_len = len(cap)
        if cap_len > 1000:
            kwargs['caption'] = cap[:990] + "..."
    return _orig_send_document(chat_id, document, **kwargs)
bot.send_document = _secure_send_document

_orig_edit_message_text = bot.edit_message_text
def _secure_edit_message_text(text, chat_id=None, message_id=None, inline_message_id=None, **kwargs):
    text_str = str(text) if text is not None else ""
    try:
        utf16_len = len(text_str.encode('utf-16-le')) // 2
    except:
        utf16_len = len(text_str)
    if utf16_len > 3800:
        text_str = text_str[:3750] + "..."
    return _orig_edit_message_text(text_str, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id, **kwargs)
bot.edit_message_text = _secure_edit_message_text

_orig_copy_message = bot.copy_message
def _secure_copy_message(chat_id, from_chat_id, message_id, **kwargs):
    if 'protect_content' not in kwargs:
        kwargs['protect_content'] = PROTECT_CONTENT and not is_admin(chat_id)
    return _orig_copy_message(chat_id, from_chat_id, message_id, **kwargs)
bot.copy_message = _secure_copy_message

def render_meter(percent, length=10):
    try:
        filled = int(round((float(percent) / 100.0) * length))
    except:
        filled = 9
    filled = max(0, min(length, filled))
    return "■" * filled + "□" * (length - filled)

def format_cyber_box(game, casino, provider, prob, fake_id, v_until):
    safe_game = html.escape(str(game))
    safe_casino = html.escape(str(casino))
    safe_prov = html.escape(str(provider))
    meter = render_meter(prob, 10)
    
    text = (
        f"⚜️ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> <code>#{fake_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<pre>"
        f"┌─ PLATFORM TELEMETRY ──────────┐\n"
        f"│ TARGET   : {safe_game[:16]:<16} │\n"
        f"│ CASINO   : {safe_casino[:16]:<16} │\n"
        f"│ PROVIDER : {safe_prov[:16]:<16} │\n"
        f"│ ACCURACY : {prob:.2f}%           │\n"
        f"│ METER    : [{meter}]     │\n"
        f"│ VOLATILE : HIGH [SURGE PEAK]  │\n"
        f"│ VALID TO : {v_until:<18} │\n"
        f"└───────────────────────────────┘"
        f"</pre>\n"
        f"<blockquote>💎 <b>INJECTION PROTOCOL:</b>\n"
        f"Pindutin ang <b>REVEAL INJECTION PATTERN</b> para sa eksaktong spin sequence.</blockquote>"
    )
    return text

def teleclaw_thinking(chat_id, action="Initializing Uplink", duration=2, final_text=None, reply_markup=None, call_id=None):
    try:
        bot.send_chat_action(chat_id, "typing")
        time.sleep(0.3)
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
            {"n": "LUCKY, GRACE & CHARM", "bb": 0}, {"n": "EMPTY THE BANK", "bb": 0}, {"n": "BOOK OF KING ARTHUR", "bb": 0}, {"n": "7 PIGGIES", "bb": 0}, {"n": "888 GOLD", "bb": 0}, {"n": "ALADDIN AND THE SORCERER", "bb": 0},
            {"n": "AMAZING MONEY MACHINE", "bb": 0}, {"n": "ANCIENT EGYPT CLASSIC", "bb": 0}, {"n": "BEOWULF", "bb": 0}, {"n": "BOOK OF TUT", "bb": 0}, {"n": "BRONCO SPIRIT", "bb": 0}, {"n": "CASH BONANZA", "bb": 1},
            {"n": "CASH ELEVATOR", "bb": 0}, {"n": "CONGO CASH", "bb": 0}, {"n": "COWBOYS GOLD", "bb": 0}, {"n": "CURSE OF THE WEREWOLF", "bb": 0}, {"n": "DA VINCI'S TREASURE", "bb": 0}, {"n": "DANCE PARTY", "bb": 0},
            {"n": "DAY OF DEAD", "bb": 0}, {"n": "DIAMOND ARE FOREVER", "bb": 0}, {"n": "DRAGON KINGDOM", "bb": 0}, {"n": "DRAGON TIGER", "bb": 0}, {"n": "DWARF MINE", "bb": 0}, {"n": "EMERALD KING", "bb": 0},
            {"n": "EMERALD KING JACKPOT", "bb": 0}, {"n": "FAIRYTALE FORTUNE", "bb": 0}, {"n": "FORBIDDEN THRONE", "bb": 0}, {"n": "GATES OF VALHALLA", "bb": 0}, {"n": "GLOOMY GRAVEYARD", "bb": 0}, {"n": "GOLD RUSH", "bb": 0},
            {"n": "GOLD TRAIN", "bb": 0}, {"n": "GOLDEN BEAUTY", "bb": 0}, {"n": "GOLDEN OX", "bb": 0}, {"n": "GREAT RHINO", "bb": 0}, {"n": "GREAT RHINO DELUXE", "bb": 0}, {"n": "HERCULES AND PEGASUS", "bb": 0},
            {"n": "HOT SAFARI", "bb": 0}, {"n": "JADE BUTTERFLY", "bb": 0}, {"n": "JOKER KING", "bb": 0}, {"n": "JOKER'S JEWELS", "bb": 0}, {"n": "JOURNEY TO THE WEST", "bb": 0}, {"n": "JUNGLE GORILLA", "bb": 0},
            {"n": "KNIGHT HOT SPOTZ", "bb": 0}, {"n": "LEPRECHAUN CAROL", "bb": 0}, {"n": "LEPRECHAUN SONG", "bb": 0}, {"n": "LUCKY DRAGONS", "bb": 0}, {"n": "LUCKY NEW YEAR", "bb": 0}, {"n": "MASTER CHEN'S FORTUNE", "bb": 0},
            {"n": "MEDUSA STRIKE", "bb": 0}, {"n": "MONEY MOUSE", "bb": 0}, {"n": "MONKEY WARRIOR", "bb": 0}, {"n": "MOON PRINCESS", "bb": 1}, {"n": "MYSTERIOUS", "bb": 0}, {"n": "MYSTERIOUS EGYPT", "bb": 0},
            {"n": "PANDA'S FORTUNE", "bb": 0}, {"n": "PEKING LUCK", "bb": 0}, {"n": "PHOENIX FORGE", "bb": 0}, {"n": "PIXIE WINGS", "bb": 0}, {"n": "QUEEN OF ATLANTIS", "bb": 0}, {"n": "QUEEN OF GOLD", "bb": 0},
            {"n": "RELEASE THE KRAKEN", "bb": 0}, {"n": "RETRO REELS", "bb": 0}, {"n": "SANTA", "bb": 0}, {"n": "SCARAB QUEEN", "bb": 0}, {"n": "SEVEN PIGGIES", "bb": 0}, {"n": "STAR BOUNTY", "bb": 0},
            {"n": "STREET RACER", "bb": 0}, {"n": "SUPER JOKER", "bb": 0}, {"n": "TEMPLAR TUMBLE", "bb": 0}, {"n": "THE CHAMPIONS", "bb": 0}, {"n": "THE WILD MACHINE", "bb": 0}, {"n": "THREE STAR FORTUNE", "bb": 0},
            {"n": "TREE OF RICHES", "bb": 0}, {"n": "TRIPLE DRAGONS", "bb": 0}, {"n": "TRIPLE JOKER", "bb": 0}, {"n": "VAMPIRE VS WOLVES", "bb": 0}, {"n": "VEGAS MAGIC", "bb": 0}, {"n": "VEGAS NIGHTS", "bb": 0},
            {"n": "VOODOO MAGIC", "bb": 0}, {"n": "WILD GLADIATORS", "bb": 0}, {"n": "WILD PIXIES", "bb": 0}, {"n": "WILD SPELLS", "bb": 0}, {"n": "WILD WALKER", "bb": 0}
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
            {"n": "BIKINI PARADISE", "bb": 0}, {"n": "DOUBLE FORTUNE", "bb": 0}, {"n": "GEM SAVIOUR CONQUEST", "bb": 0}, {"n": "HOOD VS WOLF", "bb": 0}, {"n": "HOTPOT", "bb": 0}, {"n": "ICE SCAPE", "bb": 0},
            {"n": "LEGEND OF HOU YI", "bb": 0}, {"n": "MEDUSA II", "bb": 0}, {"n": "MEDUSA", "bb": 0}, {"n": "MR. HALLOW-WIN", "bb": 0}, {"n": "PLUSHIE FRENZY", "bb": 0}, {"n": "PROSPERITY LION", "bb": 0},
            {"n": "REEL LOVE", "bb": 0}, {"n": "SHAOLIN SOCCER", "bb": 0}, {"n": "STEAMPUNK FORTUNE", "bb": 0}, {"n": "SYMBOLS OF EGYPT", "bb": 0}, {"n": "TREE OF FORTUNE", "bb": 0}, {"n": "WIN WIN WON", "bb": 0}
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
            {"n": "BAO BOON CHIN", "bb": 0}, {"n": "FORTUNE TREE", "bb": 0}
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
            {"n": "WOLF RITUAL", "bb": 0}
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
            {"n": "HIT MORE GOLD", "bb": 0}, {"n": "STICKY PIGGY", "bb": 0}, {"n": "GODDESS OF EGYPT", "bb": 0}, {"n": "BOOM! BOOM! GOLD!", "bb": 0}
        ],
        "BIGPOT GAMING": [
            {"n": "GOLDEN ERA", "bb": 0}, {"n": "SECRET OF RICHES", "bb": 0}, {"n": "LUCKY SEVEN", "bb": 0}, {"n": "WILD WEST SALOON", "bb": 0}, {"n": "PIRATE KING", "bb": 0}, {"n": "DRAGON LEGEND", "bb": 0},
            {"n": "MAGIC FOREST", "bb": 0}, {"n": "CANDY POP", "bb": 0}, {"n": "NEON CITY", "bb": 0}, {"n": "ANCIENT TREASURES", "bb": 0}, {"n": "SAMURAI'S HONOR", "bb": 0}, {"n": "VIKING GLORY", "bb": 0},
            {"n": "PHARAOH'S CURSE", "bb": 0}, {"n": "MYSTIC MOON", "bb": 0}, {"n": "JUNGLE ADVENTURE", "bb": 0}, {"n": "SPACE ODYSSEY", "bb": 0}, {"n": "ALADDIN'S WISH", "bb": 0}, {"n": "HERCULES", "bb": 0},
            {"n": "ZOMBIE ATTACK", "bb": 0}, {"n": "HALLOWEEN NIGHT", "bb": 0}, {"n": "CHRISTMAS JOY", "bb": 0}, {"n": "LUCKY FARM", "bb": 0}, {"n": "CASINO ROYALE", "bb": 0}, {"n": "NINJA SQUAD", "bb": 0},
            {"n": "ROBOT WARS", "bb": 0}, {"n": "FANTASY WORLD", "bb": 0}, {"n": "DRAGON SLAYER", "bb": 0}, {"n": "KUNG FU MASTER", "bb": 0}, {"n": "FOOTBALL FEVER", "bb": 0}, {"n": "RACING STARS", "bb": 0},
            {"n": "FRUIT SPLASH", "bb": 0}, {"n": "DIAMOND RUSH", "bb": 0}, {"n": "PANDA WARRIOR", "bb": 0}, {"n": "SKY GUARDIAN", "bb": 0}, {"n": "TREASURE ISLAND", "bb": 0}, {"n": "WILD SAFARI", "bb": 0},
            {"n": "MAGIC SPELL", "bb": 0}, {"n": "LUCKY DICE", "bb": 0}, {"n": "GOLDEN RUSH", "bb": 0}
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
            {"n": "CASH-A-CABANA", "bb": 0}, {"n": "CAT CLANS", "bb": 0}, {"n": "EGGSTRAVAGANZA", "bb": 0}, {"n": "EYE OF THE PANDA", "bb": 0}, {"n": "ITERERO", "bb": 0}, {"n": "JELLY REELS", "bb": 0},
            {"n": "POCKET ROCKETS", "bb": 0}, {"n": "WARRIOR WAYS", "bb": 0}, {"n": "WILD YIELD", "bb": 0}
        ],
        "FA CHAI": [
            {"n": "CHINESE NEW YEAR", "bb": 0}, {"n": "CHINESE NEW YEAR 2", "bb": 0}, {"n": "NIGHT MARKET", "bb": 0}, {"n": "GOLDEN GENIE", "bb": 0}, {"n": "THREE LITTLE PIGS", "bb": 0}, {"n": "DA LE MEN", "bb": 0},
            {"n": "MAGIC BEANS", "bb": 0}, {"n": "WIN WIN NEKO", "bb": 0}, {"n": "PANDA DRAGON BOAT", "bb": 0}, {"n": "BAO BOON CHIN", "bb": 0}, {"n": "WILD BUFFALO", "bb": 0}, {"n": "GOLDEN PANTHER", "bb": 0},
            {"n": "CRAZY CIRCUS", "bb": 0}, {"n": "ANIMAL RACING", "bb": 0}, {"n": "HALLOWEEN BOOM", "bb": 0}, {"n": "LEGEND OF DRAGON", "bb": 0}, {"n": "PHOENIX ADVENTURE", "bb": 0}, {"n": "LUCKY FORTUNES", "bb": 0},
            {"n": "GRAND BLUE", "bb": 0}, {"n": "TREASURE CRUISE", "bb": 0}, {"n": "GLORY OF ROME", "bb": 0}, {"n": "RICH MAN", "bb": 0}, {"n": "LUCKY CLOVER", "bb": 0}, {"n": "HOT POT PARTY", "bb": 0},
            {"n": "GOLDEN DRAGON", "bb": 0}, {"n": "KA-CHING", "bb": 0}, {"n": "PONG PONG HU", "bb": 0}, {"n": "MAHJONG WAYS 3", "bb": 0}, {"n": "FORTUNE GOD", "bb": 0}, {"n": "LUCKY WHEEL", "bb": 0},
            {"n": "DISCO NIGHT", "bb": 0}
        ],
        "JDB GAMING": [
            {"n": "BURGER SHOP", "bb": 0}, {"n": "KONGFU", "bb": 0}, {"n": "BIRDS AND ANIMALS", "bb": 0}, {"n": "LUCKY 7", "bb": 0}, {"n": "CRYSTAL REALM", "bb": 0}, {"n": "ORIENTAL BEAUTY", "bb": 0},
            {"n": "DRAGON MASTER", "bb": 0}, {"n": "BLOSSOM OF WEALTH", "bb": 0}, {"n": "KINGSMAN", "bb": 0}, {"n": "NINJA RUSH", "bb": 0}, {"n": "LUCKY RACING", "bb": 0}, {"n": "TRIPLE KING KONG", "bb": 0},
            {"n": "FORMOSA BEAR", "bb": 0}, {"n": "WINNING MASK", "bb": 0}, {"n": "GOAL", "bb": 0}, {"n": "BILLIONAIRE", "bb": 0}, {"n": "MONEY BAGS MAN", "bb": 0}, {"n": "LUCKY QILIN", "bb": 0},
            {"n": "OPEN SESAME", "bb": 0}, {"n": "LUCKY DRAGON", "bb": 0}, {"n": "SUPER NIUBI", "bb": 0}, {"n": "FLIRTING SCHOLAR TANG", "bb": 0}, {"n": "MAHJONG", "bb": 0}, {"n": "BANANA SAGA", "bb": 0},
            {"n": "STREET FIGHTER", "bb": 0}, {"n": "SHADE DRAGONS", "bb": 0}, {"n": "DRAGON WARRIOR", "bb": 0}, {"n": "LUCKY DIAMOND", "bb": 0}, {"n": "COFFEE TYCOON", "bb": 0}, {"n": "ZODIAC", "bb": 0},
            {"n": "TREASURE BOWL", "bb": 0}, {"n": "WILD WEST", "bb": 0}, {"n": "EGYPT TREASURE", "bb": 0}, {"n": "FUNKY KING", "bb": 0}, {"n": "CRAZY SCIENTIST", "bb": 0}, {"n": "PIRATE TREASURE", "bb": 0},
            {"n": "MAGIC WORLD", "bb": 0}, {"n": "WONDERLAND", "bb": 0}, {"n": "HALLOWEEN PARTY", "bb": 0}, {"n": "CHRISTMAS SURPRISE", "bb": 0}
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
            {"n": "ACE OF SPADES", "bb": 0}, {"n": "BEAST OF WEALTH", "bb": 0}, {"n": "BELL OF FORTUNE", "bb": 0}, {"n": "BIG WIN 777", "bb": 0}, {"n": "BLACK MAMBA", "bb": 0}, {"n": "BLAZIN' BULLFROG", "bb": 0},
            {"n": "BULL IN A CHINA SHOP", "bb": 0}, {"n": "CASH PUMP", "bb": 0}, {"n": "CASH VANDAL", "bb": 0}, {"n": "CELEBRATION OF WEALTH", "bb": 0}, {"n": "CHARLIE CHANCE", "bb": 0}, {"n": "CHINESE NEW YEAR", "bb": 0},
            {"n": "CHRONOS JOKER", "bb": 0}, {"n": "CLOUD QUEST", "bb": 0}, {"n": "COPS 'N' ROBBERS", "bb": 0}, {"n": "COURT OF HEARTS", "bb": 0}, {"n": "COYOTE CASH", "bb": 0}, {"n": "CRYSTAL SUN", "bb": 0},
            {"n": "DAWN OF EGYPT", "bb": 0}, {"n": "DEADLY 5", "bb": 0}, {"n": "DEMON", "bb": 0}, {"n": "DERBY WHEEL", "bb": 0}, {"n": "DIAMOND VORTEX", "bb": 0}, {"n": "DIVINE SHOWDOWN", "bb": 0},
            {"n": "DOOM OF EGYPT", "bb": 0}, {"n": "DRAGON MAIDEN", "bb": 0}, {"n": "DRAGON SHIP", "bb": 0}, {"n": "EASTER EGGS", "bb": 0}, {"n": "EGYPTIAN FORTUNE", "bb": 0}, {"n": "ENERGOONZ", "bb": 0},
            {"n": "EYE OF THE ATUM", "bb": 0}, {"n": "FACES OF FREYA", "bb": 0}, {"n": "FIRE JOKER FREEZE", "bb": 0}, {"n": "FIRE TOAD", "bb": 0}, {"n": "FORGE OF FORTUNES", "bb": 0}, {"n": "FORTUNE REWIND", "bb": 0},
            {"n": "FROZEN GEMS", "bb": 0}, {"n": "GHOST OF DEAD", "bb": 0}, {"n": "GIGANTUANZ", "bb": 0}, {"n": "GOLD KING", "bb": 0}, {"n": "GOLD TROPHY 2", "bb": 0}, {"n": "GOLD VOLCANO", "bb": 0},
            {"n": "GUNSLINGER", "bb": 0}, {"n": "HALLOWEEN JACK", "bb": 0}, {"n": "HAPPY HALLOWEEN", "bb": 0}, {"n": "HOLIDAY SPIRITS", "bb": 0}, {"n": "HOTEL YETI-WAY", "bb": 0}, {"n": "HOUSE OF DOOM", "bb": 0},
            {"n": "HUGO", "bb": 0}, {"n": "HUGO 2", "bb": 0}, {"n": "ICE JOKER", "bb": 0}, {"n": "IDOL OF FORTUNE", "bb": 0}, {"n": "IMMORTAL GUILD", "bb": 0}, {"n": "INFERNO STAR", "bb": 0},
            {"n": "IRON GIRL", "bb": 0}, {"n": "ISHIN", "bb": 0}, {"n": "IT'S MAGIC", "bb": 0}, {"n": "JACKPOT POKER", "bb": 0}, {"n": "JADE MAGICIAN", "bb": 0}, {"n": "JEWEL BOX", "bb": 0},
            {"n": "JOLLY ROGER", "bb": 0}, {"n": "JOLLY ROGER 2", "bb": 0}, {"n": "KISS REELS OF ROCK", "bb": 0}, {"n": "KNIGHT'S LIFE", "bb": 0}, {"n": "KRAKEN'S SKY", "bb": 0}, {"n": "LADY OF FORTUNE", "bb": 0},
            {"n": "LEGACY OF EGYPT", "bb": 0}, {"n": "LEPRECHAUN GOES EGYPT", "bb": 0}, {"n": "LEPRECHAUN GOES HELL", "bb": 0}, {"n": "LEPRECHAUN GOES TO WILD", "bb": 0}, {"n": "LORD MERLIN", "bb": 0}, {"n": "LOVE IS IN THE AIR", "bb": 0},
            {"n": "LUCKY DIAMONDS", "bb": 0}, {"n": "MADAME DESTINY", "bb": 0}, {"n": "MADAME DESTINY MEGAWAYS", "bb": 1}, {"n": "MAGICAL STACKS", "bb": 0}, {"n": "MAHJONG 88", "bb": 0}, {"n": "METAL DETECTOR", "bb": 0},
            {"n": "MOUNTAIN OF WEALTH", "bb": 0}, {"n": "MUERTO EN MITLAN", "bb": 0}, {"n": "MULTIFRUIT 81", "bb": 0}, {"n": "MYSTERY JOKER 6000", "bb": 0}, {"n": "NINJA FRUITS", "bb": 0}, {"n": "NYX", "bb": 0},
            {"n": "OCTOPUS TREASURE", "bb": 0}, {"n": "ODIN: PROTECTOR OF REALMS", "bb": 0}, {"n": "PAPYRUS", "bb": 0}, {"n": "PEARLS OF INDIA", "bb": 0}, {"n": "PERFECT GEMS", "bb": 0}, {"n": "PHOENIX REBORN", "bb": 0},
            {"n": "PIGGY BANK", "bb": 0}, {"n": "PIXIES VS PIRATES", "bb": 0}, {"n": "PLANET FORTUNE", "bb": 0}, {"n": "PROSPERITY PALACE", "bb": 0}, {"n": "QUEEN'S DAY TILT", "bb": 0}, {"n": "RABBIT HOLE RICHES", "bb": 0},
            {"n": "RAGING REX", "bb": 0}, {"n": "RAGING REX 2", "bb": 0}, {"n": "RAINBOW CHARMS", "bb": 0}, {"n": "REEL STEAL", "bb": 0}, {"n": "RISE OF DEAD", "bb": 0}, {"n": "RITUAL RESURRECTION", "bb": 0},
            {"n": "ROCCO GALLO", "bb": 0}, {"n": "ROCK-N-ROLLA", "bb": 0}, {"n": "RONIN", "bb": 0}, {"n": "ROYAL MASQUERADE", "bb": 0}, {"n": "SABATON", "bb": 0}, {"n": "SAILS OF GOLD", "bb": 0},
            {"n": "SAMURAI KEN", "bb": 0}, {"n": "SECRET OF THE STONES", "bb": 0}, {"n": "SINS", "bb": 0}, {"n": "SMILEY'S", "bb": 0}, {"n": "SPACE RACE", "bb": 0}, {"n": "SPARKY & SHORTZ", "bb": 0},
            {"n": "SPEED CASH", "bb": 0}, {"n": "STAR BLAST", "bb": 0}, {"n": "STICKY JOKER", "bb": 0}, {"n": "STREET MAGIC", "bb": 0}, {"n": "SUPER FLIP", "bb": 0}, {"n": "SWORD AND THE GRAIL", "bb": 0},
            {"n": "TALES OF ASGARD", "bb": 0}, {"n": "TEMPLE OF WEALTH", "bb": 0}, {"n": "TESTAMENT", "bb": 0}, {"n": "THAT'S RICH", "bb": 0}, {"n": "THE LAST SUNDOWN", "bb": 0}, {"n": "THE SWORD AND THE GRAIL", "bb": 0},
            {"n": "THUNDER SCREECH", "bb": 0}, {"n": "TWISTED SISTER", "bb": 0}, {"n": "VIKING RUNECRAFT", "bb": 0}, {"n": "WILD BLOOD", "bb": 0}, {"n": "WILD BLOOD 2", "bb": 0}, {"n": "WILD FALLS", "bb": 0},
            {"n": "WILD FRAMES", "bb": 0}, {"n": "WILD MELON", "bb": 0}, {"n": "WILD NORTH", "bb": 0}, {"n": "WIN-A-BEEST", "bb": 0}, {"n": "XMAS MAGIC", "bb": 0}
        ]
}

PROVIDERS_DATA = {
    "AGILA CLUB": DEFAULT_PROVIDERS_DATA,
    "HAHA777": DEFAULT_PROVIDERS_DATA,
    "TIKLUCK": DEFAULT_PROVIDERS_DATA,
    "JILIBET": DEFAULT_PROVIDERS_DATA,
    "BUGATTI PLAY": DEFAULT_PROVIDERS_DATA
}
SIGNALS = [
    "🟢\n10 Normal Spins -> 30 Turbo Spins",
    "🟡\n5 Quick Spins -> 15 Normal Spins",
    "🔥\n30 Turbo Spins then Buy Bonus",
    "🚀\n10 Turbo Spins -> 10 Quick Spins -> 5 Normal Spins then Buy Bonus",
    "💎\n20 Normal Spins then Add 1 peso bet and Buy Bonus",
    "⚡\n50 Turbo Spins (Low Stake)",
    "⭐\n8 Normal Spins -> 15 Quick Spins -> 10 Turbo Spins",
    "🍀\n7 Normal Spins -> 7 Turbo Spins -> 7 Quick Spins then Buy Bonus",
    "🎰\n15 Normal Spins -> 20 Turbo Spins -> 5 Quick Spins",
    "🎡\n12 Quick Spins -> 12 Normal Spins -> 12 Turbo Spins",
    "🌊\n25 Turbo Spins -> 10 Normal Spins",
    "🌋\n5 Normal Spins -> 5 Quick Spins -> 5 Turbo Spins -> Buy Bonus",
    "🌙\n40 Turbo Spins (Medium Stake)",
    "☀️\n10 Normal Spins -> 10 Turbo Spins -> 10 Quick Spins",
    "🐉\n18 Turbo Spins -> 12 Normal Spins",
    "🦁\n30 Quick Spins",
    "🐍\n9 Normal Spins -> 18 Turbo Spins -> 9 Quick Spins",
    "🦅\n15 Turbo Spins -> 15 Quick Spins",
    "🦄\n22 Normal Spins -> 11 Turbo Spins",
    "🌈\n7 Turbo Spins -> 7 Normal Spins -> 7 Quick Spins -> 7 Turbo Spins",
    "⚡\n50 Quick Spins",
    "❄️\n20 Turbo Spins -> 20 Normal Spins",
    "🌵\n10 Quick Spins -> 20 Turbo Spins",
    "🏰\n15 Normal Spins -> 15 Turbo Spins",
    "🏴‍☠️\n30 Turbo Spins -> Buy Bonus",
    "🛸\n10 Turbo Spins -> 10 Quick Spins -> 10 Normal Spins",
    "🧪\n5 Normal Spins -> 10 Turbo Spins -> 15 Quick Spins",
    "🥊\n20 Quick Spins -> 10 Turbo Spins",
    "🏎️\n60 Turbo Spins",
    "🏹\n12 Normal Spins -> 24 Turbo Spins",
    "🕯️\n15 Quick Spins -> 15 Normal Spins",
    "💎\n10 Turbo Spins -> 10 Quick Spins -> 10 Normal Spins -> Buy Bonus",
    "🍒\n20 Normal Spins -> 10 Turbo Spins",
    "🍋\n30 Quick Spins",
    "🍇\n15 Turbo Spins -> 15 Quick Spins",
    "🍉\n25 Normal Spins",
    "🔔\n10 Normal Spins -> 20 Turbo Spins",
    "🃏\n15 Quick Spins -> 15 Turbo Spins",
    "👑\n5 Normal Spins -> 5 Quick Spins -> 5 Turbo Spins -> 5 Normal Spins",
    "💰\n40 Turbo Spins",
    "🏦\n20 Quick Spins -> 20 Turbo Spins",
    "💎\n10 Normal Spins -> 30 Quick Spins",
    "🕵️\n15 Turbo Spins -> 15 Normal Spins",
    "🧙\n10 Quick Spins -> 10 Turbo Spins -> 10 Normal Spins",
    "🧚\n25 Turbo Spins",
    "🧜\n12 Normal Spins -> 12 Quick Spins",
    "🧞\n30 Turbo Spins -> Buy Bonus",
    "🧛\n20 Quick Spins -> 10 Normal Spins",
    "🐺\n15 Turbo Spins -> 15 Quick Spins -> 15 Normal Spins",
    "🦊\n15 Normal Spins -> 15 Turbo Spins -> 15 Quick Spins",
    "🔥\n10 Normal Spins -> 20 Quick Spins -> Buy Bonus",
    "💎\n30 Quick Spins -> Buy Bonus",
    "🚀\n15 Normal Spins -> Buy Bonus",
    "🌀\n15 Turbo Spins -> 15 Normal Spins",
    "🌌\n20 Quick Spins -> 10 Turbo Spins -> 20 Normal Spins",
    "⚡\n35 Turbo Spins -> 5 Quick Spins",
    "🌪️\n10 Normal -> 20 Quick -> 10 Turbo",
    "☄️\n45 Turbo Spins",
    "🌠\n8 Normal -> 8 Quick -> 8 Turbo -> 8 Normal",
    "🌊\n25 Quick Spins -> 25 Turbo Spins",
    "🔥\n15 Normal -> 30 Turbo",
    "🧊\n30 Quick -> 10 Normal",
    "🍃\n50 Normal Spins (Low Stake)",
    "🎍\n12 Quick -> 12 Turbo -> 12 Normal",
    "🎋\n20 Turbo -> 20 Quick",
    "🏮\n15 Normal -> 15 Quick -> 15 Turbo",
    "⛩️\n33 Turbo Spins",
    "🧧\n10 Normal -> 10 Quick -> 10 Turbo -> 10 Normal",
    "🏯\n40 Quick Spins",
    "🎴\n18 Turbo -> 18 Normal",
    "🎏\n22 Quick -> 11 Turbo",
    "🏔️\n10 Normal -> 40 Turbo",
    "🌋\n30 Quick -> 30 Turbo",
    "🏜️\n15 Normal -> 15 Turbo -> 15 Quick",
    "🏝️\n25 Turbo -> 25 Normal",
    "🏞️\n20 Quick -> 20 Normal",
    "🌉\n12 Turbo -> 12 Quick -> 12 Normal -> 12 Turbo",
    "🌃\n55 Turbo Spins",
    "🏙️\n15 Quick -> 45 Turbo",
    "🎡\n10 Normal -> 10 Quick -> 10 Turbo -> 10 Quick -> 10 Normal",
    "🎠\n30 Normal -> 30 Quick",
    "🎢\n20 Turbo -> 10 Quick -> 20 Turbo",
    "🚂\n50 Turbo Spins",
    "🌙\n20 Normal Spins -> 10 Turbo Spins -> 15 Quick Spins",
    "🐅\n8 Turbo Spins -> 12 Quick Spins -> 8 Turbo Spins -> 8 Normal Spins",
    "🦅\n14 Normal Spins -> 28 Turbo Spins",
    "🦂\n30 Quick Spins -> 20 Normal Spins -> Buy Bonus",
    "💎\n16 Turbo Spins -> 16 Normal Spins",
    "🌋\n25 Normal Spins -> 25 Turbo Spins",
    "🌲\n10 Turbo Spins -> 15 Normal Spins -> 20 Quick Spins",
    "🍃\n35 Quick Spins -> 15 Normal Spins",
    "🐘\n5 Normal Spins -> 15 Quick Spins -> 25 Turbo Spins -> 5 Normal Spins",
    "🦈\n40 Turbo Spins -> 10 Normal Spins",
    "🐙\n18 Quick Spins -> 18 Turbo Spins",
    "🐉\n12 Normal Spins -> 24 Turbo Spins -> 12 Quick Spins",
    "🐼\n20 Normal Spins -> 20 Quick Spins",
    "🍀\n7 Turbo Spins -> 14 Quick Spins -> 21 Normal Spins",
    "🌈\n30 Turbo Spins -> 30 Normal Spins",
    "⚡\n15 Quick Spins -> 15 Normal Spins -> 15 Turbo Spins",
    "🚂\n50 Quick Spins",
    "🚀\n22 Turbo Spins -> 11 Normal Spins",
    "🌍\n10 Normal Spins -> 30 Quick Spins -> 10 Turbo Spins",
    "🌠\n45 Turbo Spins (Medium Stake)",
    "🌞\n20 Quick Spins -> 10 Normal Spins -> 20 Turbo Spins",
    "🦇\n30 Normal Spins",
    "🕸️\n15 Turbo Spins -> 30 Normal Spins",
    "🔮\n5 Quick Spins -> 5 Turbo Spins -> 5 Normal Spins -> Buy Bonus",
    "🧪\n12 Normal Spins -> 12 Turbo Spins -> 12 Quick Spins -> 12 Normal Spins",
    "🗝️\n40 Normal Spins",
    "🧲\n18 Turbo Spins -> 18 Quick Spins -> 18 Normal Spins",
    "🎭\n25 Turbo Spins -> 25 Normal Spins",
    "🎩\n10 Quick Spins -> 20 Turbo Spins",
    "🃏\n15 Normal Spins -> 10 Quick Spins -> 15 Turbo Spins",
    "🏰\n20 Normal Spins -> 20 Turbo Spins",
    "👑\n50 Normal Spins -> Buy Bonus",
    "🏹\n30 Quick Spins -> 30 Normal Spins",
    "⚔️\n15 Turbo Spins -> 15 Normal Spins -> Buy Bonus",
    "🛡️\n40 Turbo Spins -> 20 Normal Spins",
    "🏺\n10 Normal Spins -> 10 Turbo Spins -> 10 Normal Spins -> 10 Quick Spins",
    "🏛️\n25 Turbo Spins -> 15 Quick Spins -> 10 Normal Spins",
    "📜\n20 Quick Spins -> 40 Normal Spins",
    "🐪\n15 Normal Spins -> 30 Quick Spins",
    "🐍\n10 Turbo Spins -> 5 Quick Spins -> 15 Normal Spins -> 10 Turbo Spins",
    "🦂\n45 Normal Spins",
    "🦜\n12 Quick Spins -> 24 Normal Spins",
    "🦍\n30 Turbo Spins -> 10 Quick Spins -> 10 Normal Spins",
    "🐊\n20 Normal Spins -> 15 Turbo Spins -> 5 Quick Spins -> 10 Normal Spins",
    "🦓\n15 Turbo Spins -> 15 Quick Spins -> 30 Normal Spins",
    "🦒\n35 Normal Spins -> 15 Turbo Spins",
    "🐘\n25 Quick Spins -> 25 Normal Spins",
    "🚙\n10 Normal Spins -> 20 Turbo Spins -> 30 Quick Spins",
    "🧭\n16 Normal Spins -> 16 Turbo Spins -> 16 Quick Spins",
    "🗺️\n8 Quick Spins -> 8 Normal Spins -> 8 Turbo Spins -> 8 Normal Spins"
]

# ================= ANIMATION LOGIC =================
def system_startup_animation(chat_id, message_id):
    try:
        bot.send_chat_action(chat_id, "typing")
        time.sleep(0.3)
    except:
        pass

def logout_animation(chat_id, message_id):
    steps = [
        "🔴 <b>DISCONNECTING UPLINK...</b>\n<code>[CLOSING SECURE SOCKET]</code>",
        "🔴 <b>CLEARING SESSION DATA...</b>\n<code>[CACHE WIPED]</code>",
        "🔴 <b>SESSION TERMINATED SAFELY.</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.5)
        except: pass

def reset_animation(chat_id, message_id):
    steps = [
        "🔄 <b>REBOOTING NEURAL CORE...</b>\n<code>[CYCLE 1/3]</code>",
        "🔄 <b>RECALIBRATING RNG SENSORS...</b>\n<code>[CYCLE 2/3]</code>",
        "🔄 <b>HARD RESET COMPLETE & READY.</b>\n<code>[CYCLE 3/3]</code>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.5)
        except: pass

def display_provider_games(chat_id, uid, provider_name):
    user_sessions[uid]["provider"] = provider_name
    selected_casino = user_sessions[uid].get("casino")
    games_list = PROVIDERS_DATA.get(selected_casino, {}).get(provider_name, [])
    kb = types.InlineKeyboardMarkup(row_width=2)
    game_btns = []
    for g in games_list:
        game_n = g["n"] if isinstance(g, dict) else g
        game_btns.append(types.InlineKeyboardButton(game_n, callback_data=f"game:{game_n}"))
    for i in range(0, len(game_btns), 2):
        kb.row(*game_btns[i:i+2])
    kb.row(types.InlineKeyboardButton("🔙 BACK TO PROVIDERS", callback_data="open_menu"))

    msg = send_menu_bubble(chat_id, f"🎰 <b>{html.escape(provider_name)}</b>\nShowing {len(games_list)} Games Available:", reply_markup=kb, photo=INTRO_IMAGE_URL)
    user_sessions[uid]["last_msg"] = msg.message_id

def live_encoding_animation(chat_id, message_id, uid, selected_casino, session_id):
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(
        types.InlineKeyboardButton("👁️ REVEAL INJECTION PATTERN", callback_data="show_pattern"),
        types.InlineKeyboardButton("🔄 RE-SYNC RNG DATA", callback_data="run_gen"),
        types.InlineKeyboardButton("🔙 BACK TO GAMES", callback_data="change_game"),
        types.InlineKeyboardButton("🔙 BACK TO PROVIDERS", callback_data="open_menu"),
        types.InlineKeyboardButton("🔙 BACK TO CASINOS", callback_data="change_platform")
    )

    try:
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        init_telemetry = (
            f"{res_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>CYBER TELEMETRY ACTIVE:</b>\n"
            f"<code>[SYS_SYNC] >> INITIATING PLATFORM HANDSHAKE...</code>"
        )
        bot.edit_message_text(
            init_telemetry, 
            chat_id, message_id, parse_mode="HTML", reply_markup=inline_kb
        )
    except: pass
    time.sleep(1.2)

    safe_casino = html.escape(str(selected_casino))
    frames = [
        (
            f"📡 <b>LIVE TELEMETRY STREAM:</b>\n"
            f"<code>[GATEWAY] >> CONNECTED TO {safe_casino.upper()}</code>\n"
            f"<code>[LATENCY] >> 11ms · JITTER: 0.1ms</code>\n"
            f"<code>[METER]   [■■■■■■■■■■] 100% ONLINE</code>"
        ),
        (
            f"📡 <b>LIVE TELEMETRY STREAM:</b>\n"
            f"<code>[RNG_SEED]>> DYNAMIC ENTROPY STREAMING</code>\n"
            f"<code>[VOLAT]   >> SURGE COEFFICIENT: OPTIMAL (x1.42)</code>\n"
            f"<code>[STATUS]  >> PATTERN TIME-LOCKED TO SESSION</code>"
        ),
        (
            f"📡 <b>LIVE TELEMETRY STREAM:</b>\n"
            f"<code>[MONITOR] >> LIVE RTP PEAK DETECTED</code>\n"
            f"<code>[WINDOW]  >> VALIDATION RUNNING · DO NOT REFRESH</code>\n"
            f"<code>[SIGNAL]  >> READY FOR EXECUTION</code>"
        )
    ]
    
    for frame in frames:
        if uid not in user_sessions or user_sessions[uid].get("encoding") == False or user_sessions[uid].get("encoding_id") != session_id:
            break
        try:
            res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n{frame}",
                parse_mode="HTML"
            )
        except Exception:
            break 
        time.sleep(1.2)

    if uid in user_sessions and user_sessions[uid].get("encoding_id") == session_id:
        user_sessions[uid]["encoding"] = False
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        final_footer = (
            f"🟢 <b>STATUS:</b> <code>TELEMETRY LOCKED & SYNCED</code>\n"
            f"<code>[CORE] >> EXECUTE BEFORE EXPIRATION WINDOW</code>\n"
            f"<blockquote>💡 <i>Paalala: Mag-log in muna sa casino bago simulan ang pattern sequence.</i></blockquote>"
        )
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n{final_footer}",
                parse_mode="HTML",
                reply_markup=inline_kb
            )
        except: pass


# ================= HELPERS =================
def delete_user_past_msg(chat_id, uid):
    if user_sessions.get(uid, {}).get("last_msg"):
        try: 
            bot.delete_message(chat_id, user_sessions[uid]["last_msg"])
        except: 
            pass
    if user_sessions.get(uid, {}).get("last_pattern_msg_id"):
        try:
            bot.delete_message(chat_id, user_sessions[uid]["last_pattern_msg_id"])
        except:
            pass
        user_sessions[uid]["last_pattern_msg_id"] = None

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
    bot.send_message(admin_id_val, f"👮‍♂️ <b>PROTECT CONTENT TOGGLED</b>\n━━━━━━━━━━━━━━━━━━━━━━\nStatus: <b>{status}</b>", parse_mode="HTML")

@bot.message_handler(commands=["protecton"])
def protect_on_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    save_protect_setting(True)
    bot.send_message(admin_id_val, "👮‍♂️ <b>PROTECT CONTENT ENABLED</b>\n━━━━━━━━━━━━━━━━━━━━━━\nHindi na pwedeng i-copy o i-forward ang mga messages ng bot.", parse_mode="HTML")

@bot.message_handler(commands=["protectoff"])
def protect_off_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    save_protect_setting(False)
    bot.send_message(admin_id_val, "👮‍♂️ <b>PROTECT CONTENT DISABLED</b>\n━━━━━━━━━━━━━━━━━━━━━━\nPwede nang i-copy, i-save at i-forward ang mga messages.", parse_mode="HTML")

@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
        
    if message.from_user.id != admin_id_val: return
    total = len(user_ids)
    bot.send_message(admin_id_val, f"📊 <b>BOT STATISTICS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n👥 <b>Total Users:</b> {total}", parse_mode="HTML")

@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(message):
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except:
        admin_id_val = 0
        
    if message.from_user.id != admin_id_val: 
         return
    
    # Notify admin that broadcast is starting
    status_msg = bot.send_message(admin_id_val, "🛰 <b>Broadcasting started...</b>", parse_mode="HTML")
    
    target_msg = None
    text_to_send = None
    if message.reply_to_message:
        target_msg = message.reply_to_message
    else:
        command_parts = message.text.split(None, 1)
        if len(command_parts) < 2:
            bot.edit_message_text("❌ <b>Usage:</b>\n1. Reply to any message with <code>/broadcast</code>\n2. <code>/broadcast Your message here</code>", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
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
                        f"🛰 <b>Broadcasting...</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👥 <b>Processed:</b> {i+1}/{total}\n"
                        f"✅ <b>Success:</b> {success}\n"
                        f"❌ <b>Failed:</b> {failed}"
                    )
                    bot.edit_message_text(progress, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
                except: pass
            
            # Tiny delay to avoid aggressive flooding
            import time
            time.sleep(0.05)
            
        final_report = (
            f"📢 <b>BROADCAST REPORT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Success:</b> {success}\n"
            f"❌ <b>Failed:</b> {failed}\n"
            f"👥 <b>Total Users:</b> {total}"
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
                bot.send_message(admin_id_val, f"🆕 <b>NEW USER STARTED BOT</b>\nUser: {message.from_user.first_name}{username_str}\nID: <code>{uid}</code>", parse_mode="HTML")
        except: pass

    # Find the matching "AGILA CLUB" casino in CASINO_DATA
    selected_casino = "AGILA CLUB"
    for c in CASINO_DATA.keys():
        if "AGILA" in c.upper().replace(" ", ""):
            selected_casino = c
            break
            
    user_sessions[uid]["casino"] = selected_casino
    
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
                bot.send_message(admin_id_val, f"🆕 <b>NEW USER STARTED BOT</b>\nUser: {message.from_user.first_name}{username_str}\nID: <code>{uid}</code>", parse_mode="HTML")
        except: pass

    # INTRO SCREEN (Always show this)
    user_fullname = (f"{message.from_user.first_name} {message.from_user.last_name}".strip() if message.from_user.last_name else message.from_user.first_name)
    user_fullname = html.escape(user_fullname)
    
    teleclaw_thinking(message.chat.id, "Initializing Uplink", duration=2)

    caption = (
        f"⚜️ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> ⚜️\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Mabuhay, <b>{user_fullname}</b>!\n\n"
        f"<code>[SYSTEM: ONLINE] · [CORE: VIP-v5.8] · [LATENCY: 12ms]</code>\n\n"
        f"Welcome to the high-frequency <b>RNG Pattern Recognition & Seed Audit Architecture</b>. Ang aming deep-learning engine ay sumusubaybay sa real-time casino seeds, platform RTP curves, at volatility shifts.\n\n"
        f"<b>PLATFORM TELEMETRY SUITE:</b>\n"
        f"• 📊 <b>Live RNG Seed Audit:</b> <code>Real-time entropy accuracy</code>\n"
        f"• 🧬 <b>Quantum Seed Decoder:</b> <code>Active session sync</code>\n"
        f"• 🎯 <b>Dynamic Pattern Injection:</b> <code>99.2% precision lock</code>\n\n"
        f"Pindutin ang <b>Start JACKPOT READER</b> upang simulan ang secure telemetry handshake."
    )

    
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not user_sessions[uid].get("is_logged_in"):
        kb.add(
            types.InlineKeyboardButton("🚀 Start JACKPOT READER", callback_data="user_login")
        )
    else:
        kb.add(types.InlineKeyboardButton("🚀 INITIALIZE SYSTEM", callback_data="intro_proceed"))

    kb.add(types.InlineKeyboardButton("❓ How to use the system?", callback_data="how_to_use"))

    msg = send_menu_bubble(message.chat.id, caption, reply_markup=kb, photo=INTRO_IMAGE_URL)
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "how_to_use")
def handle_how_to_use(call):
    uid = call.from_user.id
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    delete_user_past_msg(call.message.chat.id, uid)
    
    teleclaw_thinking(call.message.chat.id, "Working", duration=2, call_id=call.id)
    
    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_to_home")
    )
    
    how_to_use_text = (
        "📈 <b>SYSTEM INTEGRATION & OPERATIONS GUIDE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Sundin ang aming opisyal na step-by-step VIP algorithm procedure:\n\n"
        "1️⃣ <b>PERFORM LIVE RNG AUDIT</b>\n"
        "• I-click ang <b>Start JACKPOT READER</b> sa main screen.\n"
        "• Pindutin ang 📊 <b>CHECK LIVE RNG ANALYSIS</b> para masuri ang flow accuracy bago magsimula.\n\n"
        "2️⃣ <b>PLATFORM SELECTION</b>\n"
        "• Piliin ang iyong nilalaruang Casino Platform upang ma-load ang tamang live server parameters.\n\n"
        "3️⃣ <b>PLATFORM SYNCHRONIZATION</b>\n"
        "• Gamitin ang <b>LOG IN TO START</b> portal upang maisabay ng aming AI reader ang pattern cycle sa active session ng iyong account.\n\n"
        "4️⃣ <b>DEPLOY PATTERN SEQUENCE</b>\n"
        "• Piliin ang laro at pindutin ang <b>REVEAL INJECTION PATTERN</b> upang sundin ang calibrated spin sequence bago matapos ang expiration window.\n\n"
        "<blockquote>💬 <i>Official Channel & Support:</i> https://t.me/+emEhYhP29m41OWQ9</blockquote>"
    )
    msg = send_menu_bubble(call.message.chat.id, how_to_use_text, reply_markup=kb, photo=None)
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
    
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("📊 CHECK LIVE RNG ANALYSIS", url="https://t.me/slotpatternbot/winrate"))
    kb.row(
        types.InlineKeyboardButton("🚀 PROCEED", callback_data="user_login_proceed"),
        types.InlineKeyboardButton("🔙 HOME", callback_data="back_to_home")
    )
    
    caption = (
        "📊 <b>REAL-TIME SEED ACCURACY AUDIT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Bago simulan ang system tracking mechanics, mangyaring suriin muna ang live RNG metrics ng mga verified platforms na may mataas na win rate at optimal accuracy levels.\n\n"
        "I-click ang <b>CHECK LIVE RNG ANALYSIS</b> sa ibaba, at pagkatapos ay piliin ang <b>PROCEED TO SYSTEM</b> upang magpatuloy."
    )
    msg = send_menu_bubble(call.message.chat.id, caption, reply_markup=kb, photo=None)
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "user_login_proceed")
def handle_user_login_proceed(call):
    uid = call.from_user.id
    user_sessions[uid]["is_logged_in"] = True
    
    teleclaw_thinking(call.message.chat.id, "Working", duration=2, call_id=call.id)
    
    # Proceed to casino selection
    choose_casino_platform(call)

@bot.callback_query_handler(func=lambda c: c.data == "intro_proceed")
def choose_casino_platform(call):
    uid = call.from_user.id
    
    # Check if logged in
    if not user_sessions.get(uid, {}).get("is_logged_in"):
        bot.answer_callback_query(call.id, "⚠️ You need to log in first!", show_alert=True)
        return

    delete_user_past_msg(call.message.chat.id, uid)

    teleclaw_thinking(call.message.chat.id, "Working", duration=2, call_id=call.id)

    kb = types.InlineKeyboardMarkup(row_width=2)
    cas_btns = [types.InlineKeyboardButton(f"🏛 {casino}", callback_data=f"set_casino_{casino}") for casino in CASINO_DATA.keys()]
    for i in range(0, len(cas_btns), 2):
        kb.row(*cas_btns[i:i+2])
    kb.row(types.InlineKeyboardButton("🔙 BACK TO HOME", callback_data="back_to_home"))

    msg = send_menu_bubble(call.message.chat.id, "🏗 <b>SELECT PLATFORM DATABASE</b>\n━━━━━━━━━━━━━━━━━━━━━━\nChoose your Casino Platform to load the correct RNG server parameters and calibrated hit frequencies:", reply_markup=kb, photo=None)
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_casino_"))
def confirm_casino_selection(call):
    uid = call.from_user.id
    selected_casino = call.data.replace("set_casino_", "")
    user_sessions[uid]["casino"] = selected_casino

    reg_link = CASINO_DATA.get(selected_casino, "https://google.com")
    delete_user_past_msg(call.message.chat.id, uid)

    teleclaw_thinking(call.message.chat.id, "Hacking", duration=3, call_id=call.id)

    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🔐 LOG IN TO START", url=reg_link))
    kb.row(
        types.InlineKeyboardButton("🚀 PROCEED", callback_data="open_menu"),
        types.InlineKeyboardButton("🔙 CASINOS", callback_data="intro_proceed")
    )
    
    welcome_text = (
        f"🏛 <b>PLATFORM SELECTED: {selected_casino}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "To initialize the <b>RNG Synchronization Protocol</b>, follow these instructions:\n\n"
        "1️⃣ Click <b>LOG IN TO START</b> below to open the secure platform.\n"
        "2️⃣ Log in or Register your account on the verified site.\n"
        "3️⃣ Return here and click <b>PROCEED TO SYSTEM</b>.\n\n"
        "<blockquote>⚠️ <i>The AI algorithm only synchronizes with active sessions detected through our link.</i></blockquote>"
    )
    msg = send_menu_bubble(call.message.chat.id, welcome_text, reply_markup=kb, photo=None)
    user_sessions[uid]["last_msg"] = msg.message_id

# show_pattern moved to App.tsx

@bot.message_handler(func=lambda m: m.text in ["🔄 Re-Generate Pattern", "🔄 RE-SYNC RNG DATA", "🔄 Re-Sync RNG Data"])
def regenerate_btn(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⚡ <b>RE-INITIALIZING ALGORITHM...</b>", parse_mode="HTML")
    run_gen_logic(chat_id, msg.message_id, message.from_user, user_sessions[uid].get("casino", "UNKNOWN"), user_sessions[uid].get("game", "UNKNOWN"), user_sessions[uid].get("provider", "UNKNOWN"))


@bot.callback_query_handler(func=lambda c: c.data == "change_game")
def change_game_callback(call):
    uid = call.from_user.id
    provider = user_sessions[uid].get("provider")
    if not provider:
        bot.answer_callback_query(call.id, "⚠️ Provider not found!", show_alert=True)
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
    
    main_menu(call.message.chat.id, uid)

# Old show_games removed

@bot.message_handler(func=lambda m: m.text == "🔙 BACK")
def back_to_prov(message): 
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    main_menu(message.chat.id, message.from_user.id)

# Old pick_game removed

def run_gen_logic(chat_id, message_id, user_obj, casino, game, provider):
    uid = user_obj.id if hasattr(user_obj, 'id') else user_obj
    if (time.time() - user_sessions[uid].get("last_gen_time", 0)) < 20:
        bot.send_message(chat_id, "⚠️ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...")
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
            bot.send_message(admin_id_val, f"📊 <b>SIGNAL GENERATED</b>\nUser: {name}{username} (<code>{uid}</code>)\n🏛 <b>Casino:</b> {casino}\n🎮 <b>Provider:</b> {provider}\n🎰 <b>Game:</b> {game}", parse_mode="HTML")
    except: pass

    # 4-STAGE REALISTIC CYBER VIP TELEMETRY ANIMATION
    stages = [
        {
            "title": "⚡ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>UPLINK</code>",
            "log": "[UPLINK] >> CONNECTING [TLS v1.3]",
            "detail": "[CIPHER] >> TLS_AES_256_GCM_SHA384",
            "percent": 15,
            "ping": "12ms PING"
        },
        {
            "title": "🧬 <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>SEED SYNC</code>",
            "log": f"[SERVER] >> {html.escape(str(casino)).upper()} RNG FOUND",
            "detail": f"[SEED]   >> 0x{str(uuid.uuid4())[:8].upper()}... [DECODED]",
            "percent": 48,
            "ping": "ANALYZING"
        },
        {
            "title": "🛰 <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>NEURAL FIT</code>",
            "log": f"[TARGET] >> {html.escape(str(game)).upper()} ({html.escape(str(provider))})",
            "detail": "[CYCLES] >> HIT FREQUENCY CALIBRATED",
            "percent": 82,
            "ping": "COMPUTING"
        },
        {
            "title": "✅ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>LOCKED</code>",
            "log": "[STATUS] >> HIGH VOLATILITY INJECTION READY",
            "detail": "[STREAM] >> DEPLOYING SIGNAL TELEMETRY",
            "percent": 100,
            "ping": "READY"
        }
    ]

    for stage in stages:
        meter = render_meter(stage["percent"], 10)
        status_text = (
            f"{stage['title']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<code>{stage['log']}</code>\n"
            f"<code>{stage['detail']}</code>\n"
            f"<code>[{meter}] {stage['percent']}% · {stage['ping']}</code>"
        )
        try:
            bot.edit_message_text(status_text, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.75)
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
    
    prob_val = random.uniform(96.5, 99.4)
    result_text = format_cyber_box(game, casino, provider, prob_val, fake_id, v_until)

    user_sessions[uid]["result_text"] = result_text
    user_sessions[uid]["pattern"] = random.choice(valid_signals)
    user_sessions[uid]["encoding"] = True 
    session_id = str(uuid.uuid4())
    user_sessions[uid]["encoding_id"] = session_id
    
    # Inline buttons for everything (Chess bot compact grid layout)
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.row(types.InlineKeyboardButton("👁️ REVEAL INJECTION PATTERN", callback_data="show_pattern"))
    inline_kb.row(types.InlineKeyboardButton("🔄 RE-SYNC RNG DATA", callback_data="run_gen"))
    inline_kb.row(
        types.InlineKeyboardButton("🔙 GAMES", callback_data="change_game"),
        types.InlineKeyboardButton("🔙 PROVIDERS", callback_data="open_menu"),
        types.InlineKeyboardButton("🔙 CASINOS", callback_data="change_platform")
    )
    
    # Remove any lingering ReplyKeyboardMarkup
    remove_kb = types.ReplyKeyboardRemove()
    
    # Send message with all inline buttons
    msg = bot.send_message(chat_id, result_text, reply_markup=inline_kb, parse_mode="HTML")
    
    user_sessions[uid]["last_msg"] = msg.message_id
    user_sessions[uid]["last_kb_msg"] = None

    # Start the live encoding animation thread
    t = threading.Thread(target=live_encoding_animation, args=(chat_id, msg.message_id, uid, casino, session_id))
    t.daemon = True
    t.start()

@bot.callback_query_handler(func=lambda c: c.data == "run_gen")
def run_gen(call):
    uid = call.from_user.id
    
    # Check if we are regenerating from an existing message
    if call.message.text and ("SIGNAL DETECTED" in call.message.text or "CYBER VIP ALGORITHM" in call.message.text or "𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑" in call.message.text):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        msg = bot.send_message(call.message.chat.id, "⚡ <b>RE-INITIALIZING ALGORITHM...</b>", parse_mode="HTML")
        message_id = msg.message_id
    else:
        try:
            msg = bot.edit_message_text("⚡ <b>RE-INITIALIZING ALGORITHM...</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            message_id = msg.message_id
        except:
            msg = bot.send_message(call.message.chat.id, "⚡ <b>RE-INITIALIZING ALGORITHM...</b>", parse_mode="HTML")
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
            types.InlineKeyboardButton("📊 CHECK LIVE RNG ANALYSIS", url="https://t.me/slotpatternbot/winrate")
        )
        caption = (
            "📊 <b>REAL-TIME SEED ACCURACY AUDIT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "I-click ang button sa ibaba upang masuri ang live RNG metrics at win rate analysis:"
        )
        send_menu_bubble(message.chat.id, caption, reply_markup=kb, photo=None)
    except Exception as e:
        print(f"Error in winrate_cmd: {e}")

@bot.message_handler(commands=["howtouse"])
def howtouse_cmd(message):
    try:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("❓ How to use the system?", callback_data="how_to_use")
        )
        caption = (
            "❓ <b>SYSTEM OPERATION GUIDE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "I-click ang button sa ibaba upang mabasa ang kumpletong gabay sa paggamit ng system:"
        )
        send_menu_bubble(message.chat.id, caption, reply_markup=kb, photo=None)
    except Exception as e:
        print(f"Error in howtouse_cmd: {e}")

@bot.message_handler(commands=["topgames"])
def send_topgames_casinos_menu(message):
    try:
        kb = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for casino in CASINO_DATA.keys():
            buttons.append(types.InlineKeyboardButton(text=f"🎰 {casino}", callback_data=f"tgcas:{casino}"))
        kb.add(*buttons)
        send_menu_bubble(message.chat.id, "🔥 <b>TOP 10 GAMES MENU</b> 🔥\n\nPumili ng Casino platform upang makita ang Top 10 recommended winning games:", parse_mode="HTML", reply_markup=kb, photo=None)
    except Exception as e:
        print(f"Error in topgames menu: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tgcas:"))
def handle_topgames_casino_select(call):
    try:
        matched_casino = call.data.split("tgcas:")[1]
        cached_games = get_or_generate_top_games(matched_casino)
        if not cached_games:
            bot.answer_callback_query(call.id, "❌ No games available.", show_alert=True)
            return
            
        reply_text = f"🔥 <b>TOP 10 GAMES FOR {matched_casino}</b> 🔥\n\n"
        for i, game in enumerate(cached_games, 1):
            reply_text += f"{i}.) <b>{game['name']}</b>\n<blockquote>📈 {game['rtp']}% RTP</blockquote>\n<i>{game['provider']}</i>\n\n"
        reply_text += f"⏳ <i>Valid for next 6 hours.</i>"
        
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🔙 BACK TO CASINOS", callback_data="change_platform"))

        send_menu_bubble(call.message.chat.id, reply_text, reply_markup=kb, photo=None)
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
            bot.send_message(message.chat.id, f"❌ <b>Casino not found.</b>", parse_mode="HTML")
            return
            
        cached_games = get_or_generate_top_games(matched_casino)
        if not cached_games:
            bot.send_message(message.chat.id, f"❌ <b>No games available.</b>", parse_mode="HTML")
            return
            
        reply_text = f"🔥 <b>TOP 10 GAMES FOR {matched_casino}</b> 🔥\n\n"
        for i, game in enumerate(cached_games, 1):
            reply_text += f"{i}.) <b>{game['name']}</b>\n<blockquote>📈 {game['rtp']}% RTP</blockquote>\n<i>{game['provider']}</i>\n\n"
        reply_text += f"⏳ <i>Valid for next 6 hours.</i>"
        
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🔙 BACK TO CASINOS", callback_data="change_platform"))

        send_menu_bubble(message.chat.id, reply_text, reply_markup=kb, photo=None)
        
    except Exception as e:
        print(f"Error in topgames: {e}")

@bot.message_handler(commands=["help"])
def help_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0

    help_text = "📖 <b>AVAILABLE COMMANDS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    help_text += "🚀 /start - Open Signal Dashboard\n"
    help_text += "🎮 /topgames - Select Casino & View Top 10 Games\n"
    help_text += "📊 /winrate - Check Live RNG Analysis\n"
    help_text += "❓ /howtouse - System operations guide"
        
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

    if message.from_user.id == admin_id_val:
        admin_text = "🛠 <b>ADMIN PANEL HELP</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
        admin_text += "📊 /stats - Show user statistics\n"
        admin_text += "📢 /broadcast - Broadcast msg to all users\n"
        admin_text += "📂 /backup_users - Export user database\n"
        admin_text += "📥 /restore_users - (Reply to file) Restore database\n"
        admin_text += "🎮 /top5 & /top10 - Game recommendations"
        bot.send_message(message.chat.id, admin_text, parse_mode="HTML")



# ================= OVERRIDDEN LOGIC FOR MULTI-CASINO PROVIDERS =================
def render_meter(percent, length=10):
    try:
        filled = int(round((float(percent) / 100.0) * length))
    except:
        filled = 9
    filled = max(0, min(length, filled))
    return "■" * filled + "□" * (length - filled)

def format_cyber_box(game, casino, provider, prob, fake_id, v_until):
    safe_game = html.escape(str(game))
    safe_casino = html.escape(str(casino))
    safe_prov = html.escape(str(provider))
    meter = render_meter(prob, 10)
    
    text = (
        f"⚜️ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> <code>#{fake_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<pre>"
        f"┌─ PLATFORM TELEMETRY ──────────┐\n"
        f"│ TARGET   : {safe_game[:16]:<16} │\n"
        f"│ CASINO   : {safe_casino[:16]:<16} │\n"
        f"│ PROVIDER : {safe_prov[:16]:<16} │\n"
        f"│ ACCURACY : {prob:.2f}%           │\n"
        f"│ METER    : [{meter}]     │\n"
        f"│ VOLATILE : HIGH [SURGE PEAK]  │\n"
        f"│ VALID TO : {v_until:<18} │\n"
        f"└───────────────────────────────┘"
        f"</pre>\n"
        f"<blockquote>💎 <b>INJECTION PROTOCOL:</b>\n"
        f"Pindutin ang <b>REVEAL INJECTION PATTERN</b> para sa eksaktong spin sequence.</blockquote>"
    )
    return text

def display_provider_games(chat_id, uid, provider_name):
    user_sessions[uid]["provider"] = provider_name
    selected_casino = user_sessions[uid].get("casino")
    games_list = PROVIDERS_DATA.get(selected_casino, {}).get(provider_name, [])
    # games_list is now a list of dicts like {"n": "Game", "bb": 1}
    display_names = [g["n"] for g in games_list]

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("🔙 BACK TO PROVIDERS"))
    kb.add(*[types.KeyboardButton(n) for n in display_names])

    msg = bot.send_message(chat_id, f"🎰 <b>{html.escape(provider_name)}</b>\nShowing {len(display_names)} Games Available:", reply_markup=kb, parse_mode="HTML")
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
    kb.add(types.KeyboardButton("🔙 BACK TO CASINOS"))
    kb.add(*[types.KeyboardButton(p) for p in providers_list])
    msg = bot.send_message(chat_id, "⚙️ <b>MAIN CONTROL PANEL:</b>\n━━━━━━━━━━━━━━━━━━━━━━\nSelect your preferred Slot Provider to begin analysis:", reply_markup=kb, parse_mode="HTML")
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
    if (time.time() - user_sessions[uid].get("last_gen_time", 0)) < 15:
        bot.send_message(chat_id, "⚠️ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...")
        return

    user_sessions[uid]["last_gen_time"] = time.time()
    
    # 4-STAGE REALISTIC 𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑 TELEMETRY ANIMATION
    stages = [
        {
            "title": "⚡ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>UPLINK</code>",
            "log": "[UPLINK] >> CONNECTING [TLS v1.3]",
            "detail": "[CIPHER] >> TLS_AES_256_GCM_SHA384",
            "percent": 15,
            "ping": "12ms PING"
        },
        {
            "title": "🧬 <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>SEED SYNC</code>",
            "log": f"[SERVER] >> {html.escape(str(casino)).upper()} RNG FOUND",
            "detail": f"[SEED]   >> 0x{str(uuid.uuid4())[:8].upper()}... [DECODED]",
            "percent": 48,
            "ping": "ANALYZING"
        },
        {
            "title": "🛰 <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>NEURAL FIT</code>",
            "log": f"[TARGET] >> {html.escape(str(game_name)).upper()} ({html.escape(str(provider))})",
            "detail": "[CYCLES] >> HIT FREQUENCY CALIBRATED",
            "percent": 82,
            "ping": "COMPUTING"
        },
        {
            "title": "✅ <b>𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑</b> · <code>LOCKED</code>",
            "log": "[STATUS] >> HIGH VOLATILITY INJECTION READY",
            "detail": "[STREAM] >> DEPLOYING SIGNAL TELEMETRY",
            "percent": 100,
            "ping": "READY"
        }
    ]

    for stage in stages:
        meter = render_meter(stage["percent"], 10)
        status_text = (
            f"{stage['title']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<code>{stage['log']}</code>\n"
            f"<code>{stage['detail']}</code>\n"
            f"<code>[{meter}] {stage['percent']}% · {stage['ping']}</code>"
        )
        try:
            bot.edit_message_text(status_text, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.75)
        except:
            pass

    # Notify Admin
    try:
        admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
        if admin_id_val:
            name = user_obj.first_name + (f" {user_obj.last_name}" if user_obj.last_name else "")
            username = f" (@{user_obj.username})" if user_obj.username else ""
            bot.send_message(admin_id_val, f"📊 <b>SIGNAL GENERATED</b>\nUser: {name}{username} (<code>{uid}</code>)\n🏛 <b>Casino:</b> {casino}\n🎮 <b>Provider:</b> {provider}\n🎰 <b>Game:</b> {game_name}", parse_mode="HTML")
    except: pass

    # Delete the generating message and previous pattern message before showing result
    try: bot.delete_message(chat_id, message_id)
    except: pass
    if user_sessions.get(uid, {}).get("last_pattern_msg_id"):
        try: bot.delete_message(chat_id, user_sessions[uid]["last_pattern_msg_id"])
        except: pass
        user_sessions[uid]["last_pattern_msg_id"] = None

    # Find if game has Buy Bonus
    has_bb = False
    provider_games = PROVIDERS_DATA.get(casino, {}).get(provider, [])
    for g in provider_games:
        if g["n"] == game_name:
            has_bb = (g.get("bb", 0) == 1)
            break

    # Filtering signals
    if has_bb:
        valid_signals = SIGNALS
    else:
        valid_signals = [s for s in SIGNALS if "Buy Bonus" not in s]
    
    if "PG" in provider.upper():
        valid_signals = [s for s in valid_signals if "Turbo" not in s]
    
    if not valid_signals: valid_signals = SIGNALS

    if "used_signals" not in user_sessions[uid]:
        user_sessions[uid]["used_signals"] = []
    
    available = [s for s in valid_signals if s not in user_sessions[uid]["used_signals"]]
    if not available:
        user_sessions[uid]["used_signals"] = [s for s in user_sessions[uid]["used_signals"] if s not in valid_signals]
        available = valid_signals
    
    selected_pattern = random.choice(available)
    user_sessions[uid]["used_signals"].append(selected_pattern)

    # Result data
    ph_now = datetime.utcnow() + timedelta(hours=8)
    v_until = (ph_now + timedelta(minutes=random.randint(30, 45))).strftime("%I:%M %p")
    fake_id = str(uuid.uuid4())[:8].upper()
    prob_val = random.uniform(96.5, 99.4)

    user_sessions[uid]["result_text"] = format_cyber_box(game_name, casino, provider, prob_val, fake_id, v_until)
    user_sessions[uid]["pattern"] = selected_pattern
    user_sessions[uid]["game"] = game_name
    user_sessions[uid]["provider"] = provider
    user_sessions[uid]["casino"] = casino
    user_sessions[uid]["encoding"] = True 
    session_id = str(uuid.uuid4())
    user_sessions[uid]["encoding_id"] = session_id

    # Initially send result box
    msg = bot.send_message(chat_id, user_sessions[uid]["result_text"], parse_mode="HTML")
    user_sessions[uid]["last_msg"] = msg.message_id
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
        types.InlineKeyboardButton("🚀 ANALYZE RNG SEED", callback_data="run_gen"),
        types.InlineKeyboardButton("🔙 BACK TO GAMES", callback_data="change_game"),
        types.InlineKeyboardButton("🔙 BACK TO PROVIDERS", callback_data="open_menu")
    )
    msg = bot.send_message(message.chat.id, f"🎯 <b>SELECTED:</b> <b>{html.escape(game_name)}</b>\nClick below to start RNG sync.", reply_markup=kb, parse_mode="HTML")
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
    try:
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        init_telemetry = (
            f"{res_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>CYBER TELEMETRY ACTIVE:</b>\n"
            f"<code>[SYS_SYNC] >> INITIATING PLATFORM HANDSHAKE...</code>"
        )
        bot.edit_message_text(
            init_telemetry, 
            chat_id, message_id, parse_mode="HTML"
        )
    except: pass
    time.sleep(1.2)

    safe_casino = html.escape(str(selected_casino))
    frames = [
        (
            f"📡 <b>LIVE TELEMETRY STREAM:</b>\n"
            f"<code>[GATEWAY] >> CONNECTED TO {safe_casino.upper()}</code>\n"
            f"<code>[LATENCY] >> 11ms · JITTER: 0.1ms</code>\n"
            f"<code>[METER]   [■■■■■■■■■■] 100% ONLINE</code>"
        ),
        (
            f"📡 <b>LIVE TELEMETRY STREAM:</b>\n"
            f"<code>[RNG_SEED]>> DYNAMIC ENTROPY STREAMING</code>\n"
            f"<code>[VOLAT]   >> SURGE COEFFICIENT: OPTIMAL (x1.42)</code>\n"
            f"<code>[STATUS]  >> PATTERN TIME-LOCKED TO SESSION</code>"
        ),
        (
            f"📡 <b>LIVE TELEMETRY STREAM:</b>\n"
            f"<code>[MONITOR] >> LIVE RTP PEAK DETECTED</code>\n"
            f"<code>[WINDOW]  >> VALIDATION RUNNING · DO NOT REFRESH</code>\n"
            f"<code>[SIGNAL]  >> READY FOR EXECUTION</code>"
        )
    ]
    
    for frame in frames:
        if uid not in user_sessions or user_sessions[uid].get("encoding") == False or user_sessions[uid].get("encoding_id") != session_id:
            break
        try:
            res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n{frame}",
                parse_mode="HTML"
            )
        except Exception:
            break 
        time.sleep(1.2)

    # FINAL STEP: Show Status and Buttons after animation
    if uid in user_sessions and user_sessions[uid].get("encoding_id") == session_id:
        user_sessions[uid]["encoding"] = False
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        
        inline_kb = types.InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            types.InlineKeyboardButton("👁️ REVEAL INJECTION PATTERN", callback_data="show_pattern"), 
            types.InlineKeyboardButton("🔄 RE-SYNC RNG DATA", callback_data="run_gen"), 
            types.InlineKeyboardButton("🔙 BACK TO GAMES", callback_data="change_game"),
            types.InlineKeyboardButton("🔙 BACK TO PROVIDERS", callback_data="open_menu"),
            types.InlineKeyboardButton("🔙 BACK TO CASINOS", callback_data="change_platform")
        )
        
        final_footer = (
            f"🟢 <b>STATUS:</b> <code>TELEMETRY LOCKED & SYNCED</code>\n"
            f"<code>[CORE] >> EXECUTE BEFORE EXPIRATION WINDOW</code>\n"
            f"<blockquote>💡 <i>Paalala: Mag-log in muna sa casino bago simulan ang pattern sequence.</i></blockquote>"
        )
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n{final_footer}",
                parse_mode="HTML",
                reply_markup=inline_kb
            )
        except: pass

@bot.callback_query_handler(func=lambda c: c.data == "show_pattern")
def show_pattern_callback(call):
    uid = call.from_user.id
    if uid not in user_sessions:
        bot.answer_callback_query(call.id, "⚠️ Session expired. Please /start again.", show_alert=True)
        return
    game = user_sessions[uid].get("game", "UNKNOWN")
    casino = user_sessions[uid].get("casino", "UNKNOWN")
    pattern = user_sessions[uid].get("pattern", "No pattern available.")
    
    # Delete the previous INJECTION PATTERN VERIFIED message if it exists
    prev_pattern_id = user_sessions[uid].get("last_pattern_msg_id")
    if prev_pattern_id:
        try:
            bot.delete_message(call.message.chat.id, prev_pattern_id)
        except:
            pass
        user_sessions[uid]["last_pattern_msg_id"] = None

    safe_game = html.escape(str(game))
    safe_casino = html.escape(str(casino))
    safe_pattern = html.escape(str(pattern))
    
    alert_text = (
        f"⚜️ <b>INJECTION PATTERN VERIFIED</b> ⚜️\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎮 Game: <b>{safe_game}</b>\n"
        f"🏛 Platform: <b>{safe_casino}</b>\n\n"
        f"📋 <b>SPIN SEQUENCE:</b>\n"
        f"{safe_pattern}\n\n"
        f"⚠️ <b>Paalala:</b> Sundin nang tumpak ang injection sequence bago matapos ang expiration window."
    )
    try:
        bot.answer_callback_query(call.id, "📋 Pattern revealed below!")
    except:
        pass
    try:
        sent_pattern_msg = bot.send_message(call.message.chat.id, alert_text, parse_mode="HTML")
        if sent_pattern_msg and hasattr(sent_pattern_msg, "message_id"):
            user_sessions[uid]["last_pattern_msg_id"] = sent_pattern_msg.message_id
    except Exception as e:
        print("Error sending pattern message:", e)

# Centralized message handler to avoid conflicts and ensure new games/providers are caught
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def handle_text_messages(message):
    uid = message.from_user.id
    text = message.text.strip()
    
    # Handlers for specific navigation buttons
    if text == "🔙 BACK TO PROVIDERS":
        return back_to_providers_reply(message)
    if text == "🔙 BACK TO CASINOS":
        return back_to_casinos_handler(message)
    if text == "🔙 BACK":
        # Check if we should go to providers or casinos based on where we are
        if uid in user_sessions and user_sessions[uid].get("provider"):
            return back_to_prov(message)
        return back_to_casinos_handler(message)
    if text == "🔄 Re-Generate Pattern" or text == "🔄 Re-Sync RNG Data":
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

    # Check if text matches a Casino Name
    for cas_name in CASINO_DATA.keys():
        if cas_name.strip().upper() == text.upper() or f"🏛 {cas_name.strip().upper()}" == text.upper():
            if uid not in user_sessions:
                user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": cas_name, "is_logged_in": True}
            else:
                user_sessions[uid]["casino"] = cas_name
            return main_menu(message.chat.id, uid)

    # Fallback response for normal chat messages - provide clear user guide so bot is responsive
    save_user(uid)
    guide_caption = (
        "👋 <b>Mabuhay! Narito ang Gabay sa Paggamit ng 𝐒𝐋𝐎𝐓 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐑𝐄𝐀𝐃𝐄𝐑:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Para makakuha ng pinakabagong <b>Jackpot Signals & Injection Patterns</b>, sundin lamang ang mga simpleng hakbang na ito:\n\n"
        "1️⃣ <b>Simulan ang Bot</b> - I-type o i-click ang /start upang buksan ang Main Menu.\n"
        "2️⃣ <b>Pumili ng Platform</b> - Piliin ang Casino kung saan ka maglalaro.\n"
        "3️⃣ <b>Pumili ng Provider</b> - Piliin ang slot game provider (hal. Pragmatic Play, PG Soft, JILI, etc.).\n"
        "4️⃣ <b>Pumili ng Laro</b> - I-click ang target mong laro para sa real-time telemetry audit.\n"
        "5️⃣ <b>Kunin ang Pattern</b> - Pindutin ang <b>REVEAL INJECTION PATTERN</b> para sa eksaktong spin sequence!\n\n"
        "💡 <i>Tip: Gamitin ang mga buttons sa ibaba upang magsimula agad:</i>"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    if uid in user_sessions and user_sessions[uid].get("is_logged_in"):
        kb.add(types.InlineKeyboardButton("🚀 INITIALIZE SYSTEM", callback_data="intro_proceed"))
    else:
        kb.add(types.InlineKeyboardButton("🚀 Start JACKPOT READER", callback_data="user_login"))
    kb.add(types.InlineKeyboardButton("❓ How to use the system?", callback_data="how_to_use"))
    
    try:
        bot.send_message(message.chat.id, guide_caption, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        print(f"Error sending guide fallback message: {e}")

@bot.message_handler(commands=["top5", "top10"])
def top_games_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0
    
    if message.from_user.id != admin_id_val:
        return

    import random
    import time
    from datetime import datetime, timedelta
    num = 5 if message.text.startswith("/top5") else 10
    # Adjust to Philippine Time (UTC+8)
    now_pht = datetime.utcnow() + timedelta(hours=8)
    now_str = now_pht.strftime("%B %d, %Y ✨")
    
    header = f"<b>RECOMMENDED FOR TODAY!</b>\n({now_str})\n\n<b>PLATFORM with Exact SEED:</b>\n"
    
    casinos = list(PROVIDERS_DATA.keys())
    # Limit number of casinos to avoid long messages and satisfy user request
    limit = 4 if num == 10 else 5
    display_casinos = random.sample(casinos, min(limit, len(casinos)))

    icons = ["🔥", "💯", "💰", "👑", "💎", "⚡", "✨", "🌟", "🔥"]
    
    platform_list = "<blockquote>"
    for i, cas in enumerate(display_casinos):
        icon = icons[i % len(icons)]
        # Bold Sans Serif for "Heavy Bold"
        styled_cas = "".join([chr(ord(c) + 120211) if 'A' <= (c := c_raw.upper()) <= 'Z' else c for c_raw in cas])
        platform_list += f"{icon} <b>{styled_cas}</b>\n"
    platform_list += "</blockquote>____\n\n"
    
    # 1. Send header and platform overview
    try:
        bot.send_message(message.chat.id, header + platform_list, parse_mode="HTML")
    except Exception as e:
        print(f"Error sending header: {e}")

    # 2. Send each casino recommendations separately to guarantee under 4096 chars
    for i, cas in enumerate(display_casinos):
        icon = icons[i % len(icons)]
        styled_cas = "".join([chr(ord(c) + 120211) if 'A' <= (c := c_raw.upper()) <= 'Z' else c for c_raw in cas])
        
        cached_games = get_or_generate_top_games(cas)
        if not cached_games: continue
        
        sample_size = min(num, len(cached_games))
        selected = cached_games[:sample_size]
        
        cas_msg = f"{icon} <b>{styled_cas}</b>\n"
        cas_msg += f"🎮 Top {sample_size} Winning Games:\n"
        for idx, g_info in enumerate(selected):
            cas_msg += f"<blockquote>{idx+1}. <i><b>{g_info['name']}</b></i> — <i>{g_info['rtp']}% RTP</i>\n(<i>{g_info['provider']}</i>)</blockquote>\n"
        cas_msg += "______"
        
        try:
            bot.send_message(message.chat.id, cas_msg, parse_mode="HTML")
        except Exception as e:
            print(f"Error sending casino games: {e}")
        time.sleep(0.2)
        
    # 3. Send closing footer
    footer = "Luxury isn’t slow… it strikes.\nDon't forget to use <b>SYSTEM JACKPOT READER</b> 💯\nClick /start or Send it here to initialize system ✅\n\n#TopWinningGames #HighStakes\n\n<i>Play Responsibly ✅</i>"
    try:
        bot.send_message(message.chat.id, footer, parse_mode="HTML")
    except Exception as e:
        print(f"Error sending footer: {e}")

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
            bot.send_document(admin_id_val, f, caption=f"📂 <b>User Database Backup</b>\nTotal: {len(user_ids)}", parse_mode="HTML")
    else:
        bot.send_message(admin_id_val, "❌ <b>Backup failed:</b> <code>users.txt</code> not found.")

@bot.message_handler(commands=["restore_users"])
def restore_users_cmd(message):
    try: admin_id_val = int(ADMIN_ID) if ADMIN_ID else 0
    except: admin_id_val = 0
    if message.from_user.id != admin_id_val: return
    
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.send_message(admin_id_val, "❌ <b>Usage:</b> Reply to a <code>users.txt</code> file with <code>/restore_users</code>")
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
    bot.send_message(admin_id_val, f"✅ <b>Database restored!</b> Total users: {len(user_ids)}")


def start_bot():
    if not TOKEN or not TOKEN.strip() or TOKEN.strip() == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️ PAALALA: Walang nakalagay na valid Telegram Bot Token.")
        print("👉 Pumunta sa 'General' tab at i-paste ang iyong Bot Token mula kay @BotFather bago simulan ang bot.")
        return
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            print("🚀 BOT POLLING STARTED...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            err_msg = str(e)
            if "Unauthorized" in err_msg or "Not Found" in err_msg:
                print(f"❌ Telegram API Error: Invalid Bot Token! Pakisuri ang Token sa General tab. ({err_msg})")
                time.sleep(10)
            else:
                print(f"Bot Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    # In direct execution, start bot in background and run Flask in main thread
    t = Thread(target=start_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get('PORT', 10000))
    print(f"📡 SERVER STARTING ON PORT {port}...")
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"⚠️ Web server notice ({e}). Continuing bot polling...")
        while True:
            time.sleep(1)
else:
    # If imported (e.g. by gunicorn), start bot in background
    t = Thread(target=start_bot)
    t.daemon = True
    t.start()
