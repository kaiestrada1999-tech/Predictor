import telebot
import random
import time
import os
import threading
import uuid
import logging
from datetime import datetime, timedelta
from telebot import types
from telebot import apihelper
from flask import Flask
from threading import Thread

# Enable robust connection handling
apihelper.RETRY_ON_ERROR = True
logging.basicConfig(level=logging.INFO)

# ================= KEEP-ALIVE PARA SA RENDER =================
app = Flask('')

@app.route('/')
def home():
    return "BOT IS ALIVE"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ================= CONFIG =================
TOKEN = "8531407840:AAGHkEocBiac-znOGM_m0kgaEh1gK5OXbOU"
ADMIN_ID = 8454741864 

# URL ng Image para sa Intro
INTRO_IMAGE_URL = "https://i.imghippo.com/files/jFEp1747BHI.png" 

# ================= TURSO DB CONFIG =================
TURSO_URL = "libsql://slot-predictor-bosslapagan-droid.aws-ap-northeast-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzY2NDQ1NDUsImlkIjoiMDE5ZGE4NDQtMzQwMS03Zjc3LTg0YmEtNDQxODgwMjhmNGRhIiwicmlkIjoiMzAyNjUwYTAtZjIzNy00NTQyLWJhYjMtZTFkYjNhZTA3YWI2In0.tlEA-IDHNjaC9wjmuWB0HXysEI5DNgoifMoarzVFEX7rSw7myHvZ1zoz2L5OWaqPDzGk4g0aOevyjNPz_91bCw"

# ================= CASINO LINKS DATABASE =================
CASINO_DATA = {
    "AGILA CLUB": "https://t.me/Helpslotwinbot/agilaclub",
    "INFERNO PLAY": "https://t.me/Helpslotwinbot/infernoplay",
    "BUGATTI PLAY": "https://t.me/Helpslotwinbot/bugattiplay",
    "MASERATI PLAY": "https://t.me/Helpslotwinbot/maseratiplay",
    "LOTUSPLAY": "https://t.me/Helpslotwinbot/lotusplay",
    "FORTUNE PLAY ": "https://t.me/Helpslotwinbot/fortuneplay",
    "BIGBALLER CLUB ": "https://t.me/Helpslotwinbot/bigballerclub",
    "QUANTUM BBC ": "https://t.me/Helpslotwinbot/quantumbbc"
}

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=100)

user_sessions = {}
# ================= TURSO CONFIGURATION =================
import urllib.request
import json

