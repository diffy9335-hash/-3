"""Игровые константы MVP: постройки, войска, формы правления, нации."""

# --- Формы правления: бонусы в % (+) / штрафы (-) ---
GOVERNMENTS = {
    "democracy":  {"name": "Демократия",  "economy": +15, "army": -10, "science": +10, "stability": +5},
    "monarchy":   {"name": "Монархия",    "economy": +5,  "loyalty": +15, "science": -10, "stability": 0},
    "dictatorship": {"name": "Диктатура", "economy": -5,  "army": +20, "science": 0,   "stability": -15},
    "theocracy":  {"name": "Теократия",   "culture": +15, "science": -15, "stability": +5, "army": 0},
    "republic":   {"name": "Республика",  "economy": +5,  "army": +5,  "science": +5,  "stability": +5},
}

# --- Начальные нации (10 штук, вымышленные) ---
NATIONS = [
    {"name": "Альдерон",  "code": "ALD", "flag": "🦅", "bonus_economy": 10, "bonus_army": 0,  "bonus_science": 5,  "bonus_stability": 5},
    {"name": "Валдория",  "code": "VAL", "flag": "🐺", "bonus_economy": 0,  "bonus_army": 15, "bonus_science": 0,  "bonus_stability": 0},
    {"name": "Нордгард",  "code": "NOR", "flag": "❄️", "bonus_economy": 5,  "bonus_army": 5,  "bonus_science": 0,  "bonus_stability": 10},
    {"name": "Солария",   "code": "SOL", "flag": "☀️", "bonus_economy": 5,  "bonus_army": 0,  "bonus_science": 15, "bonus_stability": 0},
    {"name": "Драконья",  "code": "DRA", "flag": "🐉", "bonus_economy": 0,  "bonus_army": 10, "bonus_science": 0,  "bonus_stability": 5},
    {"name": "Мистраль",  "code": "MIS", "flag": "🌊", "bonus_economy": 10, "bonus_army": 0,  "bonus_science": 5,  "bonus_stability": 0},
    {"name": "Террафорд", "code": "TER", "flag": "🌿", "bonus_economy": 15, "bonus_army": -5, "bonus_science": 0,  "bonus_stability": 5},
    {"name": "Кобальтия", "code": "KOB", "flag": "⚙️", "bonus_economy": 10, "bonus_army": 0,  "bonus_science": 10, "bonus_stability": -5},
    {"name": "Астралия",  "code": "AST", "flag": "🌌", "bonus_economy": 0,  "bonus_army": -5, "bonus_science": 20, "bonus_stability": 0},
    {"name": "Громхольм", "code": "GRH", "flag": "⛈️", "bonus_economy": 0,  "bonus_army": 20, "bonus_science": -5, "bonus_stability": -5},
]

# --- Постройки: стоимость и длительность по уровню ---
BUILDINGS = {
    "farm":       {"name": "Ферма",           "emoji": "🌾", "base_cost": 100, "cost_type": "money",  "hours": 1, "produces": {"food": 50}},
    "mine":       {"name": "Шахта",           "emoji": "⛏️", "base_cost": 150, "cost_type": "money",  "hours": 2, "produces": {"iron": 20}},
    "oil_rig":    {"name": "Нефтевышка",      "emoji": "🛢️", "base_cost": 300, "cost_type": "money",  "hours": 3, "produces": {"oil": 10}},
    "factory":    {"name": "Завод",           "emoji": "🏭", "base_cost": 250, "cost_type": "money",  "hours": 2, "produces": {"industry": 15, "energy": -5}},
    "power_plant":{"name": "Электростанция",  "emoji": "⚡", "base_cost": 200, "cost_type": "money",  "hours": 2, "produces": {"energy": 30}},
    "barracks":   {"name": "Казармы",         "emoji": "🎖️", "base_cost": 180, "cost_type": "money",  "hours": 1, "produces": {}},
    "bank":       {"name": "Банк",            "emoji": "🏦", "base_cost": 400, "cost_type": "money",  "hours": 3, "produces": {"money": 60}},
    "university": {"name": "Университет",     "emoji": "🎓", "base_cost": 350, "cost_type": "money",  "hours": 3, "produces": {"science": 25}},
    "wall":       {"name": "Городская стена", "emoji": "🧱", "base_cost": 300, "cost_type": "iron",   "hours": 4, "produces": {}},
}

