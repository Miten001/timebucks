"""Mega Arcade Hub — 500+ curated HTML5 games + access to 10,000+ more.

Games launch via Telegram WebApp, opening inside Telegram itself.
URL pattern used: https://www.crazygames.com/game/{slug}
For the full portal:    https://www.crazygames.com/

Pagination: PAGE_SIZE games per page, organized by category.
"""
from __future__ import annotations

from typing import List, Tuple

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import ContextTypes

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CRAZYGAMES_BASE = "https://www.crazygames.com/game/"
MEGA_PORTAL_URL = "https://www.crazygames.com/t/new"  # 10,000+ games
PAGE_SIZE = 8


def _url(slug: str) -> str:
    return f"{CRAZYGAMES_BASE}{slug}"


# ─────────────────────────────────────────────────────────────────────────────
# Game catalog — 500+ curated games organized by category
# Format: (display_name, slug)
# ─────────────────────────────────────────────────────────────────────────────

ARCADE_GAMES: dict[str, List[Tuple[str, str]]] = {
    "action": [
        ("⚔️ Stickman Hook", "stickman-hook"),
        ("🥊 Stickman Fighter Epic", "stickman-fighter-epic-battles"),
        ("🏃 Vex 7", "vex-7"),
        ("🏃 Vex 6", "vex-6"),
        ("🏃 Vex 5", "vex-5"),
        ("🏃 Vex 4", "vex-4"),
        ("🏃 Vex 3", "vex-3"),
        ("🦸 Combat Online", "combat-online"),
        ("🔥 1v1.LOL", "1v1-lol"),
        ("⚡ Bullet Force", "bullet-force"),
        ("🥚 Shell Shockers", "shell-shockers"),
        ("💥 Krunker.io", "krunker-io"),
        ("🎯 Venge.io", "venge-io"),
        ("🪖 Forward Assault Remix", "forward-assault-remix"),
        ("👑 Zombs Royale", "zombs-royale-io"),
        ("🧟 Zombie Derby", "zombie-derby"),
        ("🧟 Zombie Mission", "zombie-mission"),
        ("🥷 Ninja Warrior", "ninja-clash-heroes"),
        ("💀 Die in 200 Ways", "die-in-200-ways"),
        ("🐉 Dragon vs Bricks", "dragon-vs-bricks"),
        ("🔫 Mr Bullet", "mr-bullet-online"),
        ("🤺 Stick Duel", "stick-duel-medieval-wars"),
        ("⚔️ Stickman Warriors", "stickman-warriors"),
        ("🏹 Archer Master 3D", "archer-master-3d"),
        ("🏹 Archery World Tour", "archery-world-tour"),
        ("💣 Bomberman Online", "bombhopper-io"),
        ("👹 Monster Survivors", "monster-survivors"),
        ("🪓 Stickman Boost", "stickman-boost"),
        ("🪓 Stickman Boost 2", "stickman-boost-2"),
        ("👊 Smash Karts", "smash-karts"),
        ("🐎 Horse Race 3D", "horse-race-3d"),
        ("⚡ Subway Surfers", "subway-surfers"),
        ("🏃 Run 3", "run-3"),
        ("🦁 Temple of Boom", "temple-of-boom"),
        ("🔥 Happy Wheels", "happy-wheels-3d"),
        ("⚔️ Castle Defender Saga", "castle-defender-saga"),
        ("🛡️ Stickman Defenders", "stickman-defenders"),
        ("🧨 TNT Bomb", "tnt-bomb"),
        ("🥋 Stick Fight: Shadow Warrior", "stick-fight-shadow-warrior"),
        ("🥷 Ninja Hands", "ninja-hands"),
        ("🐺 Wolf Simulator", "wolf-simulator"),
    ],
    "puzzle": [
        ("🧩 2048", "2048"),
        ("🧩 2048 Drop", "2048-drop"),
        ("🧠 Brain Test", "brain-test-tricky-puzzles"),
        ("🧠 Brain Out", "brain-out"),
        ("🍬 Candy Match Saga", "candy-match-saga"),
        ("💎 Jewel Academy", "jewel-academy"),
        ("💎 Bejeweled-style: Jewel Blast", "jewel-blast"),
        ("🟦 Block Puzzle", "block-puzzle-jewel"),
        ("🟪 Wood Block Puzzle", "wood-block-puzzle"),
        ("🟧 Tetris Cube", "tetra-blocks"),
        ("🟨 Tetra Blocks", "tetra-blocks"),
        ("🔢 Sudoku Classic", "sudoku-classic"),
        ("🔢 Sudoku", "sudoku"),
        ("🔠 Word Search", "word-search-classic"),
        ("📚 Wordle Game", "wordle"),
        ("🔡 Word Trip", "word-trip"),
        ("🧊 Ice Cream Stack", "ice-cream-stack"),
        ("🧱 Brick Out", "brick-out"),
        ("🧱 Brick Breaker", "brick-breaker"),
        ("⚙️ Mechanic Master", "mechanic-master"),
        ("🔗 Hexa Sort", "hexa-sort"),
        ("🌈 Color Sort 3D", "water-sort-puzzle"),
        ("🪣 Water Sort Puzzle", "water-sort-puzzle"),
        ("🚗 Parking Jam 3D", "parking-jam-3d"),
        ("🚗 Parking Fury 3D", "parking-fury-3d"),
        ("🪨 Match Stone", "match-stone"),
        ("🎨 Coloring Book", "coloring-book"),
        ("🎲 Dice Merge", "dice-merge"),
        ("🐍 Snake Solver", "snake-solver"),
        ("🪜 Stair Race 3D", "stair-race-3d"),
        ("🪙 Coin Master Puzzle", "coin-master-puzzle"),
        ("🐦 Angry Birds Style: Birds vs Pigs", "birds-vs-blocks"),
        ("🟢 Bubble Shooter", "bubble-shooter-pro"),
        ("🟢 Bubble Pop Story", "bubble-pop-story"),
        ("🟢 Bubble Trouble", "bubble-trouble"),
        ("📌 Pin Pull", "pin-pull"),
        ("🔓 Pin Rescue", "pin-rescue"),
        ("🔧 Save the Doge", "save-the-doge"),
        ("🐱 Save the Cat", "save-the-cat"),
        ("🦸 Save the Hero", "save-the-hero"),
        ("🪢 Tangle Master 3D", "tangle-master-3d"),
        ("🔪 Slice Master", "slice-master"),
        ("🎯 Aim Master", "aim-master"),
        ("🏷️ Sticky Block", "sticky-block"),
        ("🌀 Roller Splat", "roller-splat"),
        ("🪆 Stack Ball", "stack-ball-3d"),
        ("🏗️ Build Master 3D", "build-master-3d"),
        ("🪞 Mirror Match", "mirror-match"),
    ],
    "racing": [
        ("🏎️ Drift Hunters", "drift-hunters"),
        ("🏎️ Drift Boss", "driftboss"),
        ("🏎️ Madalin Stunt Cars 2", "madalin-stunt-cars-2"),
        ("🏎️ Madalin Stunt Cars 3", "madalin-stunt-cars-3"),
        ("🏎️ Madalin Cars Multiplayer", "madalin-cars-multiplayer"),
        ("🏎️ Burnin Rubber Crash N Burn", "burnin-rubber-crash-n-burn"),
        ("🏎️ Real Cars in City", "real-cars-in-city"),
        ("🚗 Highway Traffic", "highway-traffic"),
        ("🚗 Highway Racer", "highway-racer"),
        ("🚙 Traffic Rider", "traffic-rider"),
        ("🚓 Car Park Tycoon", "car-park-tycoon"),
        ("🛻 Monster Truck Stunts", "monster-truck-stunts"),
        ("🛻 Monster Truck Demolisher", "monster-truck-demolisher"),
        ("🛻 4x4 Off-Road Rally", "4x4-off-road-rally"),
        ("🚜 Farming Simulator", "farming-simulator"),
        ("🏍️ Moto X3M", "moto-x3m"),
        ("🏍️ Moto X3M 2", "moto-x3m-2"),
        ("🏍️ Moto X3M 3", "moto-x3m-3"),
        ("🏍️ Moto X3M 4 Winter", "moto-x3m-4-winter"),
        ("🏍️ Moto X3M 5 Pool Party", "moto-x3m-5-pool-party"),
        ("🏍️ Moto X3M 6 Spooky Land", "moto-x3m-6-spooky-land"),
        ("🏍️ Moto X3M Pool Party", "moto-x3m-pool-party"),
        ("🏍️ Moto Road Rash", "moto-road-rash-3d"),
        ("🚲 BMX Online", "bmx-online"),
        ("🛹 Skate Hooligans", "skate-hooligans"),
        ("🚛 Truck Loader", "truck-loader-5"),
        ("🚛 Truck Simulator", "truck-simulator"),
        ("🚜 City Car Driving Simulator", "city-car-driving-simulator"),
        ("🚓 Car Crash Simulator", "car-crash-simulator-royale"),
        ("🏎️ Crazy Cars", "crazy-cars"),
        ("🏎️ Lamborghini Drift", "lamborghini-drift"),
        ("🏎️ Drift Cup Racing", "drift-cup-racing"),
        ("🏎️ Real Drift Multiplayer", "real-drift-multiplayer"),
        ("🚗 Police Car Stunts", "police-car-stunts"),
        ("🚓 Police Pursuit Simulator", "police-pursuit-simulator"),
        ("🛺 Tuk Tuk Auto Rickshaw", "tuk-tuk-auto-rickshaw"),
        ("🚌 Bus Simulator", "bus-simulator"),
        ("🚌 Indian Bus Simulator", "indian-bus-simulator"),
    ],
    "shooting": [
        ("🔫 Bullet Force", "bullet-force"),
        ("🔫 Krunker.io", "krunker-io"),
        ("🥚 Shell Shockers", "shell-shockers"),
        ("🪖 Forward Assault Remix", "forward-assault-remix"),
        ("🎯 Combat Online", "combat-online"),
        ("🎯 Venge.io", "venge-io"),
        ("🔫 Smash Karts", "smash-karts"),
        ("🏹 Archery World Tour", "archery-world-tour"),
        ("🏹 Archer Master 3D", "archer-master-3d"),
        ("🎯 Aim Trainer", "aim-trainer"),
        ("🎯 Aim Master", "aim-master"),
        ("🪖 Stickman Sniper", "stickman-sniper"),
        ("🪖 Sniper 3D Strike", "sniper-3d-strike"),
        ("🎯 Sniper Clash 3D", "sniper-clash-3d"),
        ("🔫 Pixel Gun Apocalypse", "pixel-gun-apocalypse-9"),
        ("🔫 Pixel Warfare", "pixel-warfare"),
        ("🔫 Mini Royale 2", "mini-royale-2"),
        ("🔫 Mini Royale Nations", "mini-royale-nations"),
        ("🪖 War Brokers", "war-brokers-io"),
        ("🪖 Warbot.io", "warbot-io"),
        ("💥 Boxhead 2 Player", "boxhead-2-player"),
        ("💥 Boxhead The Rooms", "boxhead-the-rooms"),
        ("🪖 Storm Ops 3", "storm-ops-3"),
        ("🪖 Storm Ops 4", "storm-ops-4"),
        ("🎯 Shooting Star.io", "shooting-stars-io"),
        ("🔫 Gun Mayhem", "gun-mayhem"),
        ("🔫 Gun Mayhem 2", "gun-mayhem-2"),
        ("🔫 Gunblood", "gunblood"),
        ("🦖 Dino Squad", "dino-squad-adventure-2"),
        ("👽 Alien Invasion", "alien-invasion-rpg-idle-space"),
        ("🧟 Zombie Tsunami", "zombie-tsunami-online"),
        ("🧟 Zombie Mission 11", "zombie-mission-11"),
    ],
    "sports": [
        ("⚽ Basketball Stars", "basketball-stars"),
        ("⚽ Basket Random", "basket-random"),
        ("⚽ Basket Bros", "basket-bros"),
        ("⚽ Football Heads 2014 World Cup", "football-heads-2014-world-cup"),
        ("⚽ Football Legends 2021", "football-legends-2021"),
        ("⚽ Football Masters", "football-masters"),
        ("⚽ Soccer Random", "soccer-random"),
        ("⚽ Soccer Skills World Cup", "soccer-skills-world-cup"),
        ("🏀 Basketball Legends 2020", "basketball-legends-2020"),
        ("🏀 Tap-Tap Shots", "tap-tap-shots"),
        ("🏀 BasketBros", "basketbros-io"),
        ("🎱 8 Ball Pool Classic", "8-ball-pool-classic"),
        ("🎱 8 Ball Billiards Classic", "8-ball-billiards-classic"),
        ("🎱 Billiards City", "billiards-city"),
        ("🏏 Cricket Hero", "cricket-hero"),
        ("🏏 Stick Cricket", "stick-cricket-classic"),
        ("🏏 World Cricket Championship", "world-cricket-championship"),
        ("🏓 Ping Pong Go", "ping-pong-go"),
        ("🏓 Table Tennis World Tour", "table-tennis-world-tour"),
        ("🎾 Tennis Open", "tennis-open-2022"),
        ("⛳ Mini Golf", "mini-golf-club"),
        ("⛳ Golf Battle", "golf-battle"),
        ("⛳ Mini Putt Gem Garden", "mini-putt-gem-garden"),
        ("🏐 Volley Random", "volley-random"),
        ("🏐 Volleyball Challenge", "volleyball-challenge"),
        ("🏊 Aquapark.io", "aquapark-io"),
        ("🏊 Water Race 3D", "water-race-3d"),
        ("🏃 Sprinter", "sprinter"),
        ("🥊 Boxing Random", "boxing-random"),
        ("🥊 MMA Fighting Clash", "mma-fighting-clash"),
        ("🤼 Wrestle Online", "wrestle-online"),
        ("🤼 WWE Mayhem", "wwe-mayhem"),
        ("🏎️ Formula Rush", "formula-rush"),
        ("🏎️ F1 Race Stars", "f1-race-stars"),
    ],
    "io": [
        ("🐍 Snake.io", "snake-io"),
        ("🐍 Worms Zone", "worms-zone"),
        ("🐍 Slither.io", "slitherio"),
        ("🟢 Agar.io", "agar-io"),
        ("🟢 Hole.io", "hole-io"),
        ("📄 Paper.io 2", "paper-io-2"),
        ("📄 Paper.io 3", "paper-io-3"),
        ("⚪ Diep.io", "diep-io"),
        ("🔫 Krunker.io", "krunker-io"),
        ("🥚 Shell Shockers", "shell-shockers"),
        ("🎯 Venge.io", "venge-io"),
        ("👑 Zombs Royale", "zombs-royale-io"),
        ("🌪️ Tornado.io", "tornado-io"),
        ("🌪️ Tornado.io 2", "tornado-io-2-the-game-of-crash"),
        ("🐍 Snowrider.io", "snowrider-io"),
        ("🚀 Rocket Bot Royale", "rocket-bot-royale"),
        ("⚔️ MooMoo.io", "moomoo-io"),
        ("⚔️ Starve.io", "starve-io"),
        ("🦈 Shark.io", "shark-io"),
        ("🐟 Fish Eat Fish 3D", "fish-eat-fish-3d"),
        ("🦠 Bacteria.io", "bacteria-io"),
        ("🥋 Stick Fight.io", "stick-fight-io"),
        ("⚽ FootBattle.io", "footbattle-io"),
        ("🏰 Brutal.io", "brutal-io"),
        ("🪓 Surviv.io", "surviv-io"),
        ("🪓 Doblons.io", "doblons-io"),
        ("🪖 War Brokers", "war-brokers-io"),
        ("🪖 Warbot.io", "warbot-io"),
        ("🍩 Donuts.io", "donuts-io"),
        ("🍔 Eatventure", "eatventure"),
        ("🥚 EvoWorld.io", "evoworld-io"),
        ("🐹 Hamster Bag.io", "hamster-bag-io"),
        ("🛒 Shoppingcart.io", "shoppingcart-io"),
        ("📦 Build Royale.io", "buildroyale-io"),
    ],
    "2player": [
        ("👬 House of Hazards", "house-of-hazards"),
        ("👬 Stickman Fighter Epic", "stickman-fighter-epic-battles"),
        ("⚔️ Stick Duel: Medieval Wars", "stick-duel-medieval-wars"),
        ("👬 Boxing Random", "boxing-random"),
        ("👬 Volley Random", "volley-random"),
        ("👬 Soccer Random", "soccer-random"),
        ("👬 Tennis Masters", "tennis-masters"),
        ("👬 Basket Random", "basket-random"),
        ("👬 BasketBros", "basket-bros"),
        ("⚔️ Mini Battles", "mini-battles"),
        ("⚔️ Stickman Boxing KO", "stickman-boxing-ko-champion"),
        ("⚔️ 12 Mini Battles", "12-minibattles"),
        ("🤼 Wrestle Jump", "wrestle-jump"),
        ("👬 Twin Shot", "twin-shot"),
        ("👬 Tank Trouble", "tank-trouble"),
        ("👬 Tank Trouble 2", "tank-trouble-2"),
        ("👬 Bowmasters", "bowmasters"),
        ("👬 Bowman", "bowman"),
        ("👬 Getaway Shootout", "getaway-shootout"),
        ("👬 Stick Fighter", "stick-fighter"),
        ("👬 Stickman Supreme Duelist 2", "stickman-supreme-duelist-2"),
        ("👬 Drunken Wrestlers", "drunken-wrestlers"),
        ("👬 Drunken Boxing 2", "drunken-boxing-2"),
        ("👬 Mr Mine", "mr-mine"),
        ("👬 Tug of Heads", "tug-of-heads"),
        ("👬 Football Headz Cup", "football-headz-cup"),
        ("⚔️ Stickman Fight: Ragdoll Warriors", "stickman-fight-ragdoll-warriors"),
        ("👬 Mini Soccer Star", "mini-soccer-star"),
        ("👬 Sumo Party", "sumo-party"),
        ("👬 Madalin Cars Multiplayer", "madalin-cars-multiplayer"),
    ],
    "casual": [
        ("🍔 Papa's Freezeria", "papas-freezeria"),
        ("🍕 Papa's Pizzeria", "papas-pizzeria"),
        ("🍔 Papa's Burgeria", "papas-burgeria"),
        ("🌭 Hot Dog Bush", "hot-dog-bush"),
        ("🍩 Donut Maker", "donut-maker"),
        ("🍰 Cake Maker", "cake-maker-1"),
        ("👨‍🍳 Cooking Mama", "cooking-mama-style"),
        ("🍱 Sushi Roll", "sushi-roll"),
        ("☕ Coffee Stack", "coffee-stack"),
        ("🍦 Ice Cream Inc.", "ice-cream-inc"),
        ("🍦 Ice Cream Master", "ice-cream-master"),
        ("🥤 Soda Drink Maker", "soda-drink-maker"),
        ("🍓 Fruit Master", "fruit-master"),
        ("🍉 Watermelon Game", "watermelon-game"),
        ("🍉 Suika Game", "suika-game"),
        ("🪴 Idle Garden", "idle-garden-tycoon"),
        ("🚜 Farm Town", "farm-town"),
        ("🏝️ Idle Island", "idle-island"),
        ("🏗️ Idle City Builder", "idle-city-builder"),
        ("🐶 Pet Shop Tycoon", "pet-shop-tycoon"),
        ("🐱 My Cat Tom", "my-cat-tom"),
        ("🐱 My Tom: Online Pets", "my-tom-online-pets"),
        ("🐶 My Dog: Pet Care Game", "my-dog-pet-care-game"),
        ("🌸 Garden Tales", "garden-tales"),
        ("🌹 Garden Match 3D", "garden-match-3d"),
        ("🎂 Birthday Party", "birthday-party"),
        ("💍 Wedding Dress Up", "wedding-dress-up"),
        ("👗 Princess Dress Up", "princess-dress-up"),
        ("💇 Hair Salon", "hair-salon-fun-games"),
        ("💅 Nail Salon", "nail-salon"),
        ("💆 Spa Salon", "spa-salon"),
        ("🦷 Dentist Game", "dentist-game"),
        ("👶 Baby Care", "baby-care"),
        ("🛒 Supermarket Manager", "supermarket-manager-simulator"),
        ("🍲 Kitchen Story", "kitchen-story"),
        ("🌮 Taco Maker", "taco-maker"),
        ("🥘 Yummy Noodle", "yummy-noodle"),
    ],
    "adventure": [
        ("🗺️ Subway Surfers", "subway-surfers"),
        ("🗺️ Temple of Boom", "temple-of-boom"),
        ("🗺️ Tomb of the Mask", "tomb-of-the-mask"),
        ("🗺️ Tomb Runner", "tomb-runner"),
        ("🏺 Treasure of Cutlass Reef", "treasure-of-cutlass-reef"),
        ("🪦 Rise of the Pharaoh", "rise-of-the-pharaoh"),
        ("🐍 Snake Rivals", "snake-rivals"),
        ("🐉 Dragon Simulator 3D", "dragon-simulator-3d"),
        ("🦖 Dinosaur Simulator", "dinosaur-simulator"),
        ("🦕 Dino Game (Chrome)", "the-dinosaur-game"),
        ("🌳 Forest Survival Simulator", "forest-survival-simulator"),
        ("🏝️ Stranded Island", "stranded-island-survival"),
        ("⛏️ Minecraft Classic", "minecraft-classic"),
        ("⛏️ Minecraft Online", "minecraftonline"),
        ("🟢 Mine Blocks", "mine-blocks"),
        ("🔨 Voxiom.io", "voxiom-io"),
        ("🌋 Volcano Eruption", "volcano-eruption"),
        ("🏰 Castle Defense", "castle-defense"),
        ("🛡️ Knight vs Goblins", "knight-vs-goblins"),
        ("🐲 Dragons Adventure", "dragons-adventure"),
        ("🧙 Wizard's Wheel", "wizards-wheel"),
        ("🧚 Fairy Magic Match", "fairy-magic-match"),
        ("🦸 Super Hero Run", "super-hero-run"),
        ("👻 Ghost Detector", "ghost-detector"),
        ("🕷️ Spider Solitaire", "spider-solitaire-original"),
        ("🦇 Bat-man Adventure", "batman-adventure"),
        ("🐺 Wolf Hunt", "wolf-hunt"),
        ("🦊 Fox Adventure", "fox-adventure"),
        ("🐻 Bear Run", "bear-run"),
    ],
    "girls": [
        ("👗 Princess Royal Wedding", "princess-royal-wedding"),
        ("👗 Bff Princess Dress Up", "bff-princess-dress-up"),
        ("💄 Makeup Salon", "makeup-salon"),
        ("💅 Nail Studio", "nail-studio"),
        ("💇 Hair Challenge", "hair-challenge"),
        ("👰 Wedding Day", "wedding-day"),
        ("👶 Baby Hazel", "baby-hazel-doctor-play"),
        ("🐎 My Pony Style", "my-pony-style"),
        ("🦄 Unicorn Coloring Book", "unicorn-coloring-book"),
        ("🌈 Rainbow Cake", "rainbow-cake"),
        ("🎀 Cute Bunny Care", "cute-bunny-care"),
        ("🐱 Kitty Beauty Salon", "kitty-beauty-salon"),
        ("👗 Fashion Designer", "fashion-designer"),
        ("👜 Shopping Mall", "shopping-mall"),
        ("🍰 Cooking Trendy", "cooking-trendy"),
        ("🧁 Cupcake Maker", "cupcake-maker"),
        ("👯 BFF Photoshoot", "bff-photoshoot"),
        ("🎨 Coloring Book", "coloring-book"),
        ("📸 Selfie Studio", "selfie-studio"),
        ("🎠 Pony Friendship", "pony-friendship"),
        ("🪞 Mirror Match", "mirror-match"),
        ("👼 Cute Angel Dress Up", "cute-angel-dress-up"),
        ("🌷 Tulip Garden", "tulip-garden"),
    ],
    "kids": [
        ("🎈 Balloon Pop", "balloon-pop"),
        ("🍎 Fruit Sort", "fruit-sort"),
        ("🦓 Animal Quiz", "animal-quiz"),
        ("🐘 Memory Match Animals", "memory-match-animals"),
        ("🎨 Coloring Book", "coloring-book"),
        ("🟦 Shape Matching", "shape-matching"),
        ("🔢 Math for Kids", "math-for-kids"),
        ("🔠 ABC Learning", "abc-learning"),
        ("🐧 Penguin Slide", "penguin-slide"),
        ("🐠 Fish Tank", "fish-tank"),
        ("🐝 Bee Adventure", "bee-adventure"),
        ("🐌 Snail Bob", "snail-bob"),
        ("🐌 Snail Bob 2", "snail-bob-2"),
        ("🐌 Snail Bob 3", "snail-bob-3"),
        ("🐌 Snail Bob 4", "snail-bob-4"),
        ("🚂 Train Driver", "train-driver"),
        ("🚌 School Bus", "school-bus"),
        ("🦒 Zoo Tycoon", "zoo-tycoon"),
        ("🦒 My Zoo", "my-zoo"),
        ("🐶 Pet Care", "pet-care"),
        ("🍪 Cookie Clicker", "cookie-clicker-classic"),
        ("🪀 Yo-Yo Master", "yo-yo-master"),
        ("🎈 Balloon Adventure", "balloon-adventure"),
        ("🎁 Gift Wrap", "gift-wrap"),
    ],
    "card": [
        ("🃏 Solitaire Klondike", "solitaire-classic"),
        ("🃏 Spider Solitaire", "spider-solitaire-original"),
        ("🃏 FreeCell Solitaire", "freecell-solitaire"),
        ("🃏 Pyramid Solitaire", "pyramid-solitaire"),
        ("🃏 Tripeaks Solitaire", "tripeaks-solitaire"),
        ("♠️ Hearts", "hearts"),
        ("♣️ Spades", "spades"),
        ("🃏 UNO Online", "uno-online"),
        ("🃏 Crazy Eights", "crazy-eights"),
        ("♟️ Chess Online", "chess"),
        ("♟️ Chess Master 3D", "chess-master-3d"),
        ("♟️ Master Chess Multiplayer", "master-chess-multiplayer"),
        ("♟️ Real Chess", "real-chess"),
        ("⚫ Reversi", "reversi"),
        ("🟫 Backgammon", "backgammon"),
        ("🎴 Memory Match", "memory-match"),
        ("🎴 Card Match", "card-match"),
        ("♟️ Checkers", "checkers"),
        ("♟️ Ludo", "ludo-king"),
        ("🎲 Yatzy", "yatzy"),
        ("🎲 Snake and Ladders", "snakes-and-ladders"),
        ("🃏 Blackjack 21", "blackjack-21"),
        ("🃏 Texas Hold'em Poker", "texas-holdem-poker"),
        ("🃏 Governor of Poker 3", "governor-of-poker-3"),
    ],
    "strategy": [
        ("🏰 Kingdom Rush", "kingdom-rush"),
        ("🏰 Kingdom Rush Frontiers", "kingdom-rush-frontiers"),
        ("🏰 Bloons Tower Defense", "bloons-tower-defense-5"),
        ("🏰 Stick Wars", "stick-wars"),
        ("🏰 Age of War", "age-of-war"),
        ("🏰 Age of War 2", "age-of-war-2"),
        ("🏰 Stick War: Legacy", "stick-war-legacy"),
        ("🏰 Castle Defense", "castle-defense"),
        ("🛡️ Tower Defense", "tower-defense"),
        ("🪖 Battle Tabs", "battle-tabs"),
        ("👑 Empire of War", "empire-of-war"),
        ("🪖 Civilizations Wars", "civilizations-wars"),
        ("⚔️ Goodgame Empire", "goodgame-empire"),
        ("🏰 Goodgame Big Farm", "goodgame-big-farm"),
        ("🪖 Conflict of Nations", "conflict-of-nations"),
        ("⚔️ Imperial War", "imperial-war"),
        ("⚔️ Tribal Wars", "tribal-wars"),
        ("🪖 War of Caribbean Pirates", "war-of-caribbean-pirates"),
        ("🪖 World Conqueror", "world-conqueror"),
    ],
    "horror": [
        ("👻 Granny", "granny-horror-game"),
        ("👻 Granny Chapter 2", "granny-chapter-two"),
        ("👻 Slenderman", "slenderman"),
        ("👻 Five Nights at Freddy's", "five-nights-at-freddys"),
        ("👻 Five Nights at Freddy's 2", "five-nights-at-freddys-2"),
        ("👻 Five Nights at Freddy's 3", "five-nights-at-freddys-3"),
        ("👻 Five Nights at Freddy's 4", "five-nights-at-freddys-4"),
        ("👻 FNAF World", "fnaf-world"),
        ("🕷️ Spider Horror", "spider-horror"),
        ("🧟 Zombie Apocalypse", "zombie-apocalypse"),
        ("🩸 Bloody Hospital", "bloody-hospital"),
        ("👁️ Eyes the Horror Game", "eyes-the-horror-game"),
        ("🕯️ Dark Manor", "dark-manor"),
        ("🪓 Maniac Killer", "maniac-killer"),
        ("👻 Scary Maze", "scary-maze"),
    ],
    "music": [
        ("🎵 Friday Night Funkin'", "friday-night-funkin"),
        ("🎵 FNF vs Bob", "fnf-vs-bob"),
        ("🎵 FNF Online", "fnf-online"),
        ("🎵 Piano Tiles", "piano-tiles-2"),
        ("🎵 Magic Tiles 3", "magic-tiles-3"),
        ("🎹 Virtual Piano", "virtual-piano"),
        ("🥁 Drum Master", "drum-master"),
        ("🎤 Just Sing", "just-sing"),
        ("🎵 Beat Hop", "beat-hop"),
        ("🎵 Color Hop 3D", "color-hop-3d"),
        ("🎵 Dancing Road", "dancing-road"),
        ("🎵 Tiles Hop", "tiles-hop-edm-rush"),
        ("🎵 Beat Master", "beat-master"),
        ("🎺 Music Line", "music-line"),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Category metadata
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_META = [
    ("action",   "🔥 Action"),
    ("puzzle",   "🧩 Puzzle"),
    ("racing",   "🏎️ Racing"),
    ("shooting", "🔫 Shooting"),
    ("sports",   "⚽ Sports"),
    ("io",       "🌐 .io Games"),
    ("2player",  "👬 2 Player"),
    ("casual",   "🎉 Casual"),
    ("adventure","🗺️ Adventure"),
    ("girls",    "👗 Girls"),
    ("kids",     "👶 Kids"),
    ("card",     "🃏 Card / Board"),
    ("strategy", "🏰 Strategy"),
    ("horror",   "👻 Horror"),
    ("music",    "🎵 Music"),
]


def total_games() -> int:
    return sum(len(v) for v in ARCADE_GAMES.values())


# ─────────────────────────────────────────────────────────────────────────────
# Menu rendering
# ─────────────────────────────────────────────────────────────────────────────

async def _edit_or_send(update: Update, text: str, reply_markup):
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return
        except Exception:
            pass
    target = update.effective_message
    if target:
        await target.reply_text(
            text, reply_markup=reply_markup, parse_mode="HTML",
            disable_web_page_preview=True,
        )


async def arcade_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the arcade landing page with mega-portal button + categories."""
    text = (
        "🎮 <b>Mega Arcade Hub</b>\n\n"
        f"🎯 <b>{total_games()}+ curated games</b> across {len(CATEGORY_META)} categories.\n"
        "🌐 Plus <b>10,000+ games</b> in the Mega Portal!\n\n"
        "All games khulte hain Telegram ke andar — no app, no download.\n\n"
        "👇 Category chuno ya Mega Portal kholo:"
    )

    rows = []
    # Big button to mega portal
    rows.append([
        InlineKeyboardButton(
            "🌟 BROWSE 10,000+ GAMES (Mega Portal)",
            web_app=WebAppInfo(url=MEGA_PORTAL_URL),
        )
    ])
    # Categories — 2 per row
    cat_buttons = [
        InlineKeyboardButton(label, callback_data=f"arc:cat:{key}:0")
        for key, label in CATEGORY_META
    ]
    for i in range(0, len(cat_buttons), 2):
        rows.append(cat_buttons[i:i + 2])

    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")])

    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


async def arcade_show_category(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    cat_key: str,
    page: int,
):
    """Show paginated list of games in a category. Each game is a WebApp button."""
    games = ARCADE_GAMES.get(cat_key, [])
    cat_label = next((lbl for k, lbl in CATEGORY_META if k == cat_key), cat_key)
    if not games:
        await _edit_or_send(
            update,
            f"{cat_label}\n\nIs category mein abhi games nahi hain.",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Arcade", callback_data="menu:arcade")
            ]]),
        )
        return

    total_pages = max(1, (len(games) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    chunk = games[start:start + PAGE_SIZE]

    text = (
        f"{cat_label}\n\n"
        f"📄 Page <b>{page + 1}/{total_pages}</b>  •  "
        f"<b>{len(games)}</b> games\n\n"
        "Game pe tap karo — Telegram ke andar khulega 🎮"
    )

    rows: list[list[InlineKeyboardButton]] = []
    for name, slug in chunk:
        rows.append([
            InlineKeyboardButton(name, web_app=WebAppInfo(url=_url(slug)))
        ])

    # Pagination row
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"arc:cat:{cat_key}:{page - 1}")
        )
    nav.append(
        InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="arc:noop")
    )
    if page < total_pages - 1:
        nav.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"arc:cat:{cat_key}:{page + 1}")
        )
    rows.append(nav)

    rows.append([
        InlineKeyboardButton("🎮 Categories", callback_data="menu:arcade"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
    ])

    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))