def exec_turso(query, args=None):
    if not TURSO_URL or not TURSO_TOKEN:
        return None
    url = TURSO_URL.replace("libsql://", "https://")
    if not url.endswith("/v2/pipeline"):
        url = url + "/v2/pipeline"
    
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    }
    
    q_dict = {"stmt": query}
    if args:
        q_dict["args"] = [{"type": "text", "value": str(arg)} for arg in args]
        
    data = {
        "requests": [
            {"type": "execute", "stmt": q_dict},
            {"type": "close"}
        ]
    }
    
    try:
        req = urllib.request.Request(url, json.dumps(data).encode('utf-8'), headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("results", [{}])[0].get("response", {}).get("result", {})
    except Exception as e:
        print(f"Turso Error: {e}")
        return None

def init_db():
    exec_turso("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY)")

init_db()

def get_all_users():
    res = exec_turso("SELECT id FROM users")
    if not res: return set()
    rows = res.get("rows", [])
    return {int(r[0].get("value")) for r in rows if r and r[0].get("value")}

def add_user_db(uid):
    exec_turso("INSERT OR IGNORE INTO users (id) VALUES (?)", [str(uid)])

user_ids = get_all_users()

# ================= DATA: EXPANDED GAME LIST =================
PROVIDERS_DATA = {
    "PRAGMATIC PLAY": [
        "GATES OF OLYMPUS", "GATES OF OLYMPUS 1000", "SWEET BONANZA", "SWEET BONANZA 1000", "SUGAR RUSH", "SUGAR RUSH 1000", "STARLIGHT PRINCESS", "STARLIGHT PRINCESS 1000", "BIG BASS BONANZA", "BIG BASS SPLASH", "BIG BASS AMAZON XTREME", "BIG BASS FLOATS MY BOAT", "THE DOG HOUSE", "THE DOG HOUSE MEGAWAYS", "THE DOG HOUSE MULTIHOLD", "FRUIT PARTY", "FRUIT PARTY 2", "WOLF GOLD", "MUSTANG GOLD", "GREAT RHINO MEGAWAYS", "JOHN HUNTER & THE TOMB", "CHILLI HEAT", "AZTEC GEMS", "AZTEC GEMS DELUXE", "WILD WEST GOLD", "MADAME DESTINY MEGAWAYS", "THE HAND OF MIDAS", "POWER OF THOR MEGAWAYS", "BUFFALO KING", "BUFFALO KING MEGAWAYS", "JUICY FRUITS", "GEMS BONANZA", "RISE OF GIZA", "CHICKEN DROP", "BOOK OF FALLEN", "MAGICIAN'S SECRETS", "CRYSTAL CAVERNS", "SMUGGLERS COVE", "CHRISTMAS BIG BASS BONANZA", "SANTA'S WONDERLAND", "STAR PIRATES CODE", "MYSTIC CHIEF", "PIGGY BANK BILLS", "TREASURE WILD", "GATES OF GATOT KACA", "MOCKTAIL NIGHTS", "SWORD OF ARES", "SHIELD OF SPARTA", "TOWERING FORTUNES", "RELEASE THE KRAKEN 2", "SPIN & SCORE", "OLD GOLD MINER", "CANDY STARS", "BIG BASS KEEP IT REEL", "CLEOCATRA", "WILD BEACH PARTY", "QUEEN OF GODS", "ZOMBIE CARNIVAL", "FORTUNE OF GIZA", "SPIRIT OF ADVENTURE", "CLOVER GOLD", "EYE OF CLEOPATRA", "NORTH GUARDIANS", "DRILL THAT GOLD", "BARN FESTIVAL", "RAINBOW GOLD", "TIC TAC TAKE", "WILD DEPTHS", "GOLD PARTY", "ROCK VEGAS", "EMPEROR CAISHEN", "LUCKY LIGHTNING", "DRAGON HOT HOLD & SPIN", "HEART OF RIO", "PANDA'S FORTUNE 2", "5 LIONS MEGAWAYS", "BOOK OF VIKINGS", "LUCKY GRACE AND CHARM", "RISE OF SAMURAI MEGAWAYS", "CHICKEN CHASE", "WILD WEST DUELS", "MYSTERY OF THE ORIENT", "PEAK POWER", "CLUB TROPICANA", "THE KNIGHT KING", "GODS OF GIZA", "KINGDOM OF THE DEAD", "EXCALIBUR UNLEASHED", "JANE HUNTER", "ZEUS VS HADES", "JEWEL RUSH", "STICKY BEES", "PIRATES PUB", "FLOATING DRAGON", "FLOATING DRAGON MEGAWAYS", "TRIPLE TIGERS", "888 DRAGONS", "MONKEY MADNESS", "MASTER JOKER", "FIRE STRIKE", "FIRE STRIKE 2", "DIAMOND STRIKE", "EXTRA JUICY", "EXTRA JUICY MEGAWAYS", "WILD WILD RICHES", "WILD WILD RICHES MEGAWAYS", "PYRAMID KING", "HOT TO BURN", "HOT TO BURN EXTREME", "ULTRA HOLD AND SPIN", "LUCKY, GRACE & CHARM", "EMPTY THE BANK", "FLOATING DRAGON", "BOOK OF KING ARTHUR", "7 PIGGIES", "888 GOLD", "ALADDIN AND THE SORCERER", "AMAZING MONEY MACHINE", "ANCIENT EGYPT CLASSIC", "BEOWULF", "BOOK OF TUT", "BRONCO SPIRIT", "CASH BONANZA", "CASH ELEVATOR", "CONGO CASH", "COWBOYS GOLD", "CURSE OF THE WEREWOLF", "DA VINCI'S TREASURE", "DANCE PARTY", "DAY OF DEAD", "DIAMOND ARE FOREVER", "DRAGON KINGDOM", "DRAGON TIGER", "DWARF MINE", "EMERALD KING", "EMERALD KING JACKPOT", "FAIRYTALE FORTUNE", "FISHIN' REELS", "FORBIDDEN THRONE", "GATES OF VALHALLA", "GLOOMY GRAVEYARD", "GOLD RUSH", "GOLD TRAIN", "GOLDEN BEAUTY", "GOLDEN OX", "GREAT RHINO", "GREAT RHINO DELUXE", "HERCULES AND PEGASUS", "HOT SAFARI", "JADE BUTTERFLY", "JOKER KING", "JOKER'S JEWELS", "JOURNEY TO THE WEST", "JUNGLE GORILLA", "KNIGHT HOT SPOTZ", "LEPRECHAUN CAROL", "LEPRECHAUN SONG", "LUCKY DRAGONS", "LUCKY NEW YEAR", "MASTER CHEN'S FORTUNE", "MEDUSA STRIKE", "MONEY MOUSE", "MONKEY WARRIOR", "MOON PRINCESS", "MYSTERIOUS", "MYSTERIOUS EGYPT", "PANDA'S FORTUNE", "PEKING LUCK", "PHOENIX FORGE", "PIXIE WINGS", "PYRAMID KING", "QUEEN OF ATLANTIS", "QUEEN OF GOLD", "RELEASE THE KRAKEN", "RETRO REELS", "SANTA", "SCARAB QUEEN", "SEVEN PIGGIES", "STAR BOUNTY", "STREET RACER", "SUPER JOKER", "TEMPLAR TUMBLE", "THE CHAMPIONS", "THE DOG HOUSE", "THE WILD MACHINE", "THREE STAR FORTUNE", "TREE OF RICHES", "TRIPLE DRAGONS", "TRIPLE JOKER", "VAMPIRE VS WOLVES", "VEGAS MAGIC", "VEGAS NIGHTS", "VOODOO MAGIC", "WILD GLADIATORS", "WILD PIXIES", "WILD SPELLS", "WILD WALKER", "WOLF GOLD", "WISDOM OF ATHENA", "WISDOM OF ATHENA 1000", "FORGE OF OLYMPUS", "GATES OF GATOT KACA 1000", "BIG BASS MISSION FISHIN'", "BIG BASS SECRETS OF THE STYX", "REVENGE OF LOKI MEGAWAYS", "BUFFALO KING UNTAMED MEGAWAYS", "HAND OF MIDAS 2", "VAMPY PARTY", "MUSTANG GOLD MEGAWAYS", "WOLF GOLD ULTIMATE", "JOKER'S JEWELS WILD", "FORGING FORTUNE", "6 JOKERS", "DYNAMITE DIGGIN DOUG", "THE DOG HOUSE - DOG OR ALIVE", "RELEASE THE KRAKEN MEGAWAYS", "CANDY BLITZ BOMBS", "BOW OF ARTEMIS", "HIGH FLYER", "SUMO SUPREME MEGAWAYS", "MONEY STACKS", "CRANK IT UP", "RUNNING SUSHI", "SWEET KINGDOM", "BIG BASS VEGAS DOUBLE DOWN DELUXE", "CHEST OF FORTUNES", "HEART OF CLEO", "MEDUSA'S STONE", "BIG BASS DAY AT THE RACES", "BIG BASS HALLOWEEN", "FIRE PORTALS", "BARN YARD MEGAHAYS MEGAWAYS", "SUPER MANIA", "SUPER X", "SUPER 7S", "GEARS OF HORUS", "ZEUS VS HADES - GODS OF WAR", "POMPEII MEGAREELS MEGAWAYS", "JOKER'S Jewels", "THREE STAR Fortune"
    ],
    "PG SOFT": [
        "MAHJONG WAYS", "MAHJONG WAYS 2", "LUCKY NEKO", "TREASURES OF AZTEC", "FORTUNE OX", "FORTUNE MOUSE", "FORTUNE TIGER", "FORTUNE RABBIT", "FORTUNE DRAGON", "DRAGON HATCH", "DRAGON HATCH 2", "GATES OF GATOT KACA", "CAISHEN WINS", "GANESHA GOLD", "WILD BANDITO", "WAYS OF THE QILIN", "DREAMS OF MACAU", "SUPERMARKET SPREE", "ROYAL KATT", "CANDY BONANZA", "HEIST STAKES", "RISE OF APOLLO", "MERMAID RICHES", "CRYPTO GOLD", "BALI VACATION", "OPERA DYNASTY", "GUARDIANS OF ICE & FIRE", "JACK FROST'S WINTER", "GALACTIC GEMS", "JEWELS OF PROSPERITY", "QUEEN OF BOUNTY", "VAMPIRE'S CHARM", "SECRET OF CLEOPATRA", "GENIE'S 3 WISHES", "CIRCUS DELIGHT", "DRAGON TIGER LUCK", "PHOENIX RISES", "WILD FIREWORKS", "EGYPT'S BOOK OF MYSTERY", "CAPTAIN'S BOUNTY", "JOURNEY TO THE WEALTH", "GEM SAVIOUR", "GEM SAVIOUR SWORD", "PIGGY GOLD", "JUNGLE DELIGHT", "THREE MONKEYS", "EMPEROR'S FAVOUR", "MUAY THAI CHAMPION", "THE GREAT ICESCAPE", "LEPRECHAUN RICHES", "FLIRTING SCHOLAR", "NINJA VS SAMURAI", "DRAGON LEGEND", "SANTA'S GIFT RUSH", "BATTLEGROUND ROYALE", "ROOSTER RUMBLE", "BUTTERFLY BLOSSOM", "LUCKY PIGGY", "PROSPERITY FORTUNE TREE", "TOTEM WONDERS", "ALCHEMY GOLD", "MIDAS FORTUNE", "BAKERY BONANZA", "RAVE PARTY FEVER", "LUXURY GOODS", "MYSTICAL SPIRITS", "ULTIMATE STRIKER", "PINATA WINS", "SAFARI WILDS", "WEREWOLF'S HUNT", "GLADIATOR'S GLORY", "CRUISE ROYALE", "THREE PIGLETS", "SONGKRAN SPLASH", "HAWAIIAN TIKI", "SPIRITED WONDERS", "LEGEND OF PERSEUS", "WIN WIN FISH PRAWN CRAB", "ORIENTAL PROSPERITY", "MASK CARNIVAL", "EMOJI RICHES", "FARM INVADERS", "DESTINY OF SUN & MOON", "MAJESTIC TREASURES", "CANDY BURST", "ASGARDIA", "BIKINI PARADISE", "DOUBLE FORTUNE", "DRAGON TIGER LUCK", "GEM SAVIOUR CONQUEST", "HOOD VS WOLF", "HOTPOT", "ICE SCAPE", "LEGEND OF HOU YI", "MEDUSA II", "MEDUSA", "MR. HALLOW-WIN", "PLUSHIE FRENZY", "PROSPERITY LION", "REEL LOVE", "SANTA'S GIFT RUSH", "SHAOLIN SOCCER", "STEAMPUNK FORTUNE", "SYMBOLS OF EGYPT", "THE GREAT ICESCAPE", "TREE OF FORTUNE", "WILD FIREWORKS", "WIN WIN WON", "MYSTIC POTION", "YAKUZA HONOR", "FUTEBOL FEVER", "MAFIA MAYHEM", "FORGE OF WEALTH", "CASH MANIA", "WILD BOUNTY SHOWDOWN", "ASGARDIAN RISING", "DINER DELIGHTS", "WILD COASTER", "SPEED WINNER", "GARUDA GEMS", "THE QUEEN'S BANQUET", "COCKTAIL NIGHTS", "BUFFALO WIN", "ANUBIS WRATH", "WINGS OF IGUAZU", "CHICKEN VICKEN", "OISHI DELIGHT", "WILD APE #3258", "SHARK BOUNTY", "ZOMBIE OUTBREAK"
    ],
    "JILI": [
        "SUPER ACE", "SUPER ACE DELUXE", "GOLDEN EMPIRE", "GOLDEN EMPIRE 2", "FORTUNE GEMS", "FORTUNE GEMS 2", "FORTUNE GEMS 3", "MONEY COMING", "MONEY COMING EXPAND", "BOXING KING", "ALI BABA", "MEGA ACE", "MAGIC LAMP", "TWIN WINS", "FENG SHEN", "ROMA X", "ROMA X DELUXE", "DRAGON TREASURE", "CRAZY 777", "GOLDEN QUEEN", "JUNGLE KING", "CHARGE BUFFALO", "CHARGE BUFFALO 2", "PHARAOH TREASURE", "BUBBLE BEAUTY", "CANDY BABY", "NIGHT CITY", "SUPER RICH", "HAPPY TAXI", "WORLD CUP", "MAYAN EMPIRE", "CHIN SHI HUANG", "GOLDEN BANK", "LUCKY GOLDBRICKS", "HYPER BURST", "PARTY NIGHT", "SEVEN SEVEN SEVEN", "WAR OF DRAGONS", "AGENT ACE", "HOT CHILLI", "MEDUSA", "CRAZY HUNTER", "SECRET TREASURE", "TRIAL OF ADVERSITY", "WILD PANDA", "BOOK OF GOLD", "GOD OF MARTIAL", "SAMURAI", "WILD RACER", "GOLDEN LAND", "LUCKY LADY", "SUPER JOKER", "CRAZY FA FA FA", "DRAGON & TIGER", "KA CHIN", "LUCKY DIAMOND", "WORLD CUP 2022", "GOLDEN JOKER", "CRAZY PUSHER", "BONUS HUNTER", "JILI CAISHEN", "BOOK OF MYSTERY", "PIRATE QUEEN", "MONEY TREE", "TREASURE BOWL", "WILD FOX", "CRAZY GOLDEN BANK", "SUPER NIUBI", "777", "ACE OF SPADES", "BAO BOON CHIN", "BOXING KING", "CANDY BABY", "CHARGE BUFFALO", "CRAZY 777", "CRAZY HUNTER", "DRAGON TREASURE", "FENG SHEN", "FORTUNE GEMS", "FORTUNE TREE", "GOLDEN EMPIRE", "GOLDEN QUEEN", "HOT CHILLI", "JUNGLE KING", "LUCKY GOLDBRICKS", "MAGIC LAMP", "MEGA ACE", "MONEY COMING", "NIGHT CITY", "PARTY NIGHT", "PHARAOH TREASURE", "ROMA X", "SEVEN SEVEN SEVEN", "SUPER ACE", "SUPER RICH", "TWIN WINS", "WAR OF DRAGONS", "WORLD CUP", "SAMBA", "BONE FORTUNE", "CHARGE BUFFALO-ASCENT", "DINOSAUR TYCOON", "DINOSAUR TYCOON II", "BOMBING FISHING", "JACKPOT FISHING", "ROYAL FISHING", "MEGA FISHING", "BOOM LEGEND", "DRAGON FORTUNE", "HAPPY FISHING", "ALL-STAR FISHING", "JACKPOT JOKER", "WILD ACE", "CASH IT"
    ],
    "NOLIMIT CITY": [
        "SAN QUENTIN XWAYS", "MENTAL", "FIRE IN THE HOLE", "DAS XBOOT", "XWAYS HOARDER", "EAST COAST VS WEST COAST", "PUNK ROCKER", "DEADWOOD", "TOMBSTONE", "TOMBSTONE RIP", "EL PASO GUNFIGHT", "BUSHIDO WAYS", "INFECTIOUS 5", "WARRIOR GRAVEYARD", "BARBARIAN FURY", "DRAGON TRIBE", "GAELIC GOLD", "HARLEQUIN CARNIVAL", "ICE ICE YETI", "KITCHEN DRAMA", "MANHATTAN GOES WILD", "MAYA MAGIC", "MILKY WAYS", "MONKEY'S GOLD", "OWLS", "PIXIES VS PIRATES", "POISON EVE", "STARSTRUCK", "TESLA JOLT", "THE CREEPY CARNIVAL", "THOR", "TRACTOR BEAM", "TURST YOURSELF", "WIXX", "HOT 4 CASH", "IMMORTAL FRUITS", "BOOK OF SHADOWS", "BUFFALO HUNTER", "GOLDEN GENIE", "TOMB OF NEFERTITI", "TOMB OF AKHENATEN", "FOXY WILD HEART", "EVIL GOBLINS", "LEGION X", "TRUE GRIT REDEMPTION", "MISERY MINING", "REMEMBER GULAG", "KAREN MANEATER", "THE RAVE", "ROAD RAGE", "UGLIEST CATCH", "NINE TO FIVE", "DEVIL'S CROSSROAD", "D-DAY", "POSSESSED", "KENNY'S BEST", "LAND OF THE FREE", "BRICK SNAKE 2000", "FIRE IN THE HOLE 2", "WHACKED!", "BLOOD & SHADOW", "DISTURBED", "KISS MY CHAINS", "BENJI KILLED IN VEGAS", "WALK OF SHAME", "THE CAGE", "GLUTTONY", "THE CRYPT", "BOUNTY HUNTERS", "DJ PSYCHO", "SERIAL", "PEARL HARBOR", "DEAD CANARY", "FOLSOM PRISON", "THE SHADOW ORDER", "WOLF RITUAL", "DRAGON TRIBE", "MANHATTAN GOES WILD", "MAYA MAGIC", "POISON EVE", "SAN QUENTIN 2: DEATH ROW", "DEADWOOD RIP", "BLOOD & SHADOW 2", "PUNK ROCKER 2", "STOCKHOLM SYNDROME", "BEHEADED", "KENNETH MUST DIE", "JINGLE BALLS", "SPACE DONKEY", "LURE OF FORTUNE"
    ],
    "MICROGAMING": [
        "MEGA MOOLAH", "IMMORTAL ROMANCE", "THUNDERSTRUCK II", "9 MASKS OF FIRE", "BREAK DA BANK AGAIN", "JURASSIC PARK", "GAME OF THRONES", "AVALON II", "BOOK OF OZ", "WHEEL OF WISHES", "ADVENTURE PALACE", "AGENT JANE BLONDE", "ALASKAN FISHING", "ARIANA", "BASS BOSS", "BIG BAD WOLF", "BUST THE BANK", "CARNAVAL", "COOL BUCK", "DECK THE HALLS", "DRAGONZ", "EAGLE'S WINGS", "EMPEROR OF THE SEA", "FISH PARTY", "FOOTBALL STAR", "FORBIDDEN THRONE", "FORTUNIUM", "GIRLS WITH GUNS", "GOLD FACTORY", "HALLOWEEN", "HAPPY HOLIDAYS", "HELLBOY", "HIGHLANDER", "HITMAN", "HOT INK", "JUNGLE JIM EL DORADO", "KATHMANDU", "KINGS OF CASH", "LADIES NITE", "LARA CROFT", "LOADED", "LOST VEGAS", "LUCKY KOI", "LUCKY LEPRECHAUN", "LUCKY ZODIAC", "MERMAIDS MILLIONS", "PLAYBOY", "PRETTY KITTY", "PURE PLATINUM", "RETRO REELS", "TERMINATOR 2", "TOMB RAIDER", "TREASURE NILE", "WAXY VAN GOGH", "WICKED TALES", "WILD SCARABS", "WOLF HOWL", "AMAZING LINK ZEUS", "ANCIENT FORTUNES: ZEUS", "ASSASSIN MOON", "AURUM CODEX", "BANANA ODYSSEY", "BATTLE ROYAL", "BEAUTIFUL BONES", "BIG KAHUNA", "5 REEL DRIVE", "777 ROYAL WHEEL", "A DARK MATTER", "ABSALOOTLY MAD", "AFRICAN QUEST", "AGE OF CONQUEST", "ALCHEMISTS GOLD", "ALL WIN FC", "AMAZING LINK APOLLO", "ANCIENT FORTUNES: POSEIDON", "ARENA OF GOLD", "ARTHUR'S FORTUNE", "ATLANTIS RISING", "AURORA WILD", "AZTEC FALLS", "BAR BAR BLACK SHEEP", "BEACH BABES", "BELIEVE IT OR NOT", "BIG TOP", "BOOK OF ATEM", "BOOK OF CAPTAIN SILVER", "BOOK OF KING ARTHUR", "BOOM PIRATES", "BREAK AWAY", "BREAK AWAY LUCKY WILDS", "BULLSEYE", "BURNING DESIRE", "BUSH TELEGRAPH", "CASH OF KINGDOMS", "CASH SPLASH", "CASHVILLE", "CAT IN VEGAS", "CELEBRATION OF WEALTH", "CENTURION", "CHICAGO GOLD"
    ],
    "BNG (BOOONGO)": [
        "SUN OF EGYPT", "SUN OF EGYPT 2", "SUN OF EGYPT 3", "SUN OF EGYPT 4", "15 DRAGON PEARLS", "DRAGON PEARLS", "MAGIC APPLE", "MAGIC APPLE 2", "TIGER JUNGLE", "HIT THE GOLD", "BLACK WOLF", "BLACK WOLF 2", "AZTEC SUN", "GREAT PANDA", "MOON SISTERS", "BUDDHA FORTUNE", "SCARAB TEMPLE", "3 COINS", "3 COINS EGYPT", "3 HOT CHILLIES", "WUKONG", "WOLF SAGA", "PEARL DIVER", "PEARL DIVER 2", "QUEEN OF THE SUN", "GOLD EXPRESS", "CANDY BOOM", "GIE GIE GIE", "HAPPY FISH", "LOTUS CHARM", "ORCHID PRINCESS", "TIGER STONE", "SUPER RICH GOD", "EYE OF GOLD", "BOOK OF SUN", "BOOK OF SUN MULTICHANCE", "GOD'S TEMPLE", "OLYMPIAN GODS", "POISONED APPLE", "POISONED APPLE 2", "777 GEMS", "SUPREME HOT", "STAR GEMS", "SKY GEMS", "GREEN CHILLI", "GREEN CHILLI 2", "MORE MAGIC APPLE", "OIAO MEI", "COIN VOLCANO", "EGYPT FIRE", "RIO GEMS", "HIT MORE GOLD", "STICKY PIGGY", "GODDESS OF EGYPT", "BOOM! BOOM! GOLD!", "AZTEC SUN", "BOOK OF SUN", "BUDDHA FORTUNE", "DRAGON PEARLS", "EYE OF GOLD", "GOD'S TEMPLE", "GREAT PANDA", "MAGIC APPLE", "MOON SISTERS", "OLYMPIAN GODS", "POISONED APPLE", "SCARAB TEMPLE", "SUN OF EGYPT", "TIGER STONE", "WOLF SAGA"
    ],
    "BIGPOT GAMING": [
        "CRAZY HUNTER", "GOLDEN ERA", "SECRET OF RICHES", "LUCKY SEVEN", "WILD WEST SALOON", "PIRATE KING", "DRAGON LEGEND", "MAGIC FOREST", "CANDY POP", "NEON CITY", "ANCIENT TREASURES", "SAMURAI'S HONOR", "VIKING GLORY", "PHARAOH'S CURSE", "MYSTIC MOON", "JUNGLE ADVENTURE", "SPACE ODYSSEY", "OCEAN'S BOUNTY", "ALADDIN'S WISH", "HERCULES", "ZOMBIE ATTACK", "HALLOWEEN NIGHT", "CHRISTMAS JOY", "LUCKY FARM", "CASINO ROYALE", "NINJA SQUAD", "ROBOT WARS", "FANTASY WORLD", "DRAGON SLAYER", "KUNG FU MASTER", "FOOTBALL FEVER", "RACING STARS", "FISHING MASTER", "FRUIT SPLASH", "DIAMOND RUSH", "PANDA WARRIOR", "SKY GUARDIAN", "DEEP SEA", "TREASURE ISLAND", "WILD SAFARI", "MAGIC SPELL", "LUCKY DICE", "GOLDEN RUSH", "ALADDIN'S WISH", "ANCIENT TREASURES", "CANDY POP", "CASINO ROYALE", "CRAZY HUNTER", "DRAGON LEGEND", "DRAGON SLAYER", "FANTASY WORLD", "FOOTBALL FEVER", "FRUIT SPLASH", "GOLDEN ERA", "GOLDEN RUSH", "HALLOWEEN NIGHT", "HERCULES", "JUNGLE ADVENTURE", "KUNG FU MASTER", "LUCKY FARM", "LUCKY SEVEN", "MAGIC FOREST", "MAGIC SPELL", "MYSTIC MOON", "NEON CITY", "NINJA SQUAD", "OCEAN'S BOUNTY", "PHARAOH'S CURSE", "PIRATE KING", "RACING STARS", "ROBOT WARS", "SAMURAI'S HONOR", "SECRET OF RICHES", "SPACE ODYSSEY", "TREASURE ISLAND", "VIKING GLORY", "WILD SAFARI", "WILD WEST SALOON"
    ],
    "HACKSAW GAMING": [
        "WANTED DEAD OR A WILD", "CHAOS CREW", "CHAOS CREW II", "HAND OF ANUBIS", "RIP CITY", "LE BANDIT", "DORK UNIT", "STACK 'EM", "STICK 'EM", "TOSHI VIDEO CLUB", "DROP 'EM", "ROTTEN", "GLADIATOR LEGENDS", "STORMFORGED", "THE BOWERY BOYS", "PUG LIFE", "ITERCH", "KING CARROT", "JOKER BOMBS", "CUBES", "CUBES 2", "DOUBLE RAINBOW", "TASTY TREATS", "XPW", "UNDEA FORTUNE", "FEAR THE DARK", "BEAST BELOW", "SLAYERS INC", "DARK SUMMONING", "BENNY THE BEER", "2 WILD 2 DIE", "FEEL THE BEAT", "FIST OF DESTRUCTION", "DIVINE DROP", "RUSTY & CURLY", "CASH CREW", "BEAM BOYS", "BARBARIAN STASH", "JAGGED STONES", "SIXSIXSIX", "OMICRON", "HOP'N'POP", "FRUIT DUEL", "BORN WILD", "FOREST FORTUNE", "HARVEST WILD", "AZTEC TWIST", "MYSTERY MOTEL", "SCRATCH BRONZE", "SCRATCH PLATINUM", "ALPHA EAGLE", "BLOODTHIRST", "BREAK BONES", "CASH QUEST", "CASH-A-CABANA", "CAT CLANS", "DORK UNIT", "DOUBLE RAINBOW", "EGGSTRAVAGANZA", "EYE OF THE PANDA", "FRUIT DUEL", "GLADIATOR LEGENDS", "HAND OF ANUBIS", "HARVEST WILD", "HOP'N'POP", "ITERERO", "JELLY REELS", "KING CARROT", "POCKET ROCKETS", "PUG LIFE", "RIP CITY", "ROTTEN", "STACK 'EM", "STICK 'EM", "TOSHI VIDEO CLUB", "WANTED DEAD OR A WILD", "WARRIOR WAYS", "WILD YIELD", "XPW", "LE PHARAOH", "ZEUS SMASH", "CURSED CRYPT", "KEEP 'EM", "BOUNCY BOMBS", "DAWN OF KINGS", "DENSHO", "VENDING MACHINE", "FRED'S FOOD TRUCK", "MIGHTY MASKS", "MAYAN STACKWAYS", "MAGIC PIGGY", "FRANK'S FARM", "ITERO", "XPANDER", "UNDEAD FORTUNE"
    ],
    "FA CHAI": [
        "CHINESE NEW YEAR", "CHINESE NEW YEAR 2", "NIGHT MARKET", "GOLDEN GENIE", "THREE LITTLE PIGS", "DA LE MEN", "MAGIC BEANS", "WIN WIN NEKO", "FORTUNE KOI", "PANDA DRAGON BOAT", "MONEY TREE DOZER", "COIN MANIAC", "STAR HUNTER", "BAO BOON CHIN", "WILD BUFFALO", "GOLDEN PANTHER", "CRAZY CIRCUS", "ANIMAL RACING", "HALLOWEEN BOOM", "LEGEND OF DRAGON", "PHOENIX ADVENTURE", "LUCKY FORTUNES", "GRAND BLUE", "TREASURE CRUISE", "GLORY OF ROME", "MERMAID LEGEND", "RICH MAN", "LUCKY CLOVER", "HOT POT PARTY", "GOLDEN DRAGON", "KA-CHING", "PONG PONG HU", "MAHJONG WAYS 3", "FORTUNE GOD", "LUCKY WHEEL", "DISCO NIGHT", "CANDY PARTY", "JUNGLE PARTY", "CIRCUS DOZER", "LIGHTNING BOMB", "FIERCE BATTLE", "SQUID PARTY", "ANIMAL RACING", "BAO BOON CHIN", "CHINESE NEW YEAR", "COIN MANIAC", "CRAZY CIRCUS", "DA LE MEN", "FORTUNE KOI", "GOLDEN GENIE", "GOLDEN PANTHER", "GRAND BLUE", "HALLOWEEN BOOM", "HOT POT PARTY", "LEGEND OF DRAGON", "LUCKY CLOVER", "LUCKY FORTUNES", "MAGIC BEANS", "MERMAID LEGEND", "MONEY TREE DOZER", "NIGHT MARKET", "PANDA DRAGON BOAT", "PHOENIX ADVENTURE", "RICH MAN", "STAR HUNTER", "THREE LITTLE PIGS", "TREASURE CRUISE", "WILD BUFFALO", "WIN WIN NEKO"
    ],
    "JDB GAMING": [
        "BURGER SHOP", "KONGFU", "BIRDS AND ANIMALS", "LUCKY 7", "CRYSTAL REALM", "ORIENTAL BEAUTY", "DRAGON MASTER", "BLOSSOM OF WEALTH", "KINGSMAN", "NINJA RUSH", "LUCKY RACING", "TRIPLE KING KONG", "FORMOSA BEAR", "WINNING MASK", "GOAL", "BILLIONAIRE", "MONEY BAGS MAN", "LUCKY QILIN", "OPEN SESAME", "LUCKY DRAGON", "SUPER NIUBI", "FLIRTING SCHOLAR TANG", "MAHJONG", "BANANA SAGA", "STREET FIGHTER", "SHADE DRAGONS", "DRAGON WARRIOR", "LUCKY DIAMOND", "COFFEE TYCOON", "ZODIAC", "TREASURE BOWL", "WILD WEST", "EGYPT TREASURE", "FUNKY KING", "CRAZY SCIENTIST", "PIRATE TREASURE", "MAGIC WORLD", "WONDERLAND", "HALLOWEEN PARTY", "CHRISTMAS SURPRISE", "BILLIONAIRE", "BIRDS AND ANIMALS", "BLOSSOM OF WEALTH", "BURGER SHOP", "COFFEE TYCOON", "CRYSTAL REALM", "DRAGON MASTER", "DRAGON WARRIOR", "EGYPT TREASURE", "FLIRTING SCHOLAR TANG", "FORMOSA BEAR", "FUNKY KING", "GOAL", "KONGFU", "LUCKY 7", "LUCKY DIAMOND", "LUCKY DRAGON", "LUCKY QILIN", "LUCKY RACING", "MAHJONG", "MONEY BAGS MAN", "NINJA RUSH", "OPEN SESAME", "ORIENTAL BEAUTY", "PIRATE TREASURE", "SHADE DRAGONS", "STREET FIGHTER", "SUPER NIUBI", "TREASURE BOWL", "TRIPLE KING KONG", "WINNING MASK", "ZODIAC"
    ],
    "PLAY'N GO": [
        "BOOK OF DEAD", "REACTOONZ", "REACTOONZ 2", "MOON PRINCESS", "MOON PRINCESS 100", "MOON PRINCESS TRINITY", "RISE OF OLYMPUS", "RISE OF OLYMPUS 100", "GEMIX", "GEMIX 2", "FIRE JOKER", "LEGACY OF DEAD", "TOME OF MADNESS", "HONEY RUSH", "HONEY RUSH 100", "GOLDEN TICKET", "GOLDEN TICKET 2", "SWEET ALCHEMY", "SWEET ALCHEMY 2", "RISE OF MERLIN", "PIMPED", "XMAS JOKER", "MYSTERY JOKER", "BIG WIN CAT", "HOT TO BURN", "BOAT BONANZA", "CLASH OF CAMELOT", "COUNT JOKULA", "DIO KILLING THE DRAGON", "CHAMPS-ELYSEES", "CANINE CARNAGE", "USA FLIP", "SHAMROCK MINER", "WILD FALLS 2", "GRIM THE SPLITTER", "LEGACY OF INCA", "GAME OF GLADIATORS", "SAFARI OF WEALTH", "CAT WILDE", "RICH WILDE", "AGENT DESTINY", "ANCIENT EGYPT", "ANNIHILATOR", "AZTEC IDOLS", "AZTEC WARRIOR PRINCESS", "BAKER'S TREAT", "BATTLE ROYAL", "7 SINS", "ACE OF SPADES", "AGENT DESTINY", "ANCIENT EGYPT", "ANNIHILATOR", "AZTEC IDOLS", "AZTEC WARRIOR PRINCESS", "BAKER'S TREAT", "BATTLE ROYAL", "BEAST OF WEALTH", "BELL OF FORTUNE", "BIG WIN 777", "BIG WIN CAT", "BLACK MAMBA", "BLAZIN' BULLFROG", "BOOK OF DEAD", "BULL IN A CHINA SHOP", "CASH PUMP", "CASH VANDAL", "CAT WILDE", "CELEBRATION OF WEALTH", "CHAMPS-ELYSEES", "CHARLIE CHANCE", "CHINESE NEW YEAR", "CHRONOS JOKER", "CLASH OF CAMELOT", "CLOUD QUEST", "COPS 'N' ROBBERS", "COUNT JOKULA", "COURT OF HEARTS", "COYOTE CASH", "CRYSTAL SUN", "DAWN OF EGYPT", "DEADLY 5", "DEMON", "DERBY WHEEL", "DIAMOND VORTEX", "DIO KILLING THE DRAGON", "DIVINE SHOWDOWN", "DOOM OF EGYPT", "DRAGON MAIDEN", "DRAGON SHIP", "EASTER EGGS", "EGYPTIAN FORTUNE", "ENERGOONZ", "EYE OF THE ATUM", "FACES OF FREYA", "FIRE JOKER", "FIRE JOKER FREEZE", "FIRE TOAD", "FORGE OF FORTUNES", "FORTUNE REWIND", "FROZEN GEMS", "GAME OF GLADIATORS", "GEMIX", "GHOST OF DEAD", "GIGANTUANZ", "GOLD KING", "GOLD TROPHY 2", "GOLD VOLCANO", "GOLDEN TICKET", "GRIM THE SPLITTER", "GUNSLINGER", "HALLOWEEN JACK", "HAPPY HALLOWEEN", "HOLIDAY SPIRITS", "HONEY RUSH", "HOT TO BURN", "HOTEL YETI-WAY", "HOUSE OF DOOM", "HUGO", "HUGO 2", "ICE JOKER", "IDOL OF FORTUNE", "IMMORTAL GUILD", "INFERNO STAR", "IRON GIRL", "ISHIN", "IT'S MAGIC", "JACKPOT POKER", "JADE MAGICIAN", "JEWEL BOX", "JOLLY ROGER", "JOLLY ROGER 2", "KISS REELS OF ROCK", "KNIGHT'S LIFE", "KRAKEN'S SKY", "LADY OF FORTUNE", "LEGACY OF DEAD", "LEGACY OF EGYPT", "LEGACY OF INCA", "LEPRECHAUN GOES EGYPT", "LEPRECHAUN GOES HELL", "LEPRECHAUN GOES TO WILD", "LORD MERLIN", "LOVE IS IN THE AIR", "LUCKY DIAMONDS", "MADAME DESTINY", "MADAME DESTINY MEGAWAYS", "MAGICAL STACKS", "MAHJONG 88", "MERMAID'S DIAMOND", "METAL DETECTOR", "MOON PRINCESS", "MOON PRINCESS 100", "MOON PRINCESS TRINITY", "MOUNTAIN OF WEALTH", "MUERTO EN MITLAN", "MULTIFRUIT 81", "MYSTERY JOKER", "MYSTERY JOKER 6000", "NINJA FRUITS", "NYX", "OCTOPUS TREASURE", "ODIN: PROTECTOR OF REALMS", "PAPYRUS", "PEARLS OF INDIA", "PERFECT GEMS", "PHOENIX REBORN", "PIGGY BANK", "PIMPED", "PIXIES VS PIRATES", "PLANET FORTUNE", "PROSPERITY PALACE", "QUEEN'S DAY TILT", "RABBIT HOLE RICHES", "RAGING REX", "RAGING REX 2", "RAINBOW CHARMS", "REACTOONZ", "REACTOONZ 2", "REEL STEAL", "RICH WILDE", "RISE OF DEAD", "RISE OF MERLIN", "RISE OF OLYMPUS", "RISE OF OLYMPUS 100", "RITUAL RESURRECTION", "ROCCO GALLO", "ROCK-N-ROLLA", "RONIN", "ROYAL MASQUERADE", "SABATON", "SAFARI OF WEALTH", "SAILS OF GOLD", "SAMURAI KEN", "SEA HUNTER", "SECRET OF THE STONES", "SHAMROCK MINER", "SINS", "SMILEY'S", "SPACE RACE", "SPARKY & SHORTZ", "SPEED CASH", "STAR BLAST", "STICKY JOKER", "STREET MAGIC", "SUPER FLIP", "SWEET ALCHEMY", "SWEET ALCHEMY 2", "SWORD AND THE GRAIL", "TALES OF ASGARD", "TEMPLE OF WEALTH", "TESTAMENT", "THAT'S RICH", "THE LAST SUNDOWN", "THE SWORD AND THE GRAIL", "THUNDER SCREECH", "TOME OF MADNESS", "TROLL HUNTERS", "TROLL HUNTERS 2", "TWISTED SISTER", "USA FLIP", "VIKING RUNECRAFT", "WILD BLOOD", "WILD BLOOD 2", "WILD FALLS", "WILD FALLS 2", "WILD FRAMES", "WILD MELON", "WILD NORTH", "WIN-A-BEEST", "XMAS JOKER", "XMAS MAGIC", "TOME OF INSANITY", "LEGION GOLD UNLEASHED", "PIRANHA PAYS", "GARGANTOONZ", "PIGGY BLITZ", "SWEET ALCHEMY 100", "RUFF HEIST", "RETURN OF THE GREEN KNIGHT", "SCROLL OF SETH", "MERLIN: JOURNEY OF FLAME", "VIKING RUNECRAFT APOCALYPSE", "HIGHWAY LEGENDS", "PANDORA'S BOX OF EVIL", "COLT LIGHTNING", "PILGRIM OF DEAD", "INVADING VEGAS", "ATHENA'S GLORY", "MOUNT M", "LEPRECHAUN'S VAULT", "MEGA DON", "CASH OF COMMAND", "KING'S MASK", "ANIMAL MADNESS", "PUEBLA PARADE", "LORDI REEL MONSTERS", "SECRET OF DEAD", "LOVE JOKER", "TALE OF KYUBIKO", "CAPTAIN XENO'S EARTH", "HOOLIGAN HUSTLE", "BOAT BONANZA COLOSSAL CATCH", "GAME OF GLADIATORS UPRISING"
    ]
}

SIGNALS = [
    " 10 Manual Spins -> 30 Turbo Spins",
    " 5 Quick Spins -> 15 Manual Spins",
    " 30 Turbo Spins then Buy Bonus",
    " 10 Turbo Spins -> 10 Quick Spins -> 5 Manual Spins then Buy Bonus",
    " 20 Manual Spins then Add 1 peso bet and Buy Bonus",
    " 50 Turbo Spins (Low Stake)",
    " 8 Manual Spins -> 15 Quick Spins -> 10 Turbo Spins",
    " 7 Manual Spins -> 7 Turbo Spins -> 7 Quick Spins then Buy Bonus",
    " 15 Manual Spins -> 20 Turbo Spins -> 5 Quick Spins",
    " 12 Quick Spins -> 12 Manual Spins -> 12 Turbo Spins",
    " 25 Turbo Spins -> 10 Manual Spins",
    " 5 Manual Spins -> 5 Quick Spins -> 5 Turbo Spins -> Buy Bonus",
    " 40 Turbo Spins (Medium Stake)",
    " 10 Manual Spins -> 10 Turbo Spins -> 10 Quick Spins",
    " 18 Turbo Spins -> 12 Manual Spins",
    " 30 Quick Spins",
    " 9 Manual Spins -> 18 Turbo Spins -> 9 Quick Spins",
    " 15 Turbo Spins -> 15 Quick Spins",
    " 22 Manual Spins -> 11 Turbo Spins",
    " 7 Turbo Spins -> 7 Manual Spins -> 7 Quick Spins -> 7 Turbo Spins",
    " 50 Quick Spins",
    " 20 Turbo Spins -> 20 Manual Spins",
    " 10 Quick Spins -> 20 Turbo Spins",
    " 15 Manual Spins -> 15 Turbo Spins",
    " 30 Turbo Spins -> Buy Bonus",
    " 10 Turbo Spins -> 10 Quick Spins -> 10 Manual Spins",
    " 5 Manual Spins -> 10 Turbo Spins -> 15 Quick Spins",
    " 20 Quick Spins -> 10 Turbo Spins",
    " 60 Turbo Spins",
    " 12 Manual Spins -> 24 Turbo Spins",
    " 15 Quick Spins -> 15 Manual Spins",
    " 10 Turbo Spins -> 10 Quick Spins -> 10 Manual Spins -> Buy Bonus",
    " 20 Manual Spins -> 10 Turbo Spins",
    " 30 Quick Spins",
    " 15 Turbo Spins -> 15 Quick Spins",
    " 25 Manual Spins",
    " 10 Manual Spins -> 20 Turbo Spins",
    " 15 Quick Spins -> 15 Turbo Spins",
    " 5 Manual Spins -> 5 Quick Spins -> 5 Turbo Spins -> 5 Manual Spins",
    " 40 Turbo Spins",
    " 20 Quick Spins -> 20 Turbo Spins",
    " 10 Manual Spins -> 30 Quick Spins",
    " 15 Turbo Spins -> 15 Manual Spins",
    " 10 Quick Spins -> 10 Turbo Spins -> 10 Manual Spins",
    " 25 Turbo Spins",
    " 12 Manual Spins -> 12 Quick Spins",
    " 30 Turbo Spins -> Buy Bonus",
    " 20 Quick Spins -> 10 Manual Spins",
    " 15 Turbo Spins -> 15 Quick Spins -> 15 Manual Spins",
    " 15 Manual Spins -> 15 Turbo Spins -> 15 Quick Spins",
    " 10 Manual Spins -> 20 Quick Spins -> Buy Bonus",
    " 30 Quick Spins -> Buy Bonus",
    " 15 Manual Spins -> Buy Bonus"
]

# ================= ANIMATION LOGIC =================
def system_startup_animation(chat_id, message_id):
    # Professional Startup Animation
    steps = [
        "⚙️ <b>INITIALIZING SYSTEM...</b>",
        "🧬 <b>LOADING MODULES...</b>",
        "🔐 <b>BYPASSING SECURITY...</b>",
        "📡 <b>CONNECTING TO DATABASE...</b>",
        "✅ <b>SYSTEM READY</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.8)
        except: pass

def logout_animation(chat_id, message_id):
    steps = [
        "🚪 <b>LOGGING OUT...</b>",
        "🧹 <b>CLEARING SESSION DATA...</b>",
        "🔐 <b>CLOSING SECURE TUNNEL...</b>",
        "✅ <b>LOGOUT SUCCESSFUL</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.6)
        except: pass

def reset_animation(chat_id, message_id):
    steps = [
        "🔄 <b>RESETTING SYSTEM...</b>",
        "🧹 <b>PURGING CACHE...</b>",
        "⚙️ <b>RECALIBRATING RNG...</b>",
        "🧬 <b>RELOADING MODULES...</b>",
        "✅ <b>SYSTEM RESET COMPLETE</b>"
    ]
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, message_id, parse_mode="HTML")
            time.sleep(0.6)
        except: pass

def display_provider_games(chat_id, uid, provider_name):
    delete_user_past_msg(chat_id, uid)
    user_sessions[uid]["provider"] = provider_name
    display_games = PROVIDERS_DATA.get(provider_name, [])

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("🔙 BACK"))
    kb.add(*[types.KeyboardButton(g) for g in display_games])

    msg = bot.send_message(chat_id, f"🎰 <b>{provider_name}</b>\nShowing {len(display_games)} Games Available:", reply_markup=kb, parse_mode="HTML", protect_content=True)
    user_sessions[uid]["last_msg"] = msg.message_id

def live_encoding_animation(chat_id, message_id, uid, selected_game, session_id):
    # Initial Delay with Message
    try:
        res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
        bot.edit_message_text(
            f"{res_text}\n\n⚠️ <b>INITIATING INJECTION PROTOCOL...</b>", 
            chat_id, message_id, parse_mode="HTML"
        )
    except: pass
    time.sleep(1.5)

    # Professional "Hacking" Frames
    frames = [
        f"⏳ <b>INJECTING CODE TO {selected_game}</b>\n<code>[■□□□□□□□□□] 10%</code>",
        f"⏳ <b>INJECTING CODE TO {selected_game}</b>\n<code>[■■■□□□□□□□] 30%</code>",
        f"⏳ <b>INJECTING CODE TO {selected_game}</b>\n<code>[■■■■■□□□□□] 50%</code>",
        f"⏳ <b>INJECTING CODE TO {selected_game}</b>\n<code>[■■■■■■■□□□] 70%</code>",
        f"⏳ <b>INJECTING CODE TO {selected_game}</b>\n<code>[■■■■■■■■■□] 90%</code>",
        f"⏳ <b>INJECTING CODE TO {selected_game}</b>\n<code>[■■■■■■■■■■] 100%</code>",
        f"🔄 <b>BYPASSING FIREWALL...</b>",
        f"🔄 <b>SYNCING RNG SEEDS...</b>"
    ]
    
    # Run animation once
    for frame in frames:
        if uid not in user_sessions or user_sessions[uid].get("encoding") != True or user_sessions[uid].get("encoding_id") != session_id:
            break
        try:
            res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{res_text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n{frame}",
                parse_mode="HTML"
            )
        except:
            break
        time.sleep(1.0)
    
    # Animation finished, now show the buttons
    if uid in user_sessions and user_sessions[uid].get("encoding") == True and user_sessions[uid].get("encoding_id") == session_id:
        try:
            res_text = user_sessions[uid].get("result_text", "SYSTEM ERROR")
            inline_kb = types.InlineKeyboardMarkup(row_width=1)
            inline_kb.add(
                types.InlineKeyboardButton("👁️ SHOW PATTERN", callback_data="show_pattern"),
                types.InlineKeyboardButton("🔄 Re-Generate Pattern", callback_data="run_gen"),
                types.InlineKeyboardButton("🔄 Change Game", callback_data="change_game"),
                types.InlineKeyboardButton("🚪 Change Platform", callback_data="change_platform"),
                types.InlineKeyboardButton("🔄 Reset System", callback_data="reset_system")
            )
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=res_text,
                reply_markup=inline_kb,
                parse_mode="HTML"
            )
            
            # REMINDER MESSAGE
            gen_count = user_sessions[uid].get("gen_count", 0)
            if gen_count == 1:
                rem_kb = types.InlineKeyboardMarkup(row_width=1).add(
                    types.InlineKeyboardButton("🔐 Log in to Start", callback_data="login_clicked")
                )
                rem_text = (
                    "⚠️ <b>SYSTEM WARNING: ACCOUNT NOT SYNCHRONIZED</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "It appears you haven't fully logged in or synchronized your account with the system. "
                    "The patterns generated might not match your game!\n\n"
                    "<b>Instructions:</b>\n"
                    "1. Click the 'Log in to Start' button below.\n"
                    "2. Log in to your casino account.\n"
                    "3. Return here to use the generated patterns."
                )
                rem_msg = bot.send_message(chat_id, rem_text, reply_markup=rem_kb, parse_mode="HTML", protect_content=True)
                user_sessions[uid]["last_kb_msg"] = rem_msg.message_id
            elif gen_count == 2 or gen_count == 3:
                rem_text = "Note: Make sure you are logged in your account correctly to avoid mismatched of the generated pattern."
                rem_msg = bot.send_message(chat_id, rem_text, parse_mode="HTML", protect_content=True)
                user_sessions[uid]["last_kb_msg"] = rem_msg.message_id
                
        except: pass

