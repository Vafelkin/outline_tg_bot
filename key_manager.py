#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной модуль для управления ключами Outline VPN
"""

import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple

from telebot import types
import config
import outline_api as outline_module
from messages import get_message
from utils import format_timestamp, gb_to_bytes, format_bytes

# Настройка логирования
logger = logging.getLogger('key_manager')

# Эти переменные будут установлены из run_bot.py
bot = None
db = None
outline = None

# Глобальное хранилище состояний пользователей
user_states: Dict[int, Dict[str, Any]] = {}

# Вспомогательные функции, не зависящие от бота

def get_user_language(user_id: int) -> str:
    """
    Получить язык пользователя
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        str: Код языка (ru или en)
    """
    user = db.get_user(user_id)
    if user and user.get('language_code'):
        return user['language_code'].split('-')[0]
    return config.LANGUAGE

def get_main_keyboard(user_id: int, lang: str) -> types.InlineKeyboardMarkup:
    """
    Создать основную клавиатуру
    
    Args:
        user_id (int): ID пользователя
        lang (str): Код языка
        
    Returns:
        types.InlineKeyboardMarkup: Клавиатура
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    # Кнопка создания ключа
    create_button = types.InlineKeyboardButton(
        get_message('create_key_button', lang),
        callback_data='create_key'
    )
    
    # Кнопка просмотра своих ключей
    my_keys_button = types.InlineKeyboardButton(
        get_message('my_keys_button', lang),
        callback_data='my_keys'
    )
    
    # Добавляем кнопки
    keyboard.add(create_button, my_keys_button)
    
    # Если пользователь админ, добавляем кнопку просмотра всех ключей
    if db.is_admin(user_id):
        all_keys_button = types.InlineKeyboardButton(
            get_message('all_keys_button', lang),
            callback_data='all_keys'
        )
        keyboard.add(all_keys_button)
    
    return keyboard

def format_data_limit_with_usage(used_bytes: int, limit_bytes: int, lang: str) -> str:
    """
    Форматирует данные о потреблении и лимите трафика.
    
    Args:
        used_bytes (int): Использовано байт
        limit_bytes (int): Лимит в байтах
        lang (str): Код языка
        
    Returns:
        str: Отформатированное представление трафика
    """
    logger.info(f"format_data_limit_with_usage вызван с used_bytes={used_bytes}, limit_bytes={limit_bytes}")
    
    # Конвертируем байты в ГБ используя правило 1 ГБ = 1,000,000,000 байтов
    used_gb = round(used_bytes / 1000000000, 1)
    
    # Если лимита нет, показываем только использование
    if not limit_bytes or limit_bytes <= 0:
        logger.info(f"Нет лимита, возвращаем только использование: {used_gb} GB")
        return f"{used_gb} GB"
    
    # Конвертируем лимит в ГБ
    limit_gb = round(limit_bytes / 1000000000, 1)
    
    # Формат: "Использовано / Лимит"
    result = f"{used_gb} GB / {limit_gb} GB"
    logger.info(f"Возвращаем результат использование/лимит: {result}")
    return result

