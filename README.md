# Telegram-бот для сбора заявок

Демонстрационный бот на Python: он спрашивает данные клиента, показывает итог, сохраняет подтверждённую заявку в SQLite и уведомляет администратора.

## Перед началом

Нужны Python 3.10+, аккаунт Telegram и токен бота от `@BotFather`.

## Запуск в Windows

1. Откройте PowerShell в папке проекта.
2. Создайте виртуальное окружение:

   ```powershell
   python -m venv .venv
   ```

3. Активируйте его:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Установите библиотеки:

   ```powershell
   pip install -r requirements.txt
   ```

5. Скопируйте файл `.env.example`, переименуйте копию в `.env`.
6. В `.env` заполните:
   - `BOT_TOKEN` — токен от `@BotFather`;
   - `ADMIN_CHAT_ID` — ваш числовой Telegram ID. Его можно узнать через `@userinfobot`.
7. Откройте диалог с вашим ботом в Telegram и нажмите **Start**. Без этого Telegram не позволит боту написать администратору.
8. Запустите:

   ```powershell
   python main.py
   ```

Отправьте боту `/start` и заполните тестовую заявку.

## Где лежат заявки

При первом запуске появляется файл `data/leads.db`. Это локальная SQLite-база. Таблица `leads` содержит Telegram ID, username, имя, телефон, страну, комментарий и время создания в UTC.

## Команды

- `/start` — начать заявку.
- `/cancel` — отменить заполнение.
- `/leads` — последние 10 заявок; доступно только администратору.
- `/stats` — количество заявок всего и за текущий день UTC; доступно только администратору.

## Важно

Файл `.env` содержит секретный токен и исключён из Git. Не публикуйте его.

## Публикация в GitHub

Перед загрузкой проекта убедитесь, что файл `.env` не выбран для добавления: в нём находится токен бота. Файл `data/leads.db` тоже исключён, так как содержит персональные данные тестовых и реальных заявок.

В терминале в папке проекта выполните:

```powershell
git add .
git commit -m "Create Telegram lead bot"
```

Затем на GitHub создайте новый пустой репозиторий, например `telegram-lead-bot`. GitHub покажет команды для отправки локального проекта. Обычно это:

```powershell
git branch -M main
git remote add origin https://github.com/ВАШ-ЛОГИН/telegram-lead-bot.git
git push -u origin main
```

Не включайте при публикации токен, файл `.env` или базу `leads.db`.

## Для портфолио

В описании репозитория можно указать: «Telegram-бот на Python для сбора клиентских заявок: пошаговая анкета, подтверждение, SQLite и уведомления администратору».

Перед публикацией сделайте скриншоты диалога с ботом и просмотра таблицы SQLite. Если на них есть реальные имя, телефон, Telegram ID или токен, замените их тестовыми данными или обрежьте изображение.

## Управление ботом на сервере

После развёртывания на Ubuntu бот работает как системная служба `telegram-lead-bot`. Эти команды нужно выполнять в консоли сервера от пользователя `root`.

Проверить состояние бота:

```bash
systemctl status telegram-lead-bot
```

Перезапустить бота после изменения настроек или обновления кода:

```bash
systemctl restart telegram-lead-bot
```

Посмотреть текущие логи (для выхода нажмите `Ctrl + C`):

```bash
journalctl -u telegram-lead-bot -f
```

Остановить бота:

```bash
systemctl stop telegram-lead-bot
```

Запустить остановленного бота:

```bash
systemctl start telegram-lead-bot
```

## Резервные копии заявок

Скрипт `scripts/backup_database.py` создаёт корректную копию SQLite-базы через встроенный механизм SQLite, хранит её в папке `backups/` и автоматически оставляет только 14 последних копий. Папка с копиями не попадает в GitHub.

Чтобы создать резервную копию вручную на сервере:

```bash
cd /home/leadbot/telegram-lead-bot
.venv/bin/python scripts/backup_database.py
```

Чтобы включить ежедневный автоматический бэкап в 03:30 UTC, выполните на сервере от пользователя `root`:

```bash
cp /home/leadbot/telegram-lead-bot/deploy/systemd/telegram-lead-bot-backup.service /etc/systemd/system/
cp /home/leadbot/telegram-lead-bot/deploy/systemd/telegram-lead-bot-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now telegram-lead-bot-backup.timer
```

Проверить расписание бэкапов:

```bash
systemctl list-timers telegram-lead-bot-backup.timer
```