# ================= HELPERS =================
def delete_user_past_msg(chat_id, uid):
    if user_sessions.get(uid, {}).get("last_msg"):
        try: 
            bot.delete_message(chat_id, user_sessions[uid]["last_msg"])
        except: 
            pass
    if user_sessions.get(uid, {}).get("last_kb_msg"):
        try: 
            bot.delete_message(chat_id, user_sessions[uid]["last_kb_msg"])
        except: 
            pass

def main_menu(chat_id, uid):
    delete_user_past_msg(chat_id, uid)
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*[types.KeyboardButton(p) for p in PROVIDERS_DATA.keys()])
    msg = bot.send_message(chat_id, "⚙️ <b>MAIN CONTROL PANEL:</b>\n━━━━━━━━━━━━━━━━━━━━━━\nSelect your preferred Slot Provider to begin analysis:", reply_markup=kb, parse_mode="HTML", protect_content=True)
    if uid not in user_sessions:
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None}
    user_sessions[uid]["last_msg"] = msg.message_id
    user_sessions[uid]["encoding"] = False

# ================= ADMIN COMMANDS =================
@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total = len(user_ids)
    bot.send_message(ADMIN_ID, f"📊 <b>BOT STATISTICS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n👥 <b>Total Users:</b> {total}", parse_mode="HTML", protect_content=True)

