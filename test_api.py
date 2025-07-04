#!/usr/bin/env python3
"""
QRes OS 4 - Comprehensive API Test Script
Максимально дотошный скрипт для проверки всех эндпоинтов API
"""
import asyncio
import httpx
import json
import time
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = 0
        self.test_details = []
    
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
        print("=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
        print("=" * 60)
        print(f"Всего тестов: {self.total_tests}")
        print(f"Успешно: {self.passed_tests} ✅")
        print(f"Неудачно: {self.failed_tests} ❌")
        print(f"Предупреждения: {self.warnings} ⚠️")
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Успешность: {success_rate:.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for detail in self.test_details:
                if detail.startswith("❌"):
                    print(f"  {detail}")

results = TestResults()

async def comprehensive_api_test():
    """Максимально дотошное тестирование всех эндпоинтов API"""
    # Создаем клиента с большим таймаутом и без прокси
    timeout = httpx.Timeout(30.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout, proxies={}) as client:
        print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ QRes OS 4 API")
        print("=" * 60)
        
        # Переменные для хранения данных между тестами
        auth_token = None
        auth_headers = {}
        created_ids = {
            'location': None,
            'category': None,
            'dish': None,
            'ingredient': None,
            'table': None,
            'order': None,
            'user': None,
            'payment_method': None
        }
        
        # 1. БАЗОВЫЕ ПРОВЕРКИ
        print("\n🔍 1. БАЗОВЫЕ ПРОВЕРКИ СЕРВЕРА")
        print("-" * 40)
        
        # Health Check
        try:
            start_time = time.time()
            response = await client.get(f"{BASE_URL}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results.add_test(
                    "Health Check", 
                    True, 
                    f"status={data['status']}, uptime={data['uptime']:.2f}s, response_time={response_time:.3f}s"
                )
                
                # Проверяем структуру ответа
                expected_fields = ['status', 'version', 'database', 'uptime']
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    results.add_test(
                        "Health Check Structure", 
                        False, 
                        f"Отсутствуют поля: {missing_fields}"
                    )
                else:
                    results.add_test("Health Check Structure", True, "Все поля присутствуют")
                    
            else:
                results.add_test("Health Check", False, f"Код ответа: {response.status_code}")
                
        except Exception as e:
            results.add_test("Health Check", False, f"Ошибка: {str(e)}")
        
        # Проверка документации
        try:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                results.add_test("Swagger UI", True, "Документация доступна")
            else:
                results.add_test("Swagger UI", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Swagger UI", False, f"Ошибка: {str(e)}")
        
        # Проверка ReDoc
        try:
            response = await client.get(f"{BASE_URL}/redoc")
            if response.status_code == 200:
                results.add_test("ReDoc UI", True, "ReDoc документация доступна")
            else:
                results.add_test("ReDoc UI", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("ReDoc UI", False, f"Ошибка: {str(e)}")
        
        # Проверка OpenAPI схемы
        try:
            response = await client.get(f"{BASE_URL}/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                results.add_test("OpenAPI Schema", True, f"Схема содержит {len(schema.get('paths', {}))} путей")
            else:
                results.add_test("OpenAPI Schema", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("OpenAPI Schema", False, f"Ошибка: {str(e)}")
        
        # 2. ТЕСТИРОВАНИЕ АУТЕНТИФИКАЦИИ
        print("\n🔐 2. ТЕСТИРОВАНИЕ АУТЕНТИФИКАЦИИ")
        print("-" * 40)
        
        
        # Неправильные учетные данные
        try:
            login_data = {"username": "admin", "password": "wrong_password"}
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 401:
                results.add_test("Неправильный пароль", True, "Возвращает 401 как ожидается")
            else:
                results.add_test("Неправильный пароль", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Неправильный пароль", False, f"Ошибка: {str(e)}")
        
        # Правильные учетные данные
        try:
            login_data = {"username": "admin", "password": "admin123"}
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                auth_token = token_data['access_token']
                auth_headers = {"Authorization": f"Bearer {auth_token}"}
                results.add_test("Успешная аутентификация", True, f"Токен получен, expires_in={token_data.get('expires_in')}s")
                
                # Проверяем структуру токена
                expected_fields = ['access_token', 'token_type', 'expires_in']
                missing_fields = [field for field in expected_fields if field not in token_data]
                if missing_fields:
                    results.add_test("Структура токена", False, f"Отсутствуют поля: {missing_fields}")
                else:
                    results.add_test("Структура токена", True, "Все поля присутствуют")
            else:
                results.add_test("Успешная аутентификация", False, f"Код ответа: {response.status_code}")
                return  # Без токена дальше тестировать нельзя
        except Exception as e:
            results.add_test("Успешная аутентификация", False, f"Ошибка: {str(e)}")
            return
        
        # Проверка текущего пользователя
        try:
            response = await client.get(f"{BASE_URL}/auth/me", headers=auth_headers)
            if response.status_code == 200:
                user_data = response.json()
                results.add_test("Получение текущего пользователя", True, f"user={user_data['username']}, role={user_data['role']}")
            else:
                results.add_test("Получение текущего пользователя", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Получение текущего пользователя", False, f"Ошибка: {str(e)}")
        
        # Проверка неправильного токена
        try:
            wrong_headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get(f"{BASE_URL}/auth/me", headers=wrong_headers)
            if response.status_code == 401:
                results.add_test("Неправильный токен", True, "Возвращает 401 как ожидается")
            else:
                results.add_test("Неправильный токен", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Неправильный токен", False, f"Ошибка: {str(e)}")
        
        # PIN-код аутентификация
        try:
            pin_data = {"username": "admin", "pin_code": "1234"}
            response = await client.post(f"{BASE_URL}/auth/login/pin", json=pin_data)
            if response.status_code in [200, 401]:  # 401 ожидается если PIN не установлен
                results.add_test("PIN аутентификация", True, f"Эндпоинт работает, код: {response.status_code}")
            else:
                results.add_test("PIN аутентификация", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("PIN аутентификация", False, f"Ошибка: {str(e)}")
        
        # 3. ТЕСТИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ
        print("\n👥 3. ТЕСТИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ")
        print("-" * 40)
        
        # Получение списка пользователей
        try:
            response = await client.get(f"{BASE_URL}/users/", headers=auth_headers)
            if response.status_code == 200:
                users_data = response.json()
                results.add_test("Список пользователей", True, f"Всего: {users_data['total']}, получено: {len(users_data['users'])}")
            else:
                results.add_test("Список пользователей", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список пользователей", False, f"Ошибка: {str(e)}")
        
        # Получение пользователя по ID
        try:
            response = await client.get(f"{BASE_URL}/users/1", headers=auth_headers)
            if response.status_code == 200:
                user = response.json()
                results.add_test("Получение пользователя по ID", True, f"user_id=1, username={user.get('username')}")
            else:
                results.add_test("Получение пользователя по ID", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Получение пользователя по ID", False, f"Ошибка: {str(e)}")
        
        # Создание нового пользователя
        try:
            # Используем уникальный PIN-код для каждого теста
            unique_pin = str(int(time.time()) % 10000).zfill(4)
            new_user_data = {
                "username": f"test_user_{int(time.time())}",
                "password": "test123456",
                "full_name": "Тестовый Пользователь",
                "role": "waiter",
                "phone": "+7900123456",
                "pin_code": unique_pin
            }
            response = await client.post(f"{BASE_URL}/users/", json=new_user_data, headers=auth_headers)
            if response.status_code == 201:
                created_user = response.json()
                created_ids['user'] = created_user['id']
                results.add_test("Создание пользователя", True, f"user_id={created_user['id']}, username={created_user['username']}")
            else:
                results.add_test("Создание пользователя", False, f"Код ответа: {response.status_code}, ответ: {response.text}")
        except Exception as e:
            results.add_test("Создание пользователя", False, f"Ошибка: {str(e)}")
        
        # 4. ТЕСТИРОВАНИЕ ЛОКАЦИЙ
        print("\n🏢 4. ТЕСТИРОВАНИЕ ЛОКАЦИЙ")
        print("-" * 40)
        
        # Получение списка локаций
        try:
            response = await client.get(f"{BASE_URL}/locations/", headers=auth_headers)
            if response.status_code == 200:
                locations_data = response.json()
                results.add_test("Список локаций", True, f"Всего: {locations_data['total']}")
            else:
                results.add_test("Список локаций", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список локаций", False, f"Ошибка: {str(e)}")
        
        # Создание новой локации
        try:
            new_location_data = {
                "name": f"Тестовая локация {int(time.time())}",
                "address": "Тестовый адрес, 123",
                "phone": "+7900123456",
                "is_active": True
            }
            response = await client.post(f"{BASE_URL}/locations/", json=new_location_data, headers=auth_headers)
            if response.status_code in [200, 201]:  # Принимаем и 200 и 201
                created_location = response.json()
                created_ids['location'] = created_location['id']
                results.add_test("Создание локации", True, f"location_id={created_location['id']} (код: {response.status_code})")
            else:
                results.add_test("Создание локации", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Создание локации", False, f"Ошибка: {str(e)}")
        
        # 5. ТЕСТИРОВАНИЕ СТОЛОВ
        print("\n🪑 5. ТЕСТИРОВАНИЕ СТОЛОВ")
        print("-" * 40)
        
        # Получение списка столов
        try:
            response = await client.get(f"{BASE_URL}/tables/", headers=auth_headers)
            if response.status_code == 200:
                tables_data = response.json()
                results.add_test("Список столов", True, f"Всего: {tables_data['total']}")
            else:
                results.add_test("Список столов", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список столов", False, f"Ошибка: {str(e)}")
        
        # Создание нового стола
        if created_ids['location']:
            try:
                new_table_data = {
                    "number": int(time.time()) % 1000,  # int вместо string
                    "seats": 4,  # seats вместо capacity
                    "location_id": created_ids['location'],
                    "is_active": True
                }
                response = await client.post(f"{BASE_URL}/tables/", json=new_table_data, headers=auth_headers)
                if response.status_code in [200, 201]:  # Принимаем и 200 и 201
                    created_table = response.json()
                    created_ids['table'] = created_table['id']
                    results.add_test("Создание стола", True, f"table_id={created_table['id']}, number={created_table['number']} (код: {response.status_code})")
                else:
                    results.add_test("Создание стола", False, f"Код ответа: {response.status_code}, ответ: {response.text}")
            except Exception as e:
                results.add_test("Создание стола", False, f"Ошибка: {str(e)}")
        
        # 6. ТЕСТИРОВАНИЕ КАТЕГОРИЙ
        print("\n📂 6. ТЕСТИРОВАНИЕ КАТЕГОРИЙ")
        print("-" * 40)
        
        # Получение списка категорий
        try:
            response = await client.get(f"{BASE_URL}/categories/", headers=auth_headers)
            if response.status_code == 200:
                categories_data = response.json()
                results.add_test("Список категорий", True, f"Всего: {categories_data['total']}")
            else:
                results.add_test("Список категорий", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список категорий", False, f"Ошибка: {str(e)}")
        
        # Создание новой категории
        try:
            new_category_data = {
                "name": f"Тестовая категория {int(time.time())}",
                "description": "Описание тестовой категории",
                "is_active": True,
                "sort_order": 99
            }
            response = await client.post(f"{BASE_URL}/categories/", json=new_category_data, headers=auth_headers)
            if response.status_code in [200, 201]:  # Принимаем и 200 и 201
                created_category = response.json()
                created_ids['category'] = created_category['id']
                results.add_test("Создание категории", True, f"category_id={created_category['id']} (код: {response.status_code})")
            else:
                results.add_test("Создание категории", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Создание категории", False, f"Ошибка: {str(e)}")
        
        # 7. ТЕСТИРОВАНИЕ БЛЮД
        print("\n🍽️ 7. ТЕСТИРОВАНИЕ БЛЮД")
        print("-" * 40)
        
        # Получение списка блюд
        try:
            response = await client.get(f"{BASE_URL}/dishes/", headers=auth_headers)
            if response.status_code == 200:
                dishes_data = response.json()
                results.add_test("Список блюд", True, f"Всего: {dishes_data['total']}")
            else:
                results.add_test("Список блюд", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список блюд", False, f"Ошибка: {str(e)}")
        
        # Создание нового блюда
        if created_ids['category']:
            try:
                new_dish_data = {
                    "name": f"Тестовое блюдо {int(time.time())}",
                    "description": "Описание тестового блюда",
                    "price": 299.99,
                    "category_id": created_ids['category'],
                    "is_available": True,
                    "cooking_time": 15,
                    "calories": 350,
                    "weight": 250
                }
                response = await client.post(f"{BASE_URL}/dishes/", json=new_dish_data, headers=auth_headers)
                if response.status_code in [200, 201]:  # Принимаем и 200 и 201
                    created_dish = response.json()
                    created_ids['dish'] = created_dish['id']
                    results.add_test("Создание блюда", True, f"dish_id={created_dish['id']}, price={created_dish['price']} (код: {response.status_code})")
                else:
                    results.add_test("Создание блюда", False, f"Код ответа: {response.status_code}, ответ: {response.text}")
            except Exception as e:
                results.add_test("Создание блюда", False, f"Ошибка: {str(e)}")
        
        # Публичное меню
        try:
            response = await client.get(f"{BASE_URL}/dishes/menu")
            if response.status_code == 200:
                menu_data = response.json()
                results.add_test("Публичное меню", True, f"Категорий: {len(menu_data.get('categories', []))}")
            else:
                results.add_test("Публичное меню", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Публичное меню", False, f"Ошибка: {str(e)}")
        
        # 8. ТЕСТИРОВАНИЕ ИНГРЕДИЕНТОВ
        print("\n🥕 8. ТЕСТИРОВАНИЕ ИНГРЕДИЕНТОВ")
        print("-" * 40)
        
        # Получение списка ингредиентов
        try:
            response = await client.get(f"{BASE_URL}/ingredients/", headers=auth_headers)
            if response.status_code == 200:
                ingredients_data = response.json()
                results.add_test("Список ингредиентов", True, f"Всего: {ingredients_data['total']}")
            else:
                results.add_test("Список ингредиентов", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список ингредиентов", False, f"Ошибка: {str(e)}")
        
        # Создание нового ингредиента
        try:
            new_ingredient_data = {
                "name": f"Тестовый ингредиент {int(time.time())}",
                "unit": "шт",
                "cost_per_unit": 5.50,
                "current_stock": 100,
                "min_stock": 10,
                "is_active": True
            }
            response = await client.post(f"{BASE_URL}/ingredients/", json=new_ingredient_data, headers=auth_headers)
            if response.status_code in [200, 201]:  # Принимаем и 200 и 201
                created_ingredient = response.json()
                created_ids['ingredient'] = created_ingredient['id']
                results.add_test("Создание ингредиента", True, f"ingredient_id={created_ingredient['id']} (код: {response.status_code})")
            else:
                results.add_test("Создание ингредиента", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Создание ингредиента", False, f"Ошибка: {str(e)}")
        
        # 9. ТЕСТИРОВАНИЕ СПОСОБОВ ОПЛАТЫ
        print("\n💳 9. ТЕСТИРОВАНИЕ СПОСОБОВ ОПЛАТЫ")
        print("-" * 40)
        
        # Получение списка способов оплаты
        try:
            response = await client.get(f"{BASE_URL}/payment-methods/", headers=auth_headers)
            if response.status_code == 200:
                payment_data = response.json()
                results.add_test("Список способов оплаты", True, f"Всего: {payment_data['total']}")
            else:
                results.add_test("Список способов оплаты", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список способов оплаты", False, f"Ошибка: {str(e)}")
        
        # 10. ТЕСТИРОВАНИЕ ЗАКАЗОВ
        print("\n📋 10. ТЕСТИРОВАНИЕ ЗАКАЗОВ")
        print("-" * 40)
        
        # Получение списка заказов
        try:
            response = await client.get(f"{BASE_URL}/orders/", headers=auth_headers)
            if response.status_code == 200:
                orders_data = response.json()
                results.add_test("Список заказов", True, f"Всего: {orders_data['total']}")
            else:
                results.add_test("Список заказов", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Список заказов", False, f"Ошибка: {str(e)}")
        
        # Создание нового заказа
        if created_ids['table'] and created_ids['dish']:
            try:
                new_order_data = {
                    "table_id": created_ids['table'],
                    "items": [
                        {
                            "dish_id": created_ids['dish'],
                            "quantity": 2,
                            "comment": "Без соли"  # Исправляем поле на comment
                        }
                    ],
                    "notes": "Тестовый заказ"  # Исправляем поле на notes
                }
                response = await client.post(f"{BASE_URL}/orders/", json=new_order_data, headers=auth_headers)
                if response.status_code == 201:
                    created_order = response.json()
                    created_ids['order'] = created_order['id']
                    results.add_test("Создание заказа", True, f"order_id={created_order['id']}, items={len(created_order.get('items', []))}")
                else:
                    results.add_test("Создание заказа", False, f"Код ответа: {response.status_code}")
            except Exception as e:
                results.add_test("Создание заказа", False, f"Ошибка: {str(e)}")
        
        # 11. ТЕСТИРОВАНИЕ ОШИБОК И ГРАНИЧНЫХ СЛУЧАЕВ
        print("\n⚠️ 11. ТЕСТИРОВАНИЕ ОШИБОК И ГРАНИЧНЫХ СЛУЧАЕВ")
        print("-" * 40)
        
        # Несуществующий эндпоинт
        try:
            response = await client.get(f"{BASE_URL}/nonexistent")
            if response.status_code == 404:
                results.add_test("Несуществующий эндпоинт", True, "Возвращает 404")
            else:
                results.add_test("Несуществующий эндпоинт", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Несуществующий эндпоинт", False, f"Ошибка: {str(e)}")
        
        # Запрос без авторизации к защищенному эндпоинту
        try:
            response = await client.get(f"{BASE_URL}/users/")
            if response.status_code in [401, 403]:  # Принимаем и 401 и 403
                results.add_test("Запрос без авторизации", True, f"Возвращает {response.status_code}")
            else:
                results.add_test("Запрос без авторизации", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Запрос без авторизации", False, f"Ошибка: {str(e)}")
        
        # Несуществующий ресурс
        try:
            response = await client.get(f"{BASE_URL}/users/99999", headers=auth_headers)
            if response.status_code == 404:
                results.add_test("Несуществующий пользователь", True, "Возвращает 404")
            else:
                results.add_test("Несуществующий пользователь", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Несуществующий пользователь", False, f"Ошибка: {str(e)}")
        
        # Некорректные данные при создании
        try:
            invalid_user_data = {
                "username": "",  # Пустое имя
                "password": "123",  # Слишком короткий пароль
                "full_name": "",
                "role": "invalid_role"
            }
            response = await client.post(f"{BASE_URL}/users/", json=invalid_user_data, headers=auth_headers)
            if response.status_code == 422:
                results.add_test("Валидация данных", True, "Возвращает 422 для некорректных данных")
            else:
                results.add_test("Валидация данных", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Валидация данных", False, f"Ошибка: {str(e)}")
        
        # 12. ОЧИСТКА СОЗДАННЫХ ДАННЫХ
        print("\n🧹 12. ОЧИСТКА СОЗДАННЫХ ДАННЫХ")
        print("-" * 40)
        
        # Удаляем созданные данные в обратном порядке
        cleanup_order = ['order', 'dish', 'ingredient', 'table', 'category', 'location', 'user']
        
        for resource_type in cleanup_order:
            resource_id = created_ids.get(resource_type)
            if resource_id:
                try:
                    endpoint_map = {
                        'user': 'users',
                        'location': 'locations', 
                        'category': 'categories',
                        'dish': 'dishes',
                        'ingredient': 'ingredients',
                        'table': 'tables',
                        'order': 'orders'
                    }
                    endpoint = endpoint_map.get(resource_type)
                    if endpoint:
                        response = await client.delete(f"{BASE_URL}/{endpoint}/{resource_id}", headers=auth_headers)
                        if response.status_code in [200, 204]:
                            results.add_test(f"Удаление {resource_type}", True, f"ID={resource_id}")
                        else:
                            results.add_test(f"Удаление {resource_type}", False, f"Код ответа: {response.status_code}")
                except Exception as e:
                    results.add_test(f"Удаление {resource_type}", False, f"Ошибка: {str(e)}")
        
        # Выводим итоговую статистику
        results.print_summary()
        
        print("\n📖 Полная документация API: http://localhost:8000/docs")
        print("🔄 ReDoc документация: http://localhost:8000/redoc")

if __name__ == "__main__":
    asyncio.run(comprehensive_api_test())
