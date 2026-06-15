# SaaS Telegram Bot Platform

Платформа для продажи доступа в Telegram-группы и каналы. Один бот обслуживает множество владельцев групп и каналов.

## Run & Operate

- `cd bot && docker-compose up -d` — запустить всё (бот + PostgreSQL + Redis)
- `docker-compose logs -f bot` — смотреть логи бота
- `docker-compose exec bot alembic upgrade head` — применить миграции
- `docker-compose exec bot alembic revision --autogenerate -m "description"` — создать миграцию
- `docker-compose down` — остановить

## Stack

- Python 3.12, aiogram 3.x (Telegram Bot framework)
- PostgreSQL + SQLAlchemy (async) + Alembic migrations
- Redis — FSM storage (состояния диалогов)
- Docker + Docker Compose
- pydantic-settings для конфигурации через .env

## Where things live

- `bot/` — весь проект Telegram-бота
- `bot/app/handlers/` — обработчики: start, language, user, admin, superadmin, chat, receipt
- `bot/app/models/` — SQLAlchemy модели: User, Admin, Community, Subscription, Payment
- `bot/app/repositories/` — репозитории (data access layer)
- `bot/app/keyboards/` — клавиатуры для каждой роли
- `bot/app/locales/*.json` — переводы (ru, en, kg, kz, uz)
- `bot/app/middlewares/` — DB сессия и авто-загрузка пользователя
- `bot/main.py` — точка входа
- `bot/.env.example` — шаблон переменных окружения

## Architecture decisions

- **Contract-first roles**: Роль определяется в middleware и пробрасывается в хендлеры через `data["db_admin"]`, `data["is_superadmin"]`
- **Auto-expire subscriptions**: Фоновая задача каждый час помечает истёкшие подписки
- **Semi-automatic payments**: Чеки от пользователей → пересылаются adminu с кнопками Confirm/Reject
- **Таблицы создаются автоматически** при старте через `Base.metadata.create_all` (без миграций для первого запуска)
- **Мультиязычность**: Все строки в `app/locales/*.json`, загружаются один раз при старте, key-based lookup с fallback на `ru`

## Product

- **Пользователь**: покупает доступ в группы через бот, загружает чек
- **Admin сообщества**: подключает группы/каналы, создаёт тарифы, получает чеки и подтверждает оплату
- **Супер-admin**: управляет всеми adminами, видит общую статистику, выдаёт пробные периоды

## User preferences

- Язык: русский (проект для СНГ-рынка)
- Валюты: KGS, KZT, RUB, UZS, USD, EUR

## Gotchas

- **BOT_TOKEN** и **SUPERADMIN_IDS** обязательны в `.env` перед запуском
- Бот должен быть **администратором** в группе/канале с правами удаления сообщений
- Redis нужен для FSM — без него состояния диалогов не сохраняются
- `SUPERADMIN_IDS` — через запятую, если несколько: `123456789,987654321`

## Поinters

- `bot/README.md` — полная инструкция по запуску и использованию
- [@BotFather](https://t.me/BotFather) — для получения BOT_TOKEN
- [@userinfobot](https://t.me/userinfobot) — для получения своего Telegram ID