@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.send_message(ADMIN_ID, "❌ <b>Usage:</b> <code>/broadcast Your message here</code>", parse_mode="HTML", protect_content=True)
        return
    
    count = 0
    for uid in list(user_ids):
        try:
            bot.send_message(uid, f"📢 <b>ADMIN ANNOUNCEMENT</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="HTML", protect_content=True)
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ <b>Broadcast sent to {count} users.</b>", parse_mode="HTML", protect_content=True)

# ================= HANDLERS =================
def init_user_session(uid):
    if uid not in user_sessions:
        user_sessions[uid] = {
            "last_msg": None, 
            "last_kb_msg": None,
            "last_gen_time": 0, 
            "game": None, 
            "provider": None, 
            "encoding": False, 
            "casino": None, 
            "is_logged_in": True, 
            "gen_count": 0, 
            "is_busy": False
        }

def is_bot_busy(uid):
    init_user_session(uid)
    return user_sessions[uid].get("is_busy", False)

def set_bot_busy(uid, status):
    init_user_session(uid)
    user_sessions[uid]["is_busy"] = status

@bot.message_handler(commands=["start", "reset"])
def start_cmd(message):
    uid = message.from_user.id
    if is_bot_busy(uid): return
    set_bot_busy(uid, True)
    try:
        # Check if new for Admin Notification
        is_new = uid not in user_ids
        if is_new:
            user_ids.add(uid)
            # Turso insert in a background thread so it doesn't slow down the bot
            def save_db():
                add_user_db(uid)
            t = threading.Thread(target=save_db)
            t.daemon = True
            t.start()
        
        # Reset session data if /reset is called
        if message.text == "/reset":
            user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "gen_count": 0, "is_busy": True}
        
        # Delete previous bot message to keep chat clean
        delete_user_past_msg(message.chat.id, uid)
        
        if uid not in user_sessions or not user_sessions[uid]:
            user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": True, "gen_count": 0, "is_busy": True}
    
        # Notify Admin ONLY if truly new session
        if is_new:
            try:
                bot.send_message(ADMIN_ID, f"🆕 <b>NEW USER STARTED BOT</b>\nUser: {message.from_user.first_name}\nID: <code>{uid}</code>", parse_mode="HTML", protect_content=True)
            except: pass
    
        # INTRO SCREEN (Always show this)
        caption = (
            f"🛡️ <b>Welcome, {message.from_user.first_name}!</b>\n"
            "🛡️ <b>SLOT JACKPOT READER v5.2</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>SYSTEM STATUS:</b> 🟢 <b>OPTIMIZED</b>\n"
            "📡 <b>NETWORK:</b> <i>Encrypted Tunnel Active</i>\n\n"
            "Welcome to the most advanced <b>RNG Pattern Recognition System</b>. Our AI uses deep-learning algorithms to decode server-side seeds and identify high-probability winning windows in real-time.\n\n"
            "🔹 <b>Real-Time Seed Analysis:</b> Decodes live RNG sequences for precise entry points.\n"
            "🔹 <b>Dynamic Pattern Injection:</b> Provides optimized spin sequences based on server response.\n"
            "🔹 <b>99.2% Accuracy Rating:</b> Powered by the latest Neural Network architecture.\n\n"
            "🚀 <b>Click the button below to initialize the system...</b>"
        )
        
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🚀 INITIALIZE SYSTEM", callback_data="intro_proceed"))
    
        try:
            msg = bot.send_photo(message.chat.id, INTRO_IMAGE_URL, caption=caption, reply_markup=kb, parse_mode="HTML", protect_content=True)
        except:
            msg = bot.send_message(message.chat.id, caption, reply_markup=kb, parse_mode="HTML", protect_content=True)
    
        user_sessions[uid]["last_msg"] = msg.message_id
    finally:
        set_bot_busy(uid, False)

