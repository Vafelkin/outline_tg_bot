#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для работы с базой данных SQLite
"""

import sqlite3
import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

import config
from outline_api import OutlineAPI

logger = logging.getLogger('database')

class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_file: str = config.DB_FILE):
        """
        Инициализация базы данных
        
        Args:
            db_file (str): Путь к файлу базы данных
        """
        self.db_file = db_file
        self._init_db()
        self.outline = OutlineAPI(config.OUTLINE_API_URL)
    
    @contextmanager
    def _connection(self):
        """
        Контекстный менеджер для соединения с базой данных
        
        Yields:
            sqlite3.Connection: Соединение с базой данных
        """
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Результаты в виде словарей
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """Инициализация базы данных, создание таблиц"""
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_admin INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                created_at INTEGER,
                last_activity INTEGER
            )
            ''')
            
            # Таблица ключей доступа с дополнительными полями
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key_id TEXT,
                name TEXT,
                access_url TEXT,
                data_limit INTEGER DEFAULT 0,
                paid_until INTEGER DEFAULT 0,
                created_at INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            # Проверяем, существуют ли столбцы data_limit и paid_until
            cursor.execute("PRAGMA table_info(access_keys)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Если столбцов нет, добавляем их
            if 'data_limit' not in columns:
                cursor.execute("ALTER TABLE access_keys ADD COLUMN data_limit INTEGER DEFAULT 0")
            if 'paid_until' not in columns:
                cursor.execute("ALTER TABLE access_keys ADD COLUMN paid_until INTEGER DEFAULT 0")
            
            # Таблица журнала действий
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            conn.commit()
    
    def save_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Сохранить или обновить данные пользователя
        
        Args:
            user_data (dict): Данные пользователя
            
        Returns:
            bool: True, если операция успешна
        """
        user_id = user_data.get('id')
        if not user_id:
            logger.error("Невозможно сохранить пользователя без ID")
            return False
        
        current_time = int(time.time())
        
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Проверим, существует ли уже пользователь
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Обновить существующего пользователя
                cursor.execute('''
                UPDATE users SET 
                    username = ?,
                    first_name = ?,
                    last_name = ?,
                    language_code = ?,
                    last_activity = ?
                WHERE user_id = ?
                ''', (
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('language_code'),
                    current_time,
                    user_id
                ))
            else:
                # Создать нового пользователя
                cursor.execute('''
                INSERT INTO users (
                    user_id, username, first_name, last_name, 
                    language_code, created_at, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('language_code'),
                    current_time,
                    current_time
                ))
            
            conn.commit()
            return True
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить данные пользователя по ID
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            dict: Данные пользователя или None, если пользователь не найден
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            return None
    
    def set_admin_status(self, user_id: int, is_admin: bool) -> bool:
        """
        Установить статус администратора для пользователя
        
        Args:
            user_id (int): ID пользователя
            is_admin (bool): True - сделать администратором, False - убрать права администратора
            
        Returns:
            bool: True, если операция успешна
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_admin = ? WHERE user_id = ?", 
                (1 if is_admin else 0, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def block_user(self, user_id: int, block: bool = True) -> bool:
        """
        Заблокировать или разблокировать пользователя
        
        Args:
            user_id (int): ID пользователя
            block (bool): True - заблокировать, False - разблокировать
            
        Returns:
            bool: True, если операция успешна
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_blocked = ? WHERE user_id = ?", 
                (1 if block else 0, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def is_user_blocked(self, user_id: int) -> bool:
        """
        Проверить, заблокирован ли пользователь
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            bool: True, если пользователь заблокирован
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                return bool(result['is_blocked'])
            return False
    
    def is_admin(self, user_id: int) -> bool:
        """
        Проверить, является ли пользователь администратором
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            bool: True, если пользователь администратор
        """
        # Проверяем, есть ли пользователь в списке администраторов в конфиге
        if user_id in config.ADMIN_IDS:
            return True
            
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                return bool(result['is_admin'])
            return False
    
    def log_activity(self, user_id: int, action: str, details: str = '') -> bool:
        """
        Записать активность пользователя в журнал
        
        Args:
            user_id (int): ID пользователя
            action (str): Тип действия
            details (str): Детали действия
            
        Returns:
            bool: True, если операция успешна
        """
        if not config.ENABLE_ACCESS_LOG:
            return True
            
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activity_log (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, action, details, int(time.time()))
            )
            conn.commit()
            return True
    
    def save_access_key(self, user_id: int, key_data: Dict[str, Any], 
                      paid_until: Optional[int] = None, data_limit: int = 0) -> bool:
        """
        Сохранить ключ доступа
        
        Args:
            user_id (int): ID пользователя
            key_data (dict): Данные ключа
            paid_until (int, optional): Timestamp, до которого оплачен ключ
            data_limit (int): Лимит данных в байтах
            
        Returns:
            bool: True, если операция успешна
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Проверим, существует ли уже ключ с таким ID
            cursor.execute("SELECT id FROM access_keys WHERE key_id = ?", (key_data.get('id'),))
            existing_key = cursor.fetchone()
            
            current_time = int(time.time())
            
            if existing_key:
                # Обновить существующий ключ
                cursor.execute('''
                UPDATE access_keys SET 
                    user_id = ?,
                    name = ?,
                    access_url = ?,
                    data_limit = ?,
                    paid_until = ?
                WHERE key_id = ?
                ''', (
                    user_id,
                    key_data.get('name', ''),
                    key_data.get('accessUrl', ''),
                    data_limit,
                    paid_until or 0,
                    key_data.get('id')
                ))
            else:
                # Создать новый ключ
                cursor.execute('''
                INSERT INTO access_keys (
                    user_id, key_id, name, access_url, data_limit, paid_until, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    key_data.get('id', ''),
                    key_data.get('name', ''),
                    key_data.get('accessUrl', ''),
                    data_limit,
                    paid_until or 0,
                    current_time
                ))
            
            conn.commit()
            return True
    
    def update_key_payment(self, key_id: str, paid_until: int) -> bool:
        """
        Обновить дату оплаты ключа
        
        Args:
            key_id (str): ID ключа
            paid_until (int): Timestamp, до которого оплачен ключ
            
        Returns:
            bool: True, если операция успешна
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE access_keys SET paid_until = ? WHERE key_id = ?", 
                (paid_until, key_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_key_limit(self, key_id: str, data_limit: int) -> bool:
        """
        Обновить лимит данных для ключа
        
        Args:
            key_id (str): ID ключа
            data_limit (int): Лимит данных в байтах
            
        Returns:
            bool: True, если операция успешна
        """
        logger.info(f"Updating key limit in database for key {key_id}: {data_limit} bytes")
        try:
            with self._connection() as conn:
                # Проверяем, существует ли ключ
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM access_keys WHERE key_id = ?", (key_id,))
                existing_key = cursor.fetchone()
                
                if not existing_key:
                    logger.error(f"Key {key_id} not found in database")
                    return False
                
                logger.info(f"Existing key in database: {dict(existing_key)}")
                
                # Обновляем лимит
                cursor.execute(
                    "UPDATE access_keys SET data_limit = ? WHERE key_id = ?", 
                    (data_limit, key_id)
                )
                conn.commit()
                
                # Проверяем, произошло ли обновление
                if cursor.rowcount > 0:
                    logger.info(f"Successfully updated limit for key {key_id} to {data_limit} bytes")
                    return True
                else:
                    logger.warning(f"No rows updated for key {key_id}")
                    return False
        except Exception as e:
            logger.error(f"Error updating key limit in database: {e}")
            return False
    
    def get_user_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получить все ключи пользователя
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            list: Список ключей пользователя
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM access_keys 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            keys = cursor.fetchall()
            return [dict(key) for key in keys]
    
    def get_all_keys(self) -> List[Dict[str, Any]]:
        """
        Получить все ключи с информацией о пользователях
        
        Returns:
            list: Список всех ключей с данными о пользователях
        """
        # Сначала синхронизируем с сервером
        self.sync_keys_with_server()
        
        with self._connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT k.*, u.username, u.first_name, u.last_name
                FROM access_keys k
                LEFT JOIN users u ON k.user_id = u.user_id
                ORDER BY k.created_at DESC
            ''')
            
            keys = cursor.fetchall()
            return [dict(key) for key in keys]
    
    def get_key_owner(self, key_id: str) -> Optional[int]:
        """
        Получить ID владельца ключа
        
        Args:
            key_id (str): ID ключа
            
        Returns:
            int: ID пользователя или None, если ключ не найден
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM access_keys WHERE key_id = ?", (key_id,))
            result = cursor.fetchone()
            
            if result:
                return result['user_id']
            return None
    
    def delete_key(self, key_id: str) -> bool:
        """
        Удалить ключ из базы данных
        
        Args:
            key_id (str): ID ключа
            
        Returns:
            bool: True, если операция успешна
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM access_keys WHERE key_id = ?", (key_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def count_user_keys(self, user_id: int) -> int:
        """
        Подсчитать количество ключей пользователя
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            int: Количество ключей
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM access_keys WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                return result['count']
            return 0
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Получить список всех пользователей
        
        Returns:
            list: Список пользователей
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            
            users = cursor.fetchall()
            return [dict(user) for user in users]
    
    def sync_keys_with_server(self):
        """
        Синхронизация ключей с сервером Outline
        """
        try:
            # Получаем все ключи с сервера
            server_keys = self.outline.get_access_keys()
            
            # Получаем все ключи из базы
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key_id, data_limit FROM access_keys")
                db_keys = {row['key_id']: row['data_limit'] for row in cursor.fetchall()}
            
            # Добавляем новые ключи в базу и обновляем существующие
            for key in server_keys:
                key_id = str(key['id'])
                # Используем оригинальное имя ключа с сервера или создаем простое имя по ID
                key_name = key.get('name')
                if not key_name or key_name.startswith("Temporary_"):
                    key_name = f"Ключ_{key_id}"
                
                # Получаем лимит данных с сервера
                data_limit = 0
                if 'dataLimit' in key and 'bytes' in key['dataLimit']:
                    data_limit = key['dataLimit']['bytes']
                
                if key_id not in db_keys:
                    # Если ключ не найден в базе, добавляем его
                    with self._connection() as conn:
                        cursor = conn.cursor()
                        
                        # Создаем пользователя с именем из ключа
                        cursor.execute('''
                            INSERT OR IGNORE INTO users 
                            (user_id, username, created_at, last_activity)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            -int(key_id),  # Используем отрицательный ID для временных пользователей
                            key_name,  # Используем имя ключа без префикса Temporary
                            int(time.time()),
                            int(time.time())
                        ))
                        
                        # Добавляем ключ с лимитом данных с сервера
                        cursor.execute('''
                            INSERT INTO access_keys 
                            (key_id, user_id, name, access_url, data_limit, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            key_id,
                            -int(key_id),
                            key_name,
                            key['accessUrl'],
                            data_limit,
                            int(time.time())
                        ))
                        
                        conn.commit()
                        logger.info(f"Added new key {key_id} with name {key_name} from server")
                else:
                    # Если ключ уже существует, проверяем и обновляем лимит данных
                    db_limit = db_keys[key_id]
                    if db_limit != data_limit:
                        with self._connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE access_keys
                                SET data_limit = ?
                                WHERE key_id = ?
                            ''', (data_limit, key_id))
                            
                            conn.commit()
                            logger.info(f"Updated data limit for key {key_id} from {db_limit} to {data_limit} bytes")
            
            logger.info("Keys synchronized with server")
            
        except Exception as e:
            logger.error(f"Error syncing keys with server: {e}") 