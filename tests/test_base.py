#!/usr/bin/env python3
"""
QRes OS 4 - Base Test Classes
Базовые классы для тестирования системы
"""
import asyncio
import httpx
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class TestResults:
    """Класс для сбора результатов тестирования"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = 0
        self.test_details = []
        self.start_time = datetime.now()
    
    def add_test(self, name: str, passed: bool, details: str = "", warning: bool = False):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅"
        else:
            self.failed_tests += 1
            status = "❌"
        
        if warning:
            self.warnings += 1
            status = "⚠️"
        
        self.test_details.append(f"{status} {name}: {details}")
        print(f"{status} {name}: {details}")
    
    def print_summary(self):
        duration = datetime.now() - self.start_time
        print("\n" + "=" * 80)
        print("📊 ИТОГОВАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
        print("=" * 80)
        print(f"Всего тестов: {self.total_tests}")
        print(f"Успешно: {self.passed_tests} ✅")
        print(f"Неудачно: {self.failed_tests} ❌")
        print(f"Предупреждения: {self.warnings} ⚠️")
        print(f"Время выполнения: {duration.total_seconds():.2f} сек")
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Успешность: {success_rate:.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for detail in self.test_details:
                if "❌" in detail:
                    print(f"  {detail}")


class TestRunner:
    """Главный класс для управления тестированием"""
    
    BASE_URL = "http://localhost:8000"
    
    def __init__(self):
        self.client = None
        self.results = TestResults()
        self.test_prefix = f"test_{uuid.uuid4().hex[:8]}_"
        self.created_data = {
            'users': [],
            'locations': [],
            'tables': [],
            'categories': [],
            'ingredients': [],
            'dishes': [],
            'dish_variations': [],
            'payment_methods': [],
            'orders': [],
            'order_items': []
        }
        self.auth_token = None
        self.test_user_id = None
    
    async def initialize(self):
        """Инициализация подключения и проверка готовности сервера"""
        self.client = httpx.AsyncClient(timeout=30.0)
        
        try:
            response = await self.client.get(f"{self.BASE_URL}/")
            if response.status_code == 200:
                self.results.add_test("Подключение к серверу", True, "Сервер доступен")
            else:
                self.results.add_test("Подключение к серверу", False, f"Код ответа: {response.status_code}")
                return False
        except Exception as e:
            self.results.add_test("Подключение к серверу", False, f"Ошибка подключения: {str(e)}")
            return False
        
        return True
    
    async def setup_test_data(self):
        """Создание базовых тестовых данных"""
        # Создаем тестового пользователя
        await self.create_test_user()
        
        # Получаем токен авторизации
        await self.authenticate()
    
    async def create_test_user(self):
        """Создание тестового пользователя"""
        user_data = {
            "username": f"{self.test_prefix}testuser",
            "email": f"{self.test_prefix}test@example.com",
            "password": "testpassword123",
            "full_name": f"Test User {self.test_prefix}",
            "role": "admin"
        }
        
        try:
            response = await self.client.post(f"{self.BASE_URL}/users/", json=user_data)
            if response.status_code == 201:
                user = response.json()
                self.test_user_id = user["id"]
                self.created_data['users'].append(user["id"])
                self.results.add_test("Создание тестового пользователя", True, f"ID: {user['id']}")
                return user
            else:
                self.results.add_test("Создание тестового пользователя", False, f"Код: {response.status_code}, Ответ: {response.text}")
                return None
        except Exception as e:
            self.results.add_test("Создание тестового пользователя", False, f"Ошибка: {str(e)}")
            return None
    
    async def authenticate(self):
        """Получение токена авторизации"""
        auth_data = {
            "username": f"{self.test_prefix}testuser",
            "password": "testpassword123"
        }
        
        try:
            response = await self.client.post(f"{self.BASE_URL}/auth/login", data=auth_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.results.add_test("Авторизация", True, "Токен получен")
                return True
            else:
                self.results.add_test("Авторизация", False, f"Код: {response.status_code}")
                return False
        except Exception as e:
            self.results.add_test("Авторизация", False, f"Ошибка: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Получение заголовков авторизации"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def cleanup_test_data(self):
        """Очистка всех созданных тестовых данных"""
        print("\n🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        print("=" * 50)
        
        cleanup_order = [
            'order_items', 'orders', 'dish_variations', 'dishes', 
            'ingredients', 'categories', 'tables', 'locations', 
            'payment_methods', 'users'
        ]
        
        headers = self.get_auth_headers()
        
        for data_type in cleanup_order:
            items = self.created_data.get(data_type, [])
            if not items:
                continue
            
            print(f"Очистка {data_type}: {len(items)} элементов")
            
            for item_id in items:
                try:
                    endpoint = self.get_endpoint_for_type(data_type)
                    response = await self.client.delete(f"{self.BASE_URL}/{endpoint}/{item_id}", headers=headers)
                    if response.status_code not in [200, 204, 404]:
                        print(f"  ⚠️ Не удалось удалить {data_type} {item_id}: {response.status_code}")
                    else:
                        print(f"  ✅ Удален {data_type} {item_id}")
                except Exception as e:
                    print(f"  ❌ Ошибка при удалении {data_type} {item_id}: {str(e)}")
        
        print("🧹 Очистка завершена")
    
    def get_endpoint_for_type(self, data_type: str) -> str:
        """Получение endpoint для типа данных"""
        endpoints = {
            'users': 'users',
            'locations': 'locations',
            'tables': 'tables',
            'categories': 'categories',
            'ingredients': 'ingredients',
            'dishes': 'dishes',
            'dish_variations': 'dishes/variations',
            'payment_methods': 'payment-methods',
            'orders': 'orders',
            'order_items': 'orders/items'
        }
        return endpoints.get(data_type, data_type)
    
    async def close(self):
        """Закрытие соединений"""
        if self.client:
            await self.client.aclose()
    
    async def setup(self):
        """Полная настройка тестового окружения"""
        success = await self.initialize()
        if success:
            await self.setup_test_data()
        return success
    
    async def teardown(self):
        """Полная очистка тестового окружения"""
        await self.cleanup_test_data()
        if self.client:
            await self.client.aclose()


class BaseTestSuite:
    """Базовый класс для тестовых сюитов"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.client = runner.client
        self.results = runner.results
        self.test_prefix = runner.test_prefix
        self.created_data = runner.created_data
    
    def get_auth_headers(self) -> Dict[str, str]:
        return self.runner.get_auth_headers()
    
    async def test_crud_operations(self, endpoint: str, create_data: Dict, update_data: Dict, 
                                 data_type: str, required_fields: List[str] = None):
        """Базовый тест CRUD операций"""
        headers = self.get_auth_headers()
        
        # CREATE
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/{endpoint}", 
                                           json=create_data, headers=headers)
            if response.status_code == 201:
                created_item = response.json()
                item_id = created_item["id"]
                self.created_data[data_type].append(item_id)
                self.results.add_test(f"CREATE {data_type}", True, f"ID: {item_id}")
                
                # Проверяем обязательные поля
                if required_fields:
                    for field in required_fields:
                        if field not in created_item:
                            self.results.add_test(f"CREATE {data_type} - поле {field}", False, 
                                                "Отсутствует обязательное поле")
                        else:
                            self.results.add_test(f"CREATE {data_type} - поле {field}", True, 
                                                f"Значение: {created_item[field]}")
                
            else:
                self.results.add_test(f"CREATE {data_type}", False, 
                                    f"Код: {response.status_code}, Ответ: {response.text}")
                return None
        except Exception as e:
            self.results.add_test(f"CREATE {data_type}", False, f"Ошибка: {str(e)}")
            return None
        
        # READ
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/{endpoint}/{item_id}", 
                                          headers=headers)
            if response.status_code == 200:
                self.results.add_test(f"READ {data_type}", True, f"Получен объект ID: {item_id}")
            else:
                self.results.add_test(f"READ {data_type}", False, f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test(f"READ {data_type}", False, f"Ошибка: {str(e)}")
        
        # UPDATE
        try:
            response = await self.client.put(f"{self.runner.BASE_URL}/{endpoint}/{item_id}", 
                                          json=update_data, headers=headers)
            if response.status_code == 200:
                self.results.add_test(f"UPDATE {data_type}", True, f"Обновлен объект ID: {item_id}")
            else:
                self.results.add_test(f"UPDATE {data_type}", False, f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test(f"UPDATE {data_type}", False, f"Ошибка: {str(e)}")
        
        # LIST
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/{endpoint}", 
                                          headers=headers)
            if response.status_code == 200:
                items = response.json()
                self.results.add_test(f"LIST {data_type}", True, f"Получено {len(items)} объектов")
            else:
                self.results.add_test(f"LIST {data_type}", False, f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test(f"LIST {data_type}", False, f"Ошибка: {str(e)}")
        
        return item_id
    
    async def run_tests(self):
        """Запуск всех тестов сюита (переопределяется в наследниках)"""
        raise NotImplementedError("Метод run_tests должен быть переопределен в наследнике")
