#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример конфигурационного файла для Outline VPN Bot
Переименуйте этот файл в config.py и настройте его параметры
"""

# Конфигурация Telegram бота
API_TOKEN = 'ваш_токен_от_BotFather'  # Получите токен у @BotFather в Telegram

# ID администраторов (список целых чисел)
# Эти пользователи могут управлять всеми ключами и имеют дополнительные права
ADMIN_IDS = [123456789, 987654321]

# Ограничения на количество ключей
MAX_KEYS_PER_USER = 1  # Максимальное количество ключей для обычных пользователей
MAX_KEYS_PER_ADMIN = 10  # Максимальное количество ключей для администраторов

# Язык по умолчанию (ru или en)
LANGUAGE = 'ru'

# URL API Outline сервера
# Формат: https://server-ip:port/api-token
# Пример: https://1.2.3.4:8080/KN62fLAaqLnHmXYLTP1XLw
OUTLINE_API_URL = 'https://your-server-ip:port/api-token'

# Путь к базе данных SQLite
DB_PATH = 'outline_bot.db' 