#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для работы с API Outline VPN сервера
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Union, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('outline_api')

class OutlineAPI:
    """Класс для взаимодействия с API Outline сервера"""
    
    def __init__(self, api_url: str):
        """
        Инициализация клиента API
        
        Args:
            api_url (str): URL API Outline сервера
        """
        self.api_url = api_url.rstrip('/')
        logger.info(f"Outline API initialized with URL: {api_url}")
    
    def _request(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнить запрос к API
        
        Args:
            method (str): HTTP метод (GET, POST, PUT, DELETE)
            endpoint (str): Конечная точка API
            json_data (dict, optional): Данные для отправки с запросом
            
        Returns:
            dict: Ответ от API в виде словаря
            
        Raises:
            Exception: Если произошла ошибка в запросе
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_data,
                timeout=10,
                verify=False  # Отключаем проверку SSL
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            raise Exception(f"API request error: {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Получить информацию о сервере
        
        Returns:
            dict: Информация о сервере
        """
        return self._request('GET', '/server')
    
    def get_access_keys(self) -> List[Dict[str, Any]]:
        """
        Получение списка всех ключей доступа
        
        Returns:
            list: Список ключей доступа
        """
        response = self._request('GET', '/access-keys')
        keys = response.get('accessKeys', [])
        
        # Получаем более детальную информацию для каждого ключа
        for i, key in enumerate(keys):
            if 'id' in key:
                try:
                    # Получаем данные о лимите трафика
                    key_info = self.get_access_key(key['id'])
                    # Добавляем информацию о лимите
                    if 'dataLimit' in key_info:
                        keys[i]['dataLimit'] = key_info['dataLimit']
                except Exception as e:
                    logger.error(f"Error getting details for key {key['id']}: {e}")
        
        return keys
    
    def create_access_key(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Создать новый ключ доступа
        
        Args:
            name (str, optional): Имя для нового ключа
            
        Returns:
            dict: Информация о созданном ключе
        """
        data = {}
        if name:
            data['name'] = name
        
        return self._request('POST', '/access-keys', data)
    
    def delete_access_key(self, key_id: str) -> bool:
        """
        Удалить ключ доступа
        
        Args:
            key_id (str): ID ключа для удаления
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            self._request('DELETE', f'/access-keys/{key_id}')
            return True
        except Exception as e:
            logger.error(f"Error deleting access key {key_id}: {e}")
            return False
    
    def get_access_key(self, key_id: str) -> Dict[str, Any]:
        """
        Получить информацию о конкретном ключе доступа
        
        Args:
            key_id (str): ID ключа
            
        Returns:
            dict: Информация о ключе
        """
        return self._request('GET', f'/access-keys/{key_id}')
    
    def set_data_limit(self, key_id: str, limit_bytes: int) -> bool:
        """
        Установить лимит данных для ключа
        
        Args:
            key_id (str): ID ключа
            limit_bytes (int): Лимит в байтах (0 для снятия лимита)
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            logger.info(f"Setting data limit for key {key_id}: {limit_bytes} bytes")
            
            if limit_bytes > 0:
                logger.info(f"Sending PUT request to set limit to {limit_bytes} bytes")
                data = {
                    'limit': {
                        'bytes': limit_bytes
                    }
                }
                logger.info(f"Request data: {data}")
                
                response = self._request('PUT', f'/access-keys/{key_id}/data-limit', data)
                logger.info(f"Limit set response: {response}")
            else:
                # Удаляем лимит
                logger.info(f"Sending DELETE request to remove limit")
                response = self._request('DELETE', f'/access-keys/{key_id}/data-limit')
                logger.info(f"Limit removal response: {response}")
            
            # Проверяем, успешно ли установился лимит
            try:
                key_info = self.get_access_key(key_id)
                logger.info(f"Key info after setting limit: {key_info}")
                
                if limit_bytes > 0:
                    # Проверяем, установился ли лимит
                    if 'dataLimit' not in key_info or 'bytes' not in key_info['dataLimit']:
                        logger.error(f"Failed to set limit: dataLimit not found in response")
                        return False
                    
                    actual_limit = key_info['dataLimit']['bytes']
                    if actual_limit != limit_bytes:
                        logger.error(f"Limit mismatch: expected {limit_bytes}, got {actual_limit}")
                        return False
                else:
                    # Проверяем, удалился ли лимит
                    if 'dataLimit' in key_info:
                        logger.error(f"Failed to remove limit: dataLimit still present")
                        return False
                
            except Exception as e:
                logger.error(f"Error verifying limit change: {e}")
                # Возвращаем True, так как основной запрос мог пройти успешно
            
            return True
        except Exception as e:
            logger.error(f"Error setting data limit for key {key_id}: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Получить метрики по использованию сервера
        
        Returns:
            dict: Метрики сервера
        """
        logger.info(f"Запрашиваем метрики сервера")
        try:
            metrics = self._request('GET', '/metrics')
            logger.info(f"Получены метрики: {json.dumps(metrics, indent=2)}")
            return metrics
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return {}
    
    def get_server_transfer_stats(self) -> Dict[str, Any]:
        """
        Получить статистику передачи данных сервера через /metrics/transfer
        
        Returns:
            dict: Статистика передачи данных
        """
        logger.info(f"Запрашиваем статистику передачи данных через /metrics/transfer")
        try:
            # Правильный эндпоинт /metrics/transfer согласно API Outline Server
            stats = self._request('GET', '/metrics/transfer')
            logger.info(f"Получены данные о передаче: {json.dumps(stats, indent=2)}")
            return stats
        except Exception as e:
            logger.error(f"Error fetching transfer stats: {e}")
            return {}
    
    def get_key_data_usage(self, key_id: str) -> int:
        """
        Получить информацию о текущем использовании трафика для конкретного ключа
        
        Args:
            key_id (str): ID ключа
            
        Returns:
            int: Количество использованных байт
        """
        logger.info(f"Запрашиваем использование трафика для ключа {key_id}")
        
        # Метод 1: Запрос через /metrics/transfer (самый точный и рекомендуемый)
        try:
            transfer_stats = self.get_server_transfer_stats()
            logger.info(f"Анализируем transfer-stats на наличие данных для ключа {key_id}")
            
            if transfer_stats and 'bytesTransferredByUserId' in transfer_stats:
                # Данные приходят в формате {"bytesTransferredByUserId": {"28": 96775558316, ...}}
                user_stats = transfer_stats['bytesTransferredByUserId']
                
                # Проверяем, есть ли данные для нашего ключа
                if str(key_id) in user_stats:
                    data_usage = user_stats[str(key_id)]
                    # Используем правило 1 ГБ = 1,000,000,000 байтов
                    logger.info(f"Найдено использование трафика для ключа {key_id}: {data_usage} байт ({round(data_usage/1000000000, 2)} ГБ)")
                    return data_usage
                
                logger.info(f"Данные о трафике для ключа {key_id} не найдены в metrics/transfer. Доступные ключи: {list(user_stats.keys())}")
        except Exception as e:
            logger.error(f"Error getting traffic usage from metrics/transfer for key {key_id}: {e}")
        
        # Метод 2: Запрос через /metrics (может быть менее точным или отсутствовать)
        try:
            metrics = self.get_metrics()
            logger.info(f"Пробуем получить данные через /metrics для ключа {key_id}")
            
            if metrics and 'bytesTransferredByUserId' in metrics:
                user_metrics = metrics['bytesTransferredByUserId']
                
                # Проверяем, есть ли данные для нашего ключа
                if str(key_id) in user_metrics:
                    data_usage = user_metrics[str(key_id)]
                    # Используем правило 1 ГБ = 1,000,000,000 байтов
                    logger.info(f"Найдено использование трафика для ключа {key_id} через metrics: {data_usage} байт ({round(data_usage/1000000000, 2)} ГБ)")
                    return data_usage
                
                logger.info(f"Данные о трафике для ключа {key_id} не найдены в metrics")
        except Exception as e:
            logger.error(f"Error getting traffic usage from metrics for key {key_id}: {e}")
        
        # Метод 3: Прямой запрос ключа
        try:
            key_info = self.get_access_key(key_id)
            logger.info(f"Пробуем получить данные использования из прямого запроса ключа: {key_id}")
            logger.info(f"Данные ключа: {json.dumps(key_info, indent=2)}")
            
            # В некоторых версиях Outline VPN может быть доступно так
            if key_info and 'usageBytes' in key_info:
                usage = key_info.get('usageBytes', 0)
                logger.info(f"Найдено использование трафика в данных ключа: {usage} байт ({round(usage/1000000000, 2)} ГБ)")
                return usage
            
            if key_info and 'usage' in key_info and 'bytes' in key_info['usage']:
                usage = key_info['usage']['bytes'] 
                logger.info(f"Найдено использование трафика в данных ключа: {usage} байт ({round(usage/1000000000, 2)} ГБ)")
                return usage
        except Exception as e:
            logger.error(f"Error getting traffic usage from key info for key {key_id}: {e}")
        
        # Если не удалось получить данные ни через один метод
        logger.info(f"Не удалось получить данные о потреблении трафика для ключа {key_id}, возвращаем значение по умолчанию: 0")
        return 0
    
    def rename_server(self, name: str) -> bool:
        """
        Переименовать сервер
        
        Args:
            name (str): Новое имя сервера
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            self._request('PUT', '/name', {'name': name})
            return True
        except Exception as e:
            logger.error(f"Error renaming server: {e}")
            return False
    
    def rename_access_key(self, key_id: str, new_name: str) -> Dict[str, Any]:
        """
        Переименовать ключ доступа
        
        Args:
            key_id (str): ID ключа
            new_name (str): Новое имя для ключа
            
        Returns:
            dict: Результат операции
        """
        data = {'name': new_name}
        return self._request('PUT', f'/access-keys/{key_id}/name', data)
    
    def remove_data_limit(self) -> Dict[str, Any]:
        """
        Удалить лимит данных для всех ключей доступа
        
        Returns:
            dict: Результат операции
        """
        return self._request('DELETE', '/server/access-key-data-limit') 