def format_key_info(key: Dict[str, Any], lang: str) -> str:
    """
    Форматирует информацию о ключе
    
    Args:
        key (dict): Данные ключа
        lang (str): Код языка
        
    Returns:
        str: Отформатированная информация
    """
    # Перед отображением информации синхронизируем данные с сервером
    key_id = key.get('key_id')
    data_limit = 0  # Лимит данных
    
    logger.info(f"format_key_info вызван для ключа {key_id}")
    logger.debug(f"Исходные данные ключа: {key}")
    
    if key_id:
        try:
            # Получаем актуальные данные с сервера
            server_key = outline.get_access_key(key_id)
            logger.info(f"Данные ключа с сервера получены: {server_key}")
            
            # Получаем лимит данных с сервера
            if server_key and 'dataLimit' in server_key and 'bytes' in server_key['dataLimit']:
                data_limit = server_key['dataLimit']['bytes']
                # Используем правило 1 ГБ = 1,000,000,000 байтов
                logger.info(f"Лимит трафика с сервера: {data_limit} байт ({round(data_limit/1000000000, 2)} ГБ)")
            else:
                logger.info(f"Лимит трафика отсутствует в данных сервера")
            
            # Получаем актуальное использование трафика с сервера
            data_usage = outline.get_key_data_usage(key_id)
            # Используем правило 1 ГБ = 1,000,000,000 байтов
            logger.info(f"Использование трафика с сервера: {data_usage} байт ({round(data_usage/1000000000, 2)} ГБ)")
            
        except Exception as e:
            logger.error(f"Error syncing key data from server: {e}")
            logger.error(f"Ошибка при синхронизации данных с сервера: {str(e)}")
            # В случае ошибки используем значение по умолчанию для использования трафика
            data_usage = 0
            
    else:
        # Если нет ID ключа, используем значение по умолчанию
        data_usage = 0
    
    # Получаем имя пользователя
    username = key.get('username') or key.get('first_name') or f"User_{key['user_id']}"
    
    # Форматируем дату создания
    created_at = format_timestamp(key.get('created_at', 0))
    
    # Форматируем дату оплаты
    paid_until = format_paid_until(key.get('paid_until', 0), lang)
    
    # Форматируем использование трафика и лимит
    # Формируем строку "Использовано / Лимит"
    # Преобразуем байты в ГБ для более читабельного отображения по правилу 1 ГБ = 1,000,000,000 байтов
    limit_gb = round(data_limit / 1000000000, 1)
    used_gb = round(data_usage / 1000000000, 1)
    
    logger.info(f"Форматируем данные: использование={used_gb} ГБ, лимит={limit_gb} ГБ")
    
    if data_limit <= 0:
        # Если нет лимита, показываем только использование
        data_limit_formatted = f"{used_gb} GB"
    else:
        # Формат "Использовано / Лимит"
        data_limit_formatted = f"{used_gb} GB / {limit_gb} GB"
    
    logger.info(f"Отформатированный лимит/потребление: {data_limit_formatted}")
    
    # Формируем текст
    result = get_message('key_info', lang).format(
        key_id=key.get('key_id', '?'),
        username=username,
        created_at=created_at,
        paid_until=paid_until,
        data_limit=data_limit_formatted,
        access_url=key.get('access_url', '')
    )
    
    logger.info(f"Итоговый результат format_key_info сформирован")
    return result