# --- Войска: атака / защита / HP / стоимость (деньги+железо+еда) / содержание в час ---
UNITS = {
    "infantry":  {"name": "Пехота",    "emoji": "🪖", "attack": 10, "defense": 15, "hp": 100, "cost": {"money": 50,  "iron": 5,   "food": 10}, "upkeep": 1},
    "archers":   {"name": "Стрелки",   "emoji": "🏹", "attack": 14, "defense": 8,  "hp": 70,  "cost": {"money": 70,  "iron": 5,   "food": 10}, "upkeep": 1},
    "cavalry":   {"name": "Кавалерия", "emoji": "🐎", "attack": 25, "defense": 15, "hp": 150, "cost": {"money": 150, "iron": 10,  "food": 30}, "upkeep": 3},
    "artillery": {"name": "Артиллерия","emoji": "💣", "attack": 40, "defense": 5,  "hp": 80,  "cost": {"money": 300, "iron": 40,  "food": 5},  "upkeep": 5},
}

# --- NPC-противники для боёв MVP ---
NPC_TARGETS = {
    "bandits":  {"name": "Бандиты",   "emoji": "🏴‍☠️", "power": 80,   "loot": {"money": 120, "food": 40}},
    "raiders":  {"name": "Рейдеры",   "emoji": "⚔️",  "power": 250,  "loot": {"money": 400, "iron": 60}},
    "warlord":  {"name": "Военачальник","emoji": "👹", "power": 700,  "loot": {"money": 1500, "oil": 40}},
}

BUILD_MAX_LEVEL = 10
MORALE_BASE = 1.0


# --- Рейтинги (/top) ---
TOP_LIMIT = 10

# Вес ресурса в «богатстве» (население не считаем — это не накопление)
RESOURCE_WEIGHTS = {"money": 1, "food": 1, "iron": 2, "oil": 3,
                    "science": 2, "energy": 1, "industry": 2}

# Достижения считаются по накопительным метрикам (не убывают при тратах/потерях).
# stat — поле PlayerStats из bot/services/rating_service.py
ACHIEVEMENTS = [
    {"key": "first_blood", "emoji": "🗡️", "name": "Первая кровь",   "desc": "выиграть 1 бой",              "stat": "wins",      "goal": 1},
    {"key": "veteran",     "emoji": "🎖️", "name": "Ветеран",        "desc": "выиграть 10 боёв",            "stat": "wins",      "goal": 10},
    {"key": "pvp_winner",  "emoji": "⚔️", "name": "Полководец",     "desc": "победить игрока в атаке",     "stat": "pvp_wins",  "goal": 1},
    {"key": "defender",    "emoji": "🛡️", "name": "Несокрушимый",   "desc": "отбить 3 атаки",              "stat": "defends",   "goal": 3},
    {"key": "conqueror",   "emoji": "🚩", "name": "Завоеватель",    "desc": "владеть 5 регионами",         "stat": "regions",   "goal": 5},
    {"key": "emperor",     "emoji": "👑", "name": "Император",      "desc": "владеть 25 регионами",        "stat": "regions",   "goal": 25},
    {"key": "builder",     "emoji": "🏗️", "name": "Строитель",      "desc": "построить 5 зданий",          "stat": "buildings", "goal": 5},
    {"key": "fortress",    "emoji": "🧱", "name": "Крепость",       "desc": "стена 5 уровня",              "stat": "wall",      "goal": 5},
]

# --- Админка ---
ADMIN_RESOURCES = ("money", "food", "iron", "oil", "science", "population", "energy", "industry")
ADMIN_MAX_GRANT = 1_000_000_000   # защита от опечаток при выдаче
ADMIN_LOG_DEFAULT = 10
ADMIN_LOG_MAX = 30
