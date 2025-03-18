#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль с сообщениями для бота на разных языках
"""

MESSAGES = {
    'ru': {
        'welcome': 'Привет! Я бот для управления доступом к Outline VPN серверу.',
        'help': '''Доступные команды:
/start - Начать работу с ботом
/help - Показать это сообщение
/key - Получить новый ключ доступа
/keys - Показать ваши ключи
/delete - Удалить ключ
/admin - Панель администратора''',
        'key_created': '✅ Ключ успешно создан.\n\nИмя: <b>{name}</b>\n\nСсылка для подключения:\n<code>{access_url}</code>',
        'key_deleted': 'Ключ успешно удален',
        'no_keys': 'У вас пока нет ключей доступа',
        'your_keys': 'Ваши ключи доступа:\n{keys}',
        'error': 'Произошла ошибка: {error}',
        'admin_panel': 'Панель администратора',
        'user_blocked': 'Пользователь заблокирован',
        'user_unblocked': 'Пользователь разблокирован',
        'admin_added': 'Пользователь добавлен как администратор',
        'admin_removed': 'Пользователь удален из администраторов',
        'max_keys_reached': 'Вы достигли максимального количества ключей',
        'invalid_key_id': 'Неверный ID ключа',
        'key_not_found': 'Ключ не найден',
        'not_admin': 'У вас нет прав администратора',
        'user_not_found': 'Пользователь не найден',
        'server_info': '''Информация о сервере:
Страна: {country}
IP: {ip}
Порт: {port}
Метод: {method}
''',
        'metrics': '''Статистика использования:
Всего пользователей: {total_users}
Активных ключей: {active_keys}
Передано данных: {bytes_transferred}
''',
        # Сообщения для обновленного функционала
        'key_info': '''📌 <b>Ключ №{key_id}</b>

👤 <b>Пользователь:</b> {username}
📅 <b>Дата создания:</b> {created_at}
📆 <b>Оплачен до:</b> {paid_until}
📊 <b>Использовано/Лимит:</b> {data_limit}
🔗 <b>URL доступа:</b> {access_url}''',
        'key_list_title': '📋 <b>Список ключей доступа:</b>',
        'no_payment_date': 'Не определено',
        'no_limit': 'Без ограничений',
        'expired': '⚠️ Истек!',
        'set_paid_until': 'Установить дату оплаты',
        'set_data_limit': 'Установить лимит трафика',
        'paid_until_set': 'Дата оплаты установлена до {date}',
        'data_limit_set': 'Лимит трафика установлен: {limit}',
        'input_date': 'Введите дату оплаты в формате ДД.ММ.ГГГГ',
        'input_limit': 'Введите лимит трафика в ГБ (целое число)',
        'invalid_date': 'Неверный формат даты. Используйте формат ДД.ММ.ГГГГ',
        'invalid_limit': 'Неверный формат лимита. Введите целое число',
        'date_in_past': 'Дата не может быть в прошлом',
        'admin_key_management': 'Управление ключами',
        'back_button': '← Назад',
        'create_key_button': 'Создать ключ',
        'my_keys_button': 'Мои ключи',
        'all_keys_button': 'Все ключи',
        'key_settings_button': 'Настройки ключа',
        'day': 'день',
        'days': 'дней',
        'days_left': 'Осталось: {days}',
        'format_bytes': '{size:.1f} {suffix}',
        'enter_key_name': '📝 Введите имя для нового ключа (например, имя пользователя):',
        'enter_key_duration': '⏱ Выберите срок действия ключа:',
        'key_created_with_duration': '✅ Ключ успешно создан.\n\nИмя: <b>{name}</b>\nСрок действия: <b>{duration}</b>\n\nСсылка для подключения:\n<code>{access_url}</code>',
        'delete_key_button': 'Удалить ключ',
        'cancel_button': 'Отмена',
    },
    'en': {
        'welcome': 'Hi! I am a bot for managing access to the Outline VPN server.',
        'help': '''Available commands:
/start - Start working with the bot
/help - Show this message
/key - Get a new access key
/keys - Show your keys
/delete - Delete a key
/admin - Admin panel''',
        'key_created': '✅ Key successfully created.\n\nName: <b>{name}</b>\n\nConnection link:\n<code>{access_url}</code>',
        'key_deleted': 'Key successfully deleted',
        'no_keys': 'You don\'t have any access keys yet',
        'your_keys': 'Your access keys:\n{keys}',
        'error': 'An error occurred: {error}',
        'admin_panel': 'Admin panel',
        'user_blocked': 'User blocked',
        'user_unblocked': 'User unblocked',
        'admin_added': 'User added as administrator',
        'admin_removed': 'User removed from administrators',
        'max_keys_reached': 'You have reached the maximum number of keys',
        'invalid_key_id': 'Invalid key ID',
        'key_not_found': 'Key not found',
        'not_admin': 'You don\'t have administrator rights',
        'user_not_found': 'User not found',
        'server_info': '''Server information:
Country: {country}
IP: {ip}
Port: {port}
Method: {method}
''',
        'metrics': '''Usage statistics:
Total users: {total_users}
Active keys: {active_keys}
Data transferred: {bytes_transferred}
''',
        # Messages for updated functionality
        'key_info': '''📌 <b>Key #{key_id}</b>

👤 <b>User:</b> {username}
📅 <b>Created:</b> {created_at}
📆 <b>Paid until:</b> {paid_until}
📊 <b>Used/Limit:</b> {data_limit}
🔗 <b>Access URL:</b> {access_url}''',
        'key_list_title': '📋 <b>Access key list:</b>',
        'no_payment_date': 'Not defined',
        'no_limit': 'Unlimited',
        'expired': '⚠️ Expired!',
        'set_paid_until': 'Set payment date',
        'set_data_limit': 'Set data limit',
        'paid_until_set': 'Payment date set until {date}',
        'data_limit_set': 'Data limit set: {limit}',
        'input_date': 'Enter payment date in DD.MM.YYYY format',
        'input_limit': 'Enter data limit in GB (integer)',
        'invalid_date': 'Invalid date format. Use DD.MM.YYYY format',
        'invalid_limit': 'Invalid limit format. Enter an integer',
        'date_in_past': 'Date cannot be in the past',
        'admin_key_management': 'Key management',
        'back_button': '← Back',
        'create_key_button': 'Create key',
        'my_keys_button': 'My keys',
        'all_keys_button': 'All keys',
        'key_settings_button': 'Key settings',
        'day': 'day',
        'days': 'days',
        'days_left': 'Left: {days}',
        'format_bytes': '{size:.1f} {suffix}',
        'enter_key_name': '📝 Enter a name for the new key (for example, username):',
        'enter_key_duration': '⏱ Select key duration:',
        'key_created_with_duration': '✅ Key successfully created.\n\nName: <b>{name}</b>\nValid until: <b>{duration}</b>\n\nConnection link:\n<code>{access_url}</code>',
        'delete_key_button': 'Delete key',
        'cancel_button': 'Cancel',
    }
}

def get_message(key: str, lang: str = 'ru') -> str:
    """
    Получить сообщение на указанном языке
    
    Args:
        key (str): Ключ сообщения
        lang (str): Код языка ('ru' или 'en')
        
    Returns:
        str: Сообщение на указанном языке
    """
    # Проверяем, существует ли ключ для указанного языка
    lang_dict = MESSAGES.get(lang, MESSAGES['en'])
    
    # Если ключ не найден в указанном языке, берем из английского
    return lang_dict.get(key, MESSAGES['en'].get(key, f"Message '{key}' not found")) 