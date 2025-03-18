# Outline VPN Bot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue)
![Outline](https://img.shields.io/badge/Outline-VPN-orange)
![License](https://img.shields.io/badge/License-MIT-green)

Телеграм-бот для управления Outline VPN сервером. Позволяет легко и удобно создавать ключи доступа, устанавливать лимиты трафика и управлять доступом пользователей к VPN.

## Возможности

- 🔑 Создание и управление ключами доступа к VPN серверу
- 📈 Отслеживание использования трафика по каждому ключу
- 📅 Установка срока действия ключей
- 📊 Установка лимитов трафика для каждого ключа
- 👥 Разделение прав доступа (администраторы/пользователи)
- 🌐 Мультиязычный интерфейс (Русский/Английский)
- 📱 Удобный интерфейс через Telegram

## Настройка

### Предварительные требования

- Python 3.8+
- Telegram Bot API Token
- Outline VPN сервер

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Vafelkin/outline_tg_bot.git
   cd outline_tg_bot
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Создайте файл `config.py` с вашими настройками:
   ```python
   # Конфигурация Telegram бота
   API_TOKEN = 'ваш_токен_от_BotFather'
   
   # ID администраторов (могут управлять всеми ключами)
   ADMIN_IDS = [123456789, 987654321]
   
   # Ограничения на количество ключей
   MAX_KEYS_PER_USER = 1  # Обычные пользователи
   MAX_KEYS_PER_ADMIN = 10  # Администраторы
   
   # Язык по умолчанию (ru или en)
   LANGUAGE = 'ru'
   
   # URL API Outline сервера
   OUTLINE_API_URL = 'https://your-server-ip:port/api-token'
   
   # Путь к БД SQLite
   DB_PATH = 'outline_bot.db'
   ```

4. Запустите бота:
   ```bash
   python run_bot.py
   ```

## Использование

1. Начните общение с ботом командой `/start`
2. Используйте встроенные кнопки для управления ключами:
   - Создание ключа
   - Просмотр своих ключей
   - Установка лимита трафика (только администраторы)
   - Установка срока действия ключа (только администраторы)

## Структура проекта

- `run_bot.py` - Основной файл для запуска бота
- `key_manager.py` - Модуль для управления ключами
- `outline_api.py` - Модуль для работы с API Outline сервера
- `database.py` - Модуль для работы с БД
- `messages.py` - Модуль с сообщениями на разных языках
- `utils.py` - Вспомогательные функции

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности смотрите в файле LICENSE.

## Авторы

- [Nikolay](https://github.com/Vafelkin)

## Благодарности

- [Проект Outline VPN](https://getoutline.org/) за отличный инструмент для создания VPN серверов
- [PyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) за удобную библиотеку для создания Telegram ботов 