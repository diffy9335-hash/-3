# Военная стратегия — Telegram MMO (MVP)

## Запуск (Docker)
1. Создайте бота у @BotFather и скопируйте токен.
2. `cp .env.example .env`, впишите `BOT_TOKEN` и свой Telegram ID в `ADMIN_IDS=[...]`
   (ID можно узнать у @userinfobot).
3. `docker compose up --build -d`, логи: `docker compose logs -f bot`.
   Миграции и начальные данные (нации, карта 20×20) применяются автоматически.

Без Docker: Python 3.11+, запущенный PostgreSQL, `pip install -r requirements.txt`,
`DATABASE_URL` на localhost в `.env`, затем `python main.py`. Redis не нужен (`USE_REDIS=false`).

## Команды игрока
| Команда | Что делает |
|---|---|
| `/start` | регистрация, выбор нации, главное меню |
| `/profile` | профиль: уровень, стабильность, деньги |
| `/economy` | ресурсы и постройки |
| `/build` | постройка/улучшение зданий |
| `/daily` | ежедневный бонус |
| `/army` | армия и найм войск |
| `/attack` | бой с NPC (бандиты, рейдеры, военачальник) |
| `/war <id>` | атака на другого игрока по Telegram ID |
| `/battle_log` | последние 5 боёв |
| `/map` | карта мира 20×20 |
| `/region <id>` | информация о регионе (0–399) |
| `/claim <id>` | захват нейтрального региона |
| `/top` | рейтинги: ресурсы / армия / территории / достижения |
| `/stats` | число игроков и ваши победы |
| `/settings` | заглушка |

## Админ-панель (только `ADMIN_IDS`)
| Команда | Что делает |
|---|---|
| `/admin` | справка и сводка |
| `/admin give <id> <ресурс> <кол-во>` | выдать ресурс (отрицательное число — забрать, не ниже 0) |
| `/admin ban <id> [причина]` | забанить (админов банить нельзя) |
| `/admin unban <id>` | разбанить |
| `/admin log [id\|all] [N]` | последние записи audit_log (по умолчанию 10, максимум 30) |

Ресурсы: money, food, iron, oil, science, population, energy, industry.
Все админ-действия пишутся в audit_log (`admin_give`, `admin_ban`, `admin_unban`).
