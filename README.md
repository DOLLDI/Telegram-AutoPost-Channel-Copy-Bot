# Telegram AutoPost Channel Copy Bot

Telegram-бот и userbot для автоматического копирования постов из одного Telegram-канала в другой.

Проект позволяет:

- автоматически публиковать новые посты из исходного канала;
- отправлять посты администратору на подтверждение перед публикацией;
- добавлять уникальную ссылку к каждому посту;
- добавлять кнопку перехода к оригинальному посту;
- управлять настройками через Telegram-меню.

## Скриншоты

![Главное меню](Screenshots/Screenshot%202026-10-08%20232534.png)

![Настройки](Screenshots/Screenshot%202026-10-08%20232600.png)

![Автопостинг](Screenshots/Screenshot%202026-10-08%20232617.png)

## Возможности

- Автопостинг из source-канала в target-канал.
- Ручная модерация постов через кнопки подтверждения и отклонения.
- Работа с текстом, фото, видео и документами.
- Кнопка "Оригинальный пост" для ссылки на источник.
- Настройка каналов и пользовательской ссылки через Telegram.
- Хранение настроек и истории публикаций в SQLite.

## Требования

- Python 3.10+
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)
- Telegram API ID и API HASH с [my.telegram.org](https://my.telegram.org)
- Доступ userbot-аккаунта к исходному каналу
- Права администратора для бота в канале назначения

## Установка

```bash
git clone https://github.com/DOLLDI/Telegram-AutoPost-Channel-Copy-Bot.git
cd Telegram-AutoPost-Channel-Copy-Bot
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Настройка

Создайте локальные файлы конфигурации из примеров:

```bash
copy .env.example .env
copy .env.userbot.example .env.userbot
```

Для Linux/macOS:

```bash
cp .env.example .env
cp .env.userbot.example .env.userbot
```

Заполните значения:

```env
BOT_TOKEN=1234567890:replace_with_bot_token
ADMIN_ID=123456789
SOURCE_CHANNEL_ID=-1001234567890
TARGET_CHANNEL_ID=-1009876543210
DATABASE_PATH=data/bot.db
```

В `.env.userbot` дополнительно нужны:

```env
API_ID=123456
API_HASH=replace_with_api_hash
USER_SESSION=userbot
CUSTOM_LINK=
```

Файлы `.env`, `.env.userbot`, `.session` и база данных не публикуются в GitHub.

## Где взять данные

### BOT_TOKEN

1. Откройте Telegram.
2. Найдите [@BotFather](https://t.me/BotFather).
3. Выполните команду `/newbot`.
4. Следуйте инструкциям и вставьте полученный токен в `.env` и `.env.userbot`.

### ADMIN_ID

1. Откройте [@userinfobot](https://t.me/userinfobot).
2. Нажмите Start.
3. Скопируйте свой Telegram ID.

### SOURCE_CHANNEL_ID и TARGET_CHANNEL_ID

ID канала обычно выглядит так:

```text
-1001234567890
```

Его можно получить через ботов для извлечения ID, например переслав сообщение из канала в такого бота.

### API_ID и API_HASH

1. Перейдите на [my.telegram.org](https://my.telegram.org).
2. Войдите по номеру телефона.
3. Откройте раздел API development tools.
4. Создайте приложение и скопируйте API ID и API HASH.

## Первый запуск userbot

Userbot создаёт `.session`-файл при первой авторизации:

```bash
python userbot_main.py
```

Telegram попросит:

- номер телефона;
- код подтверждения;
- пароль 2FA, если он включён.

`.session`-файл даёт доступ к Telegram-аккаунту, поэтому не передавайте его третьим лицам и не публикуйте в GitHub.

## Запуск

Проект состоит из двух процессов, их нужно запускать в отдельных терминалах.

Терминал 1:

```bash
python main.py
```

Терминал 2:

```bash
python userbot_main.py
```

После запуска откройте бота в Telegram и используйте меню управления.

## Режимы работы

### Автопостинг включён

Новые посты из исходного канала публикуются в канал назначения автоматически.

### Автопостинг выключен

Новый пост приходит администратору. Администратор может подтвердить или отклонить публикацию.

## Структура проекта

```text
.
├── main.py                 # запуск aiogram-бота
├── userbot_main.py         # запуск Telethon userbot
├── src/
│   ├── config.py           # загрузка настроек
│   ├── database/           # модели и SQLite
│   ├── handlers/           # Telegram-команды и callbacks
│   ├── keyboards/          # клавиатуры
│   └── userbot/            # Telethon-клиент и обработка постов
├── data/                   # локальная база данных
├── Screenshots/            # скриншоты для README
└── requirements.txt
```

## Частые проблемы

- Бот не публикует посты: проверьте права администратора в канале назначения.
- Посты не приходят: проверьте `SOURCE_CHANNEL_ID` и доступ userbot-аккаунта к исходному каналу.
- Ошибка подключения: проверьте `.env`, `.env.userbot`, `API_ID`, `API_HASH` и `BOT_TOKEN`.
- Не работает автопостинг: включите его в меню Telegram-бота.

## Безопасность

Не публикуйте:

- `.env`;
- `.env.userbot`;
- `.session`;
- `data/bot.db`;
- реальные Telegram-токены и API-ключи.
