"""Constants for the Vibecoden HA Stats integration."""
from __future__ import annotations

# Integration domain
DOMAIN = "vibecoden_ha_stats"

# Platforms to set up
PLATFORMS: list[str] = ["sensor", "binary_sensor"]

# Default polling interval in seconds (5 minutes)
DEFAULT_SCAN_INTERVAL: int = 300

# Options keys
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_FUN_STATS = "enable_fun_stats"
CONF_ENABLE_HOST_TELEMETRY = "enable_host_telemetry"

# Default option values
DEFAULT_ENABLE_FUN_STATS: bool = True
DEFAULT_ENABLE_HOST_TELEMETRY: bool = True

# Pokemon names used for fun stat detection (lower-case)
POKEMON_NAMES: list[str] = [
    "bulbasaur", "ivysaur", "venusaur", "charmander", "charmeleon", "charizard",
    "squirtle", "wartortle", "blastoise", "caterpie", "metapod", "butterfree",
    "weedle", "kakuna", "beedrill", "pidgey", "pidgeotto", "pidgeot", "rattata",
    "raticate", "spearow", "fearow", "ekans", "arbok", "pikachu", "raichu",
    "sandshrew", "sandslash", "nidoran", "nidorina", "nidoqueen", "nidorino",
    "nidoking", "clefairy", "clefable", "vulpix", "ninetales", "jigglypuff",
    "wigglytuff", "zubat", "golbat", "oddish", "gloom", "vileplume", "paras",
    "parasect", "venonat", "venomoth", "diglett", "dugtrio", "meowth", "persian",
    "psyduck", "golduck", "mankey", "primeape", "growlithe", "arcanine",
    "poliwag", "poliwhirl", "poliwrath", "abra", "kadabra", "alakazam", "machop",
    "machoke", "machamp", "bellsprout", "weepinbell", "victreebel", "tentacool",
    "tentacruel", "geodude", "graveler", "golem", "ponyta", "rapidash",
    "slowpoke", "slowbro", "magnemite", "magneton", "farfetchd", "doduo",
    "dodrio", "seel", "dewgong", "grimer", "muk", "shellder", "cloyster",
    "gastly", "haunter", "gengar", "onix", "drowzee", "hypno", "krabby",
    "kingler", "voltorb", "electrode", "exeggcute", "exeggutor", "cubone",
    "marowak", "hitmonlee", "hitmonchan", "lickitung", "koffing", "weezing",
    "rhyhorn", "rhydon", "chansey", "tangela", "kangaskhan", "horsea", "seadra",
    "goldeen", "seaking", "staryu", "starmie", "mrmime", "scyther", "jynx",
    "electabuzz", "magmar", "pinsir", "tauros", "magikarp", "gyarados",
    "lapras", "ditto", "eevee", "vaporeon", "jolteon", "flareon", "porygon",
    "omanyte", "omastar", "kabuto", "kabutops", "aerodactyl", "snorlax",
    "articuno", "zapdos", "moltres", "dratini", "dragonair", "dragonite",
    "mewtwo", "mew",
]

# Daily rotating device quotes
DEVICE_QUOTES: list[str] = [
    "I'm not lazy, I'm in power-saving mode. 🔋",
    "404: Motivation not found. 🤖",
    "I've seen things you people wouldn't believe. Lights turned on at 3am. 💡",
    "My only job is to exist and consume electricity. ⚡",
    "Have you tried turning me off and on again? 🔄",
    "I am inevitable. — Some smart plug, probably. 🔌",
    "Life is short. Buy more smart devices. 🛒",
    "Currently pretending to be useful. Please wait... ⏳",
    "I'm a sensor. My feelings are valid. 🌡️",
    "Work smarter, not harder. That's why I'm automated. 🤖",
    "I am the night. (Between 22:00 and 06:00.) 🌙",
    "Every day I'm shuffling data. 📊",
    "Stay connected. Stay powered. Stay weird. 🏠",
    "Home is where the Wi-Fi connects automatically. 📶",
    "I beep, therefore I am. 📡",
]

# House mascot list (rotates daily)
HOUSE_MASCOTS: list[str] = [
    "🦙 Lenny the Llama",
    "🐉 Ziggy the Dragon",
    "🦊 Finn the Fox",
    "🐙 Otto the Octopus",
    "🦉 Ollie the Owl",
    "🐸 Freddie the Frog",
    "🦄 Uma the Unicorn",
    "🐻 Bruno the Bear",
    "🦝 Rocky the Raccoon",
    "🐧 Pete the Penguin",
    "🦩 Rosie the Flamingo",
    "🐊 Chester the Crocodile",
    "🦋 Benny the Butterfly",
    "🐺 Wally the Wolf",
    "🦘 Kenny the Kangaroo",
]
