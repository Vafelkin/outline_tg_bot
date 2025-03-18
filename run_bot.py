#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный файл для запуска бота с кнопками для управления ключами Outline VPN
"""

import logging
import sys
import telebot
import config
from database import Database
import outline_api

# Настройка логирования в файл и консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('run_bot')

# Создаем экземпляры бота и базы данных
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
db = Database(config.DB_FILE)
outline = outline_api.OutlineAPI(config.OUTLINE_API_URL)

# Экспортируем экземпляры для использования в других модулях
import key_manager
key_manager.bot = bot
key_manager.db = db
key_manager.outline = outline

# Регистрируем обработчики сообщений
key_manager.register_handlers()

# Импортируем все модули
try:
    logger.info("Importing modules...")
    
    # Модули с обработчиками
    import key_manager_paid
    import key_manager_limit
    import key_manager_delete
    import key_manager_admin
    import key_manager_messages
    
    # Передаем экземпляры в другие модули
    key_manager_paid.bot = bot
    key_manager_paid.db = db
    
    key_manager_limit.bot = bot
    key_manager_limit.db = db
    key_manager_limit.outline = outline
    key_manager_limit.register_handlers()
    
    key_manager_delete.bot = bot
    key_manager_delete.db = db
    
    key_manager_admin.bot = bot
    key_manager_admin.db = db
    
    key_manager_messages.bot = bot
    key_manager_messages.db = db
    
    logger.info("All modules imported successfully")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting the bot...")
    try:
        # Запускаем бот
        logger.info("Bot is running. Press Ctrl+C to stop.")
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1) 