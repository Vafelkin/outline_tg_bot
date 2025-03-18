#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для Outline VPN бота
"""

import time
import datetime
from typing import Dict, Any, Optional, Tuple, Union
from math import floor

def format_timestamp(timestamp: int, format_string: str = '%d.%m.%Y %H:%M') -> str:
    """
    Форматирует timestamp в читаемую дату
    
    Args:
        timestamp (int): Unix timestamp
        format_string (str): Строка форматирования
        
    Returns:
        str: Отформатированная дата
    """
    if not timestamp:
        return "Не определено"
    
    return datetime.datetime.fromtimestamp(timestamp).strftime(format_string)

def format_bytes(size_bytes: int) -> str:
    """
    Форматирует размер в байтах в человекочитаемую форму
    
    Args:
        size_bytes (int): Размер в байтах
        
    Returns:
        str: Отформатированный размер
    """
    if not size_bytes:
        return "Без ограничений"
    
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    suffix_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and suffix_index < len(suffixes) - 1:
        suffix_index += 1
        size /= 1024.0
    
    return f"{size:.1f} {suffixes[suffix_index]}"

def get_days_left(timestamp: int) -> Tuple[int, bool]:
    """
    Возвращает количество дней до указанной даты
    
    Args:
        timestamp (int): Unix timestamp
        
    Returns:
        Tuple[int, bool]: (количество дней, истекло ли время)
    """
    if not timestamp:
        return 0, False
        
    now = datetime.datetime.now()
    target_date = datetime.datetime.fromtimestamp(timestamp)
    
    days_left = (target_date - now).days
    return days_left, days_left < 0

def string_to_timestamp(date_string: str, format_string: str = '%d.%m.%Y') -> Optional[int]:
    """
    Преобразует строку с датой в timestamp
    
    Args:
        date_string (str): Строка с датой
        format_string (str): Формат даты
        
    Returns:
        int: Unix timestamp или None, если некорректная дата
    """
    try:
        dt = datetime.datetime.strptime(date_string, format_string)
        return int(dt.timestamp())
    except ValueError:
        return None

def gb_to_bytes(gb: Union[int, float]) -> int:
    """
    Преобразует гигабайты в байты
    
    Args:
        gb (int, float): Размер в ГБ
        
    Returns:
        int: Размер в байтах
    """
    return int(gb * 1024 * 1024 * 1024)

def format_paid_until(timestamp: int, lang: str) -> str:
    """
    Форматирует дату окончания оплаты
    
    Args:
        timestamp (int): Unix timestamp
        lang (str): Код языка
        
    Returns:
        str: Отформатированная дата
    """
    from messages import get_message
    
    if not timestamp:
        return get_message('no_payment_date', lang)
    
    date_str = format_timestamp(timestamp, '%d.%m.%Y')
    days_left, expired = get_days_left(timestamp)
    
    if expired:
        return f"{date_str} ({get_message('expired', lang)})"
    
    # Склонение слова "день"
    if lang == 'ru':
        day_word = get_message('day', lang) if abs(days_left) == 1 else get_message('days', lang)
    else:
        day_word = get_message('day', lang) if abs(days_left) == 1 else get_message('days', lang)
    
    days_left_text = get_message('days_left', lang).format(days=f"{days_left} {day_word}")
    return f"{date_str} ({days_left_text})"

def format_data_limit(limit_bytes: int, lang: str) -> str:
    """
    Форматирует лимит данных
    
    Args:
        limit_bytes (int): Лимит в байтах
        lang (str): Код языка
        
    Returns:
        str: Отформатированный лимит
    """
    from messages import get_message
    
    if not limit_bytes:
        return get_message('no_limit', lang)
    
    return format_bytes(limit_bytes) 