def get_key_by_id(key_id: str) -> Optional[Dict[str, Any]]:
    """
    Получить данные ключа по ID
    
    Args:
        key_id (str): ID ключа
        
    Returns:
        dict: Данные ключа или None
    """
    # Получаем ключ из базы данных
    with db._connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT k.*, u.username, u.first_name, u.last_name
            FROM access_keys k
            LEFT JOIN users u ON k.user_id = u.user_id
            WHERE k.key_id = ?
        """, (key_id,))
        
        key = cursor.fetchone()
        if key:
            return dict(key)
    return None

def notify_admins(message: str):
    """
    Отправить уведомление всем администраторам
    
    Args:
        message (str): Текст уведомления
    """
    for admin_id in config.ADMIN_IDS:
        try:
            bot.send_message(admin_id, message)
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {e}")

def format_paid_until(timestamp: int, lang: str) -> str:
    """
    Форматирует дату оплаты
    
    Args:
        timestamp (int): Timestamp 
        lang (str): Код языка
        
    Returns:
        str: Отформатированная дата
    """
    if not timestamp or timestamp <= 0:
        return get_message('no_payment_date', lang)
        
    # Проверяем, истек ли срок
    current_time = int(time.time())
    expired = timestamp < current_time
    
    # Форматируем дату
    date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y')
    
    # Если истек срок, добавляем предупреждение
    if expired:
        return f"{date_str} {get_message('expired', lang)}"
    
    # Добавляем количество оставшихся дней
    days_left, _ = get_days_left(timestamp)
    if days_left > 0:
        days_text = get_message('days_left', lang).format(days=days_left)
        return f"{date_str} ({days_text})"
    
    return date_str

def format_data_limit(limit_bytes: int, lang: str) -> str:
    """
    Форматирует лимит данных
    
    Args:
        limit_bytes (int): Лимит в байтах
        lang (str): Код языка
        
    Returns:
        str: Отформатированный лимит
    """
    if not limit_bytes or limit_bytes <= 0:
        return get_message('no_limit', lang)
    
    # Конвертируем байты в ГБ по правилу 1 ГБ = 1,000,000,000 байтов
    limit_gb = round(limit_bytes / 1000000000, 1)
    return f"{limit_gb} GB"

def get_days_left(timestamp: int) -> Tuple[int, bool]:
    """
    Получить количество дней до истечения срока
    
    Args:
        timestamp (int): Timestamp 
        
    Returns:
        tuple: (количество дней, истек ли срок)
    """
    if not timestamp or timestamp <= 0:
        return 0, False
        
    current_time = int(time.time())
    
    # Проверяем, истек ли срок
    if timestamp < current_time:
        return 0, True
    
    # Вычисляем количество дней
    delta = datetime.datetime.fromtimestamp(timestamp) - datetime.datetime.fromtimestamp(current_time)
    days = delta.days
    
    return days, False

def handle_key_name_input(message: types.Message):
    """
    Обработка ввода имени для ключа
    
    Args:
        message (types.Message): Сообщение с именем ключа
    """
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    # Получаем состояние пользователя
    if user_id not in user_states or user_states[user_id].get('state') != 'waiting_for_key_name':
        return
    
    # Имя ключа
    key_name = message.text.strip()
    
    try:
        # Создаем ключ
        key_data = outline.create_access_key(key_name)
        
        # Сохраняем в базу данных
        db.save_access_key(user_id, key_data)
        
        # Отправляем сообщение с информацией о ключе
        bot.send_message(
            user_id,
            get_message('key_created', lang).format(
                name=key_name,
                access_url=key_data.get('accessUrl', '')
            ),
            parse_mode='HTML'
        )
        
        # Логируем активность
        db.log_activity(
            user_id, 
            'key_created', 
            f"Created new key {key_data.get('id')} with name {key_name}"
        )
        
    except Exception as e:
        logger.error(f"Error creating key: {e}")
        bot.send_message(
            user_id,
            get_message('error', lang).format(error=str(e)),
            parse_mode='HTML'
        )
    
    # Удаляем предыдущее сообщение
    try:
        bot.delete_message(
            user_states[user_id]['chat_id'],
            user_states[user_id]['message_id']
        )
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
    
    # Удаляем состояние пользователя
    del user_states[user_id]
    
    # Отправляем главное меню
    keyboard = get_main_keyboard(user_id, lang)
    bot.send_message(
        user_id,
        get_message('welcome', lang),
        reply_markup=keyboard,
        parse_mode='HTML'
    )

def register_handlers():
    """Регистрирует обработчики сообщений и callback-запросов"""
    @bot.message_handler(commands=['start'])
    def start_command(message: types.Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        user_data = message.from_user.to_dict()
        lang = get_user_language(user_id)
        
        # Сохраняем информацию о пользователе
        db.save_user(user_data)
        db.log_activity(user_id, 'start', 'User started the bot')
        
        # Отправляем приветственное сообщение с клавиатурой
        welcome_msg = get_message('welcome', lang)
        keyboard = get_main_keyboard(user_id, lang)
        
        bot.send_message(
            user_id, 
            welcome_msg,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.message_handler(commands=['help'])
    def help_command(message: types.Message):
        """Обработчик команды /help"""
        user_id = message.from_user.id
        lang = get_user_language(user_id)
        
        # Логируем активность
        db.log_activity(user_id, 'help', 'User requested help')
        
        # Отправляем сообщение помощи с клавиатурой
        help_msg = get_message('help', lang)
        keyboard = get_main_keyboard(user_id, lang)
        
        bot.send_message(
            user_id, 
            help_msg,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data == 'create_key')
    def create_key_callback(call: types.CallbackQuery):
        """Обработчик кнопки создания ключа"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Проверяем, не заблокирован ли пользователь
        if db.is_user_blocked(user_id):
            bot.answer_callback_query(call.id, get_message('user_blocked', lang))
            return
        
        # Проверяем количество ключей пользователя с учетом прав администратора
        is_admin = db.is_admin(user_id)
        max_keys = config.MAX_KEYS_PER_ADMIN if is_admin else config.MAX_KEYS_PER_USER
        
        if db.count_user_keys(user_id) >= max_keys:
            bot.answer_callback_query(call.id, get_message('max_keys_reached', lang))
            return
        
        # Запрашиваем имя для ключа
        bot.answer_callback_query(call.id)
        
        # Создаем клавиатуру с кнопкой отмены
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            get_message('cancel_button', lang),
            callback_data='back_to_main'
        ))
        
        # Отправляем сообщение с запросом имени ключа
        bot.edit_message_text(
            get_message('enter_key_name', lang),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Сохраняем состояние пользователя
        user_states[user_id] = {
            'state': 'waiting_for_key_name',
            'chat_id': call.message.chat.id,
            'message_id': call.message.message_id
        }

    @bot.callback_query_handler(func=lambda call: call.data == 'my_keys')
    def my_keys_callback(call: types.CallbackQuery):
        """Обработчик кнопки просмотра своих ключей"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Получаем ключи пользователя
        keys = db.get_user_keys(user_id)
        
        if not keys:
            bot.answer_callback_query(call.id, get_message('no_keys', lang))
            return
        
        # Создаем клавиатуру с ключами
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for key in keys:
            # Создаем название кнопки
            key_name = key.get('name') or f"Key {key['key_id']}"
            
            # Добавляем эмодзи статуса оплаты
            days_left, expired = get_days_left(key.get('paid_until', 0))
            status_emoji = "🔴" if expired else "🟢"
            
            button_text = f"{status_emoji} {key_name}"
            
            # Добавляем кнопку
            keyboard.add(types.InlineKeyboardButton(
                button_text,
                callback_data=f"key_{key['key_id']}"
            ))
        
        # Добавляем кнопку "Назад"
        keyboard.add(types.InlineKeyboardButton(
            get_message('back_button', lang),
            callback_data='back_to_main'
        ))
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id)
        
        # Отправляем список ключей
        bot.edit_message_text(
            get_message('key_list_title', lang),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data == 'all_keys')
    def all_keys_callback(call: types.CallbackQuery):
        """Обработчик кнопки просмотра всех ключей (для админов)"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Проверяем права администратора
        if not db.is_admin(user_id):
            bot.answer_callback_query(call.id, get_message('not_admin', lang))
            return
        
        # Получаем все ключи
        keys = db.get_all_keys()
        
        if not keys:
            bot.answer_callback_query(call.id, get_message('no_keys', lang))
            return
        
        # Создаем клавиатуру с ключами
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for key in keys:
            # Создаем название кнопки
            key_name = key.get('name') or f"Key {key['key_id']}"
            username = key.get('username') or key.get('first_name') or f"User_{key['user_id']}"
            
            # Добавляем эмодзи статуса оплаты
            days_left, expired = get_days_left(key.get('paid_until', 0))
            status_emoji = "🔴" if expired else "🟢"
            
            button_text = f"{status_emoji} {key_name} ({username})"
            
            # Добавляем кнопку
            keyboard.add(types.InlineKeyboardButton(
                button_text,
                callback_data=f"key_{key['key_id']}"
            ))
        
        # Добавляем кнопку "Назад"
        keyboard.add(types.InlineKeyboardButton(
            get_message('back_button', lang),
            callback_data='back_to_main'
        ))
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id)
        
        # Отправляем список ключей
        bot.edit_message_text(
            get_message('key_list_title', lang),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('key_'))
    def key_info_callback(call: types.CallbackQuery):
        """Обработчик просмотра информации о ключе"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Извлекаем ID ключа из callback данных
        key_id = call.data.split('_')[1]
        
        # Получаем данные ключа
        key = get_key_by_id(key_id)
        
        if not key:
            bot.answer_callback_query(call.id, get_message('key_not_found', lang))
            return
        
        # Проверяем, принадлежит ли ключ пользователю или является ли пользователь администратором
        is_admin = db.is_admin(user_id)
        is_owner = key['user_id'] == user_id
        
        if not is_owner and not is_admin:
            bot.answer_callback_query(call.id, get_message('not_admin', lang))
            return
        
        # Создаем клавиатуру для управления ключом
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        # Если пользователь админ, добавляем кнопки управления
        if is_admin:
            # Кнопка установки даты оплаты
            keyboard.add(types.InlineKeyboardButton(
                get_message('set_paid_until', lang),
                callback_data=f'set_paid_{key_id}'
            ))
            
            # Кнопка установки лимита данных
            keyboard.add(types.InlineKeyboardButton(
                get_message('set_data_limit', lang),
                callback_data=f'set_limit_{key_id}'
            ))
        
        # Кнопка удаления ключа
        keyboard.add(types.InlineKeyboardButton(
            get_message('delete_key_button', lang),
            callback_data=f'delete_{key_id}'
        ))
        
        # Кнопка "Назад"
        back_data = 'all_keys' if is_admin and not is_owner else 'my_keys'
        keyboard.add(types.InlineKeyboardButton(
            get_message('back_button', lang),
            callback_data=back_data
        ))
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id)
        
        # Форматируем информацию о ключе
        key_info = format_key_info(key, lang)
        
        # Отправляем информацию о ключе
        bot.edit_message_text(
            key_info,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
    def back_to_main_callback(call: types.CallbackQuery):
        """Обработчик кнопки отмены действия и возврата в главное меню"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Удаляем состояние пользователя
        if user_id in user_states:
            del user_states[user_id]
        
        # Отправляем пользователю главное меню
        keyboard = get_main_keyboard(user_id, lang)
        
        bot.edit_message_text(
            get_message('welcome', lang),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('set_limit_'))
    def set_limit_callback(call: types.CallbackQuery):
        """Обработчик кнопки установки лимита трафика"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Проверяем права администратора
        if not db.is_admin(user_id):
            bot.answer_callback_query(call.id, get_message('not_admin', lang))
            return
        
        # Извлекаем ID ключа из callback данных
        key_id = call.data.split('_')[2]
        
        # Создаем клавиатуру с кнопкой отмены
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            get_message('cancel_button', lang),
            callback_data=f'key_{key_id}'
        ))
        
        # Отправляем сообщение с запросом лимита трафика
        bot.edit_message_text(
            get_message('input_limit', lang),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Сохраняем состояние пользователя
        user_states[user_id] = {
            'state': 'waiting_for_limit',
            'key_id': key_id,
            'chat_id': call.message.chat.id,
            'message_id': call.message.message_id
        }
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('set_paid_'))
    def set_paid_callback(call: types.CallbackQuery):
        """Обработчик кнопки установки даты оплаты"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Проверяем права администратора
        if not db.is_admin(user_id):
            bot.answer_callback_query(call.id, get_message('not_admin', lang))
            return
        
        # Извлекаем ID ключа из callback данных
        key_id = call.data.split('_')[2]
        
        # Создаем клавиатуру с кнопкой отмены
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            get_message('cancel_button', lang),
            callback_data=f'key_{key_id}'
        ))
        
        # Отправляем сообщение с запросом даты оплаты
        bot.edit_message_text(
            get_message('input_date', lang),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Сохраняем состояние пользователя
        user_states[user_id] = {
            'state': 'waiting_for_date',
            'key_id': key_id,
            'chat_id': call.message.chat.id,
            'message_id': call.message.message_id
        }
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id)
    
    # Обработчик callback запросов для отмены процесса установки даты или лимита
    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
    def delete_key_callback(call: types.CallbackQuery):
        """Обработчик кнопки удаления ключа"""
        user_id = call.from_user.id
        lang = get_user_language(user_id)
        
        # Извлекаем ID ключа из callback данных
        key_id = call.data.split('_')[1]
        
        # Получаем данные ключа
        key = get_key_by_id(key_id)
        
        if not key:
            bot.answer_callback_query(call.id, get_message('key_not_found', lang))
            return
        
        # Проверяем, принадлежит ли ключ пользователю или является ли пользователь администратором
        is_admin = db.is_admin(user_id)
        is_owner = key['user_id'] == user_id
        
        if not is_owner and not is_admin:
            bot.answer_callback_query(call.id, get_message('not_admin', lang))
            return
        
        try:
            # Удаляем ключ из Outline сервера
            outline.delete_access_key(key_id)
            
            # Удаляем ключ из базы данных
            db.delete_access_key(key_id)
            
            # Логируем активность
            db.log_activity(
                user_id, 
                'key_deleted', 
                f"Deleted key {key_id}"
            )
            
            # Отвечаем на callback
            bot.answer_callback_query(call.id, get_message('key_deleted', lang))
            
            # Возвращаем пользователя в соответствующее меню
            back_data = 'all_keys' if is_admin and not is_owner else 'my_keys'
            
            keyboard = get_main_keyboard(user_id, lang)
            bot.edit_message_text(
                get_message('welcome', lang),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error deleting key {key_id}: {e}")
            bot.answer_callback_query(call.id, get_message('error', lang).format(error=str(e)))
    
    # Обработчик текстовых сообщений для получения лимита трафика
    @bot.message_handler(func=lambda message: message.from_user.id in user_states 
                                         and user_states[message.from_user.id].get('state') == 'waiting_for_limit')
    def process_limit_input(message: types.Message):
        """Обработка ввода лимита трафика"""
        user_id = message.from_user.id
        lang = get_user_language(user_id)
        
        # Получаем состояние пользователя
        if user_id not in user_states or user_states[user_id].get('state') != 'waiting_for_limit':
            return
        
        # Получаем ID ключа из состояния
        key_id = user_states[user_id].get('key_id')
        
        # Проверяем ввод пользователя
        try:
            # Преобразуем ввод пользователя в число
            limit_gb = float(message.text.strip())
            
            # Проверяем, что лимит положительный
            if limit_gb <= 0:
                raise ValueError("Limit must be positive")
            
            # Преобразуем ГБ в байты
            limit_bytes = int(limit_gb * 1000000000)
            
            # Устанавливаем лимит на сервере
            if outline.set_data_limit(key_id, limit_bytes):
                # Отправляем сообщение об успешной установке лимита
                bot.send_message(
                    user_id,
                    get_message('data_limit_set', lang).format(limit=f"{limit_gb} GB"),
                    parse_mode='HTML'
                )
                
                # Логируем активность
                db.log_activity(
                    user_id, 
                    'limit_set', 
                    f"Set data limit {limit_gb} GB for key {key_id}"
                )
            else:
                # Отправляем сообщение об ошибке
                bot.send_message(
                    user_id,
                    get_message('error', lang).format(error="Failed to set data limit"),
                    parse_mode='HTML'
                )
        except ValueError:
            # Отправляем сообщение о неверном формате лимита
            bot.send_message(
                user_id,
                get_message('invalid_limit', lang),
                parse_mode='HTML'
            )
            return
        
        # Удаляем предыдущее сообщение
        try:
            bot.delete_message(
                user_states[user_id]['chat_id'],
                user_states[user_id]['message_id']
            )
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
        
        # Удаляем состояние пользователя
        del user_states[user_id]
        
        # Получаем данные ключа
        key = get_key_by_id(key_id)
        
        # Отправляем информацию о ключе
        if key:
            # Форматируем информацию о ключе
            key_info = format_key_info(key, lang)
            
            # Создаем клавиатуру для управления ключом
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            
            # Кнопка установки даты оплаты
            keyboard.add(types.InlineKeyboardButton(
                get_message('set_paid_until', lang),
                callback_data=f'set_paid_{key_id}'
            ))
            
            # Кнопка установки лимита данных
            keyboard.add(types.InlineKeyboardButton(
                get_message('set_data_limit', lang),
                callback_data=f'set_limit_{key_id}'
            ))
            
            # Кнопка удаления ключа
            keyboard.add(types.InlineKeyboardButton(
                get_message('delete_key_button', lang),
                callback_data=f'delete_{key_id}'
            ))
            
            # Кнопка "Назад"
            keyboard.add(types.InlineKeyboardButton(
                get_message('back_button', lang),
                callback_data='all_keys'
            ))
            
            # Отправляем информацию о ключе
            bot.send_message(
                user_id,
                key_info,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # Отправляем главное меню
            keyboard = get_main_keyboard(user_id, lang)
            bot.send_message(
                user_id,
                get_message('welcome', lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    # Обработчик текстовых сообщений для получения даты оплаты
    @bot.message_handler(func=lambda message: message.from_user.id in user_states 
                                         and user_states[message.from_user.id].get('state') == 'waiting_for_date')
    def process_date_input(message: types.Message):
        """Обработка ввода даты оплаты"""
        user_id = message.from_user.id
        lang = get_user_language(user_id)
        
        # Получаем состояние пользователя
        if user_id not in user_states or user_states[user_id].get('state') != 'waiting_for_date':
            return
        
        # Получаем ID ключа из состояния
        key_id = user_states[user_id].get('key_id')
        
        # Проверяем ввод пользователя
        try:
            # Разбираем дату в формате ДД.ММ.ГГГГ
            day, month, year = map(int, message.text.strip().split('.'))
            
            # Проверяем корректность даты
            date = datetime.datetime(year, month, day)
            
            # Проверяем, что дата не в прошлом
            now = datetime.datetime.now()
            if date < now:
                bot.send_message(
                    user_id,
                    get_message('date_in_past', lang),
                    parse_mode='HTML'
                )
                return
            
            # Преобразуем дату в timestamp
            timestamp = int(date.timestamp())
            
            # Обновляем дату оплаты в базе данных
            db.update_paid_until(key_id, timestamp)
            
            # Отправляем сообщение об успешной установке даты
            bot.send_message(
                user_id,
                get_message('paid_until_set', lang).format(date=message.text.strip()),
                parse_mode='HTML'
            )
            
            # Логируем активность
            db.log_activity(
                user_id, 
                'date_set', 
                f"Set payment date {message.text.strip()} for key {key_id}"
            )
        except ValueError:
            # Отправляем сообщение о неверном формате даты
            bot.send_message(
                user_id,
                get_message('invalid_date', lang),
                parse_mode='HTML'
            )
            return
        
        # Удаляем предыдущее сообщение
        try:
            bot.delete_message(
                user_states[user_id]['chat_id'],
                user_states[user_id]['message_id']
            )
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
        
        # Удаляем состояние пользователя
        del user_states[user_id]
        
        # Получаем данные ключа
        key = get_key_by_id(key_id)
        
        # Отправляем информацию о ключе
        if key:
            # Форматируем информацию о ключе
            key_info = format_key_info(key, lang)
            
            # Создаем клавиатуру для управления ключом
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            
            # Кнопка установки даты оплаты
            keyboard.add(types.InlineKeyboardButton(
                get_message('set_paid_until', lang),
                callback_data=f'set_paid_{key_id}'
            ))
            
            # Кнопка установки лимита данных
            keyboard.add(types.InlineKeyboardButton(
                get_message('set_data_limit', lang),
                callback_data=f'set_limit_{key_id}'
            ))
            
            # Кнопка удаления ключа
            keyboard.add(types.InlineKeyboardButton(
                get_message('delete_key_button', lang),
                callback_data=f'delete_{key_id}'
            ))
            
            # Кнопка "Назад"
            keyboard.add(types.InlineKeyboardButton(
                get_message('back_button', lang),
                callback_data='all_keys'
            ))
            
            # Отправляем информацию о ключе
            bot.send_message(
                user_id,
                key_info,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # Отправляем главное меню
            keyboard = get_main_keyboard(user_id, lang)
            bot.send_message(
                user_id,
                get_message('welcome', lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )

    # Регистрируем обработчик текстовых сообщений для получения имени ключа
    @bot.message_handler(func=lambda message: message.from_user.id in user_states 
                                         and user_states[message.from_user.id].get('state') == 'waiting_for_key_name')
    def process_key_name(message: types.Message):
        handle_key_name_input(message)
    
    # Обработчик для неизвестных сообщений
    @bot.message_handler(func=lambda message: True)
    def unknown_message(message: types.Message):
        """Обработчик неизвестных сообщений"""
        user_id = message.from_user.id
        lang = get_user_language(user_id)
        
        # Если у пользователя есть состояние, и оно неизвестно, логируем ошибку
        if user_id in user_states:
            state = user_states[user_id].get('state')
            logger.warning(f"Unknown state: {state} for user {user_id}")
        
        # Отправляем главное меню
        keyboard = get_main_keyboard(user_id, lang)
        bot.send_message(
            user_id,
            get_message('welcome', lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        ) 