@bot.callback_query_handler(func=lambda c: c.data == "user_login")
def handle_user_login(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    if is_bot_busy(uid): return
    set_bot_busy(uid, True)
    try:
        user_sessions[uid]["is_logged_in"] = True
        
        # Loading animation
        msg = bot.send_message(call.message.chat.id, "⏳ <b>INITIALIZING SYSTEM...</b>", parse_mode="HTML", protect_content=True)
        time.sleep(1)
        bot.edit_message_text("⏳ <b>LOADING MODULES...</b>", call.message.chat.id, msg.message_id, parse_mode="HTML")
        time.sleep(1)
        bot.delete_message(call.message.chat.id, msg.message_id)
        
        # Proceed to casino selection
        choose_casino_platform(call)
    finally:
        set_bot_busy(uid, False)

@bot.callback_query_handler(func=lambda c: c.data == "intro_proceed")
def choose_casino_platform(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    
    delete_user_past_msg(call.message.chat.id, uid)

    kb = types.InlineKeyboardMarkup(row_width=1)
    for casino in CASINO_DATA.keys():
        kb.add(types.InlineKeyboardButton(f"🏛 {casino}", callback_data=f"set_casino_{casino}"))

    msg = bot.send_message(call.message.chat.id, "🏗 <b>SELECT PLATFORM DATABASE</b>\n━━━━━━━━━━━━━━━━━━━━━━\nChoose your Casino Platform to load the correct RNG configuration:", reply_markup=kb, parse_mode="HTML", protect_content=True)
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_casino_"))
def confirm_casino_selection(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    init_user_session(uid)
    selected_casino = call.data.replace("set_casino_", "")
    user_sessions[uid]["casino"] = selected_casino

    delete_user_past_msg(call.message.chat.id, uid)

    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("🔐 Log in to Start", callback_data="login_clicked"),
        types.InlineKeyboardButton("🚀 PROCEED TO SYSTEM", callback_data="open_menu")
    )
    
    welcome_text = (
        f"🏛 <b>PLATFORM SELECTED: {selected_casino}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>IMPORTANT:</b> You must log in to your account first before proceeding.\n\n"
        "🔐 <b>Click 'Log in to Start' to authenticate.</b>\n"
        "🚀 Then click 'PROCEED TO SYSTEM'."
    )
    msg = bot.send_message(call.message.chat.id, welcome_text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True, protect_content=True)
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "login_clicked")
def login_clicked_callback(call):
    uid = call.from_user.id
    init_user_session(uid)
    user_sessions[uid]["login_clicks"] = user_sessions.get(uid, {}).get("login_clicks", 0) + 1
    selected_casino = user_sessions[uid].get("casino", "UNKNOWN")
    url = CASINO_DATA.get(selected_casino, "https://google.com")
    
    kb = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("🌐 OPEN LOGIN PAGE", url=url)
    )
    
    # Delete previous kb msg if it exists
    if user_sessions.get(uid, {}).get("last_kb_msg"):
        try: bot.delete_message(call.message.chat.id, user_sessions[uid]["last_kb_msg"])
        except: pass

    link_msg = bot.send_message(
        call.message.chat.id, 
        f"🔗 <b>Secure Login Link for {selected_casino}</b>\n\nClick the button below to open the login page. Make sure to log in before generating patterns!", 
        reply_markup=kb, 
        parse_mode="HTML",
        protect_content=True
    )
    user_sessions[uid]["last_kb_msg"] = link_msg.message_id
    bot.answer_callback_query(call.id, "Login link generated!")

@bot.message_handler(commands=["reset"])
def reset_cmd(message):
    uid = message.from_user.id
    delete_user_past_msg(message.chat.id, uid)

    user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "gen_count": 0}

    res_msg = bot.send_message(message.chat.id, "🔄 <b>RESETTING TOOL SYSTEM...</b>", parse_mode="HTML", protect_content=True)
    time.sleep(1)
    for i in range(1, 4):
        try:
            bot.edit_message_text(f"🔄 <b>CLEANING CACHE{'.' * i}</b>", message.chat.id, res_msg.message_id, parse_mode="HTML")
            time.sleep(0.3)
        except: pass

    try: bot.delete_message(message.chat.id, res_msg.message_id)
    except: pass

    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 RESTART SYSTEM", callback_data="intro_proceed"))
    msg = bot.send_message(message.chat.id, "✅ <b>RESET SUCCESSFUL</b>\nSystem cache has been cleared.", reply_markup=kb, parse_mode="HTML", protect_content=True)
    user_sessions[uid]["last_msg"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "show_pattern")
def show_pattern_callback(call):
    uid = call.from_user.id
    init_user_session(uid)
    pattern = user_sessions[uid].get("pattern", "No pattern available.")
    game = user_sessions[uid].get("game", "UNKNOWN")
    bot.answer_callback_query(call.id, f"GAME INJECTED: {game}\nPATTERN: {pattern}", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "🔄 Re-Generate Pattern")
def regenerate_btn(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    if is_bot_busy(uid): return
    if (time.time() - user_sessions.get(uid, {}).get("last_gen_time", 0)) < 20:
        bot.send_message(chat_id, "⚠️ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...", protect_content=True)
        return

    set_bot_busy(uid, True)
    try:
        # Improved 5-second generation animation
        msg = bot.send_message(chat_id, "🔄 <b>INITIALIZING...</b>\n<code>[▯▯▯▯▯▯▯▯▯▯] 0%</code>", parse_mode="HTML", protect_content=True)
        
        steps = [
            {"icon": "📡", "text": "Connecting to Servers..."},
            {"icon": "🧬", "text": "Extracting RNG Seed Data..."},
            {"icon": "🛰", "text": "Matching Pattern Database..."},
            {"icon": "🧠", "text": "Neural Network Processing..."},
            {"icon": "✅", "text": "Signal Generation Complete!"}
        ]
    
        for idx, step in enumerate(steps):
            p_bar = ["■" if i <= int((idx/4)*9) else "▯" for i in range(10)]
            status_text = (
                f"<b>{step['icon']} <code>{step['text']}</code></b>\n"
                f"<code>[{''.join(p_bar)}] {int((idx/4)*100)}%</code>"
            )
            try:
                bot.edit_message_text(status_text, chat_id, msg.message_id, parse_mode="HTML")
                time.sleep(1) # Total 5 seconds for 5 steps
            except: pass
        
        try: bot.delete_message(chat_id, msg.message_id)
        except: pass
        
        run_gen_logic(chat_id, message.message_id, uid, user_sessions[uid].get("casino", "UNKNOWN"), user_sessions[uid].get("game", "UNKNOWN"), user_sessions[uid].get("provider", "UNKNOWN"))
    finally:
        set_bot_busy(uid, False)

@bot.message_handler(func=lambda m: m.text == "🔄 Change Game")
def change_game_btn(message):
    uid = message.from_user.id
    if uid in user_sessions:
        user_sessions[uid]["encoding"] = False 
        user_sessions[uid]["encoding_id"] = None 
        provider = user_sessions[uid].get("provider", list(PROVIDERS_DATA.keys())[0])
        display_provider_games(message.chat.id, uid, provider)

@bot.message_handler(func=lambda m: m.text == "🔄 Reset System")
def reset_system_btn(message):
    uid = message.from_user.id
    if is_bot_busy(uid): return
    set_bot_busy(uid, True)
    try:
        # Reset animation
        msg = bot.send_message(message.chat.id, "🔄 <b>INITIATING RESET...</b>", parse_mode="HTML", protect_content=True)
        reset_animation(message.chat.id, msg.message_id)
        bot.delete_message(message.chat.id, msg.message_id)
        
        # Delete last message
        delete_user_past_msg(message.chat.id, uid)
        # Clear session
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": True, "gen_count": 0, "is_busy": True}
        
        # Go directly to platform selection
        class Call:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
                self.id = "0"
        
        choose_casino_platform(Call(message))
    finally:
        set_bot_busy(uid, False)

@bot.callback_query_handler(func=lambda c: c.data == "open_menu")
def trigger_menu(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    if is_bot_busy(uid): return
    set_bot_busy(uid, True)
    try:
        delete_user_past_msg(call.message.chat.id, uid)
        
        # SYSTEM CHECK ANIMATION
        msg = bot.send_message(call.message.chat.id, "⚙️ <b>SYSTEM CHECK...</b>", parse_mode="HTML", protect_content=True)
        system_startup_animation(call.message.chat.id, msg.message_id)
        bot.delete_message(call.message.chat.id, msg.message_id)
        
        main_menu(call.message.chat.id, uid)
    finally:
        set_bot_busy(uid, False)

@bot.message_handler(func=lambda m: m.text in PROVIDERS_DATA.keys())
def show_games(message):
    display_provider_games(message.chat.id, message.from_user.id, message.text)

@bot.message_handler(func=lambda m: m.text == "🔙 BACK")
def back_to_prov(message): 
    main_menu(message.chat.id, message.from_user.id)

@bot.message_handler(func=lambda m: any(m.text in v for v in PROVIDERS_DATA.values()))
def pick_game(message):
    uid = message.from_user.id
    delete_user_past_msg(message.chat.id, uid)
    user_sessions[uid]["game"] = message.text
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 ANALYZE RNG SEED", callback_data="run_gen"))
    msg = bot.send_message(message.chat.id, f"🎯 <b>SELECTED GAME:</b> {message.text}\n━━━━━━━━━━━━━━━━━━━━━━\nClick the button below to start the analysis.", reply_markup=kb, parse_mode="HTML", protect_content=True)
    user_sessions[uid]["last_msg"] = msg.message_id

def run_gen_logic(chat_id, message_id, uid, casino, game, provider):
    if (time.time() - user_sessions[uid].get("last_gen_time", 0)) < 20:
        bot.send_message(chat_id, "⚠️ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...", protect_content=True)
        return

    user_sessions[uid]["last_gen_time"] = time.time()
    user_sessions[uid]["gen_count"] = user_sessions[uid].get("gen_count", 0) + 1
    
    # NOTIFY ADMIN OF GENERATION
    try:
        bot.send_message(ADMIN_ID, f"📊 <b>SIGNAL GENERATED</b>\nUser: {uid}\n🏛 <b>Casino:</b> {casino}\n🎰 <b>Game:</b> {game}", parse_mode="HTML", protect_content=True)
    except: pass

    steps = [
        {"icon": "📡", "text": "Connecting to Servers..."},
        {"icon": "🧬", "text": "Extracting RNG Seed Data..."},
        {"icon": "🛰", "text": "Matching Pattern Database..."},
        {"icon": "🧠", "text": "Neural Network Processing..."},
        {"icon": "✅", "text": "Signal Generation Complete!"}
    ]

    for idx, step in enumerate(steps):
        p_bar = ["■" if i <= int((idx/4)*9) else "▯" for i in range(10)]
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
        f"📡 <b>SIGNAL DETECTED</b> <code>#{fake_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Target:</b> {game}\n"
        f"🎰 <b>Provider:</b> {provider}\n"
        f"📊 <b>Probability:</b> {random.uniform(96, 99):.2f}%\n"
        f"⚡ <b>Volatility:</b> HIGH\n"
        f"⏰ <b>Valid Until:</b> {v_until}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Click the button below to reveal the injection pattern.</i>"
    )

    user_sessions[uid]["result_text"] = result_text
    user_sessions[uid]["pattern"] = random.choice(valid_signals)
    user_sessions[uid]["encoding"] = True 
    session_id = str(uuid.uuid4())
    user_sessions[uid]["encoding_id"] = session_id
    
    # Send message initially without buttons
    msg = bot.send_message(chat_id, result_text, parse_mode="HTML", protect_content=True)
    
    user_sessions[uid]["last_msg"] = msg.message_id
    user_sessions[uid]["last_kb_msg"] = None # No separate keyboard message

    t = threading.Thread(target=live_encoding_animation, args=(chat_id, msg.message_id, uid, game, session_id))
    t.daemon = True
    t.start()

@bot.callback_query_handler(func=lambda c: c.data == "run_gen")
def run_gen(call):
    uid = call.from_user.id
    if is_bot_busy(uid):
        try: bot.answer_callback_query(call.id, "Please wait...", show_alert=True)
        except: pass
        return
    if (time.time() - user_sessions.get(uid, {}).get("last_gen_time", 0)) < 20:
        bot.answer_callback_query(call.id, "⚠️ SYSTEM BUSY. Pattern is active.\nPlease wait a few seconds...", show_alert=True)
        return

    try: bot.answer_callback_query(call.id)
    except: pass
    
    set_bot_busy(uid, True)
    try:
        user_sessions[uid]["last_gen_time"] = time.time()
        user_sessions[uid]["gen_count"] = user_sessions[uid].get("gen_count", 0) + 1
        
        # NOTIFY ADMIN OF GENERATION
        selected_casino = user_sessions[uid].get("casino", "UNKNOWN")
        selected_game = user_sessions[uid].get("game", "UNKNOWN")
        try:
            bot.send_message(ADMIN_ID, f"📊 <b>SIGNAL GENERATED</b>\nUser: {call.from_user.first_name}\nID: <code>{uid}</code>\n🏛 <b>Casino:</b> {selected_casino}\n🎰 <b>Game:</b> {selected_game}", parse_mode="HTML", protect_content=True)
        except: pass
    
        steps = [
            {"icon": "📡", "text": "Connecting to Servers..."},
            {"icon": "🧬", "text": "Extracting RNG Seed Data..."},
            {"icon": "🛰", "text": "Matching Pattern Database..."},
            {"icon": "🧠", "text": "Neural Network Processing..."},
            {"icon": "✅", "text": "Signal Generation Complete!"}
        ]
    
        for idx, step in enumerate(steps):
            p_bar = ["■" if i <= int((idx/4)*9) else "▯" for i in range(10)]
            status_text = (
                f"<b>{step['icon']} <code>{step['text']}</code></b>\n"
                f"<code>[{''.join(p_bar)}] {int((idx/4)*100)}%</code>"
            )
            try:
                bot.edit_message_text(status_text, call.message.chat.id, call.message.message_id, parse_mode="HTML")
                time.sleep(0.7)
            except: pass
    
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
    
        if user_sessions[uid].get("last_kb_msg"):
            try: bot.delete_message(call.message.chat.id, user_sessions[uid]["last_kb_msg"])
            except: pass
    
        ph_now = datetime.utcnow() + timedelta(hours=8)
        v_until = (ph_now + timedelta(minutes=random.randint(30, 45))).strftime("%I:%M %p")
    
        fake_id = str(uuid.uuid4())[:8].upper()
    
        current_provider = user_sessions[uid].get('provider', '')
        if "PG" in current_provider.upper():
            valid_signals = [s for s in SIGNALS if "Turbo" not in s]
        else:
            valid_signals = SIGNALS
        
        if not valid_signals:
            valid_signals = SIGNALS
    
        result_text = (
            f"📡 <b>SIGNAL DETECTED</b> <code>#{fake_id}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Target:</b> {user_sessions[uid].get('game')}\n"
            f"🎰 <b>Provider:</b> {user_sessions[uid].get('provider')}\n"
            f"📊 <b>Probability:</b> {random.uniform(96, 99):.2f}%\n"
            f"⚡ <b>Volatility:</b> HIGH\n"
            f"⏰ <b>Valid Until:</b> {v_until}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Click the button below to reveal the injection pattern.</i>"
        )
    
        user_sessions[uid]["result_text"] = result_text
        user_sessions[uid]["pattern"] = random.choice(valid_signals)
        user_sessions[uid]["encoding"] = True 
        session_id = str(uuid.uuid4())
        user_sessions[uid]["encoding_id"] = session_id
        
        # Send message initially without buttons
        msg = bot.send_message(call.message.chat.id, result_text, parse_mode="HTML", protect_content=True)
        user_sessions[uid]["last_msg"] = msg.message_id
        user_sessions[uid]["last_kb_msg"] = None
    
        t = threading.Thread(target=live_encoding_animation, args=(call.message.chat.id, msg.message_id, uid, selected_game, session_id))
        t.daemon = True
        t.start()
    finally:
        set_bot_busy(uid, False)

@bot.callback_query_handler(func=lambda c: c.data == "change_game")
def change_game_callback(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    if uid in user_sessions:
        user_sessions[uid]["encoding"] = False 
        user_sessions[uid]["encoding_id"] = None 
        provider = user_sessions[uid].get("provider", list(PROVIDERS_DATA.keys())[0])
        display_provider_games(call.message.chat.id, uid, provider)

@bot.callback_query_handler(func=lambda c: c.data == "change_platform")
def change_platform_callback(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    if is_bot_busy(uid): return
    
    if uid in user_sessions:
        set_bot_busy(uid, True)
        try:
            user_sessions[uid]["encoding"] = False 
            user_sessions[uid]["encoding_id"] = None 
            
            # Logout animation
            logout_animation(call.message.chat.id, call.message.message_id)
            time.sleep(0.5)
            
            # Clear specific session data
            user_sessions[uid]["casino"] = None
            user_sessions[uid]["game"] = None
            user_sessions[uid]["provider"] = None
            
            choose_casino_platform(call)
        finally:
            set_bot_busy(uid, False)

@bot.callback_query_handler(func=lambda c: c.data == "reset_system")
def reset_system_callback(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    uid = call.from_user.id
    if is_bot_busy(uid): return
    set_bot_busy(uid, True)
    try:
        # Reset animation
        reset_animation(call.message.chat.id, call.message.message_id)
        time.sleep(0.5)
        
        # Delete last message
        delete_user_past_msg(call.message.chat.id, uid)
        # Clear session
        user_sessions[uid] = {"last_msg": None, "last_gen_time": 0, "game": None, "provider": None, "encoding": False, "casino": None, "is_logged_in": True, "is_busy": True}
        
        # Go directly to platform selection
        choose_casino_platform(call)
    finally:
        set_bot_busy(uid, False)

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 BOT STARTING...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
