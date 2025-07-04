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
            login_data = {"username": "admin", "password": "admin"}
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
            response = await client.get(f"{BASE_URL}/users/2", headers=auth_headers)
            if response.status_code == 200:
                user = response.json()
                results.add_test("Получение пользователя по ID", True, f"user_id=2, username={user.get('username')}")
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
                    "category_id": created_ids['category'],
                    "is_available": True,
                    "cooking_time": 15,
                    "calories": 350,
                    "weight": 250.0,
                    "main_image_url": "https://example.com/dish.jpg",
                    "sort_order": 1,
                    "is_popular": False,
                    "code": f"DISH_{int(time.time())}"
                }
                response = await client.post(f"{BASE_URL}/dishes/", json=new_dish_data, headers=auth_headers)
                if response.status_code in [200, 201]:  # Принимаем и 200 и 201
                    created_dish = response.json()
                    created_ids['dish'] = created_dish['id']
                    results.add_test("Создание блюда", True, f"dish_id={created_dish['id']} (код: {response.status_code})")
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
        
        # 7.5. ТЕСТИРОВАНИЕ ВАРИАЦИЙ БЛЮД
        print("\n🍽️ 7.5. ТЕСТИРОВАНИЕ ВАРИАЦИЙ БЛЮД")
        print("-" * 40)
        
        dish_variation_id = None
        
        if created_ids['dish']:
            # Получение списка вариаций блюда
            try:
                response = await client.get(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/", headers=auth_headers)
                if response.status_code == 200:
                    variations_data = response.json()
                    results.add_test("Список вариаций блюда", True, f"Всего: {variations_data['total']}")
                else:
                    results.add_test("Список вариаций блюда", False, f"Код ответа: {response.status_code}")
            except Exception as e:
                results.add_test("Список вариаций блюда", False, f"Ошибка: {str(e)}")
            
            # Создание новой вариации блюда
            try:
                new_variation_data = {
                    "name": f"Большая порция {int(time.time())}",
                    "description": "Увеличенная порция блюда",
                    "price": 399.99,
                    "weight": 350.0,
                    "calories": 450,
                    "is_default": True,
                    "is_available": True,
                    "sort_order": 1,
                    "sku": f"VAR_{int(time.time())}"
                }
                response = await client.post(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/", json=new_variation_data, headers=auth_headers)
                if response.status_code == 201:
                    created_variation = response.json()
                    dish_variation_id = created_variation['id']
                    results.add_test("Создание вариации блюда", True, f"variation_id={created_variation['id']}, price={created_variation['price']}")
                else:
                    results.add_test("Создание вариации блюда", False, f"Код ответа: {response.status_code}, ответ: {response.text}")
            except Exception as e:
                results.add_test("Создание вариации блюда", False, f"Ошибка: {str(e)}")
            
            # Получение вариации по ID
            if dish_variation_id:
                try:
                    response = await client.get(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/{dish_variation_id}", headers=auth_headers)
                    if response.status_code == 200:
                        variation = response.json()
                        results.add_test("Получение вариации по ID", True, f"variation_id={variation['id']}, name={variation['name']}")
                    else:
                        results.add_test("Получение вариации по ID", False, f"Код ответа: {response.status_code}")
                except Exception as e:
                    results.add_test("Получение вариации по ID", False, f"Ошибка: {str(e)}")
                
                # Обновление вариации
                try:
                    update_variation_data = {
                        "price": 449.99,
                        "description": "Обновленное описание вариации"
                    }
                    response = await client.patch(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/{dish_variation_id}", json=update_variation_data, headers=auth_headers)
                    if response.status_code == 200:
                        updated_variation = response.json()
                        results.add_test("Обновление вариации", True, f"new_price={updated_variation['price']}")
                    else:
                        results.add_test("Обновление вариации", False, f"Код ответа: {response.status_code}")
                except Exception as e:
                    results.add_test("Обновление вариации", False, f"Ошибка: {str(e)}")
                
                # Изменение доступности вариации
                try:
                    availability_data = {"is_available": False}
                    response = await client.patch(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/{dish_variation_id}/availability", json=availability_data, headers=auth_headers)
                    if response.status_code == 200:
                        availability_response = response.json()
                        results.add_test("Изменение доступности вариации", True, f"message: {availability_response.get('message', 'OK')}")
                    else:
                        results.add_test("Изменение доступности вариации", False, f"Код ответа: {response.status_code}")
                except Exception as e:
                    results.add_test("Изменение доступности вариации", False, f"Ошибка: {str(e)}")
        
        # Создание второй вариации для тестирования удаления
        second_variation_id = None
        if created_ids['dish']:
            try:
                second_variation_data = {
                    "name": f"Маленькая порция {int(time.time())}",
                    "description": "Уменьшенная порция блюда",
                    "price": 199.99,
                    "weight": 150.0,
                    "calories": 200,
                    "is_default": False,
                    "is_available": True,
                    "sort_order": 2,
                    "sku": f"VAR_SMALL_{int(time.time())}"
                }
                response = await client.post(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/", json=second_variation_data, headers=auth_headers)
                if response.status_code == 201:
                    second_variation = response.json()
                    second_variation_id = second_variation['id']
                    results.add_test("Создание второй вариации", True, f"variation_id={second_variation['id']}")
                else:
                    results.add_test("Создание второй вариации", False, f"Код ответа: {response.status_code}")
            except Exception as e:
                results.add_test("Создание второй вариации", False, f"Ошибка: {str(e)}")
        
        # Получение списка вариаций с фильтром (только доступные)
        if created_ids['dish']:
            try:
                response = await client.get(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/?available_only=true", headers=auth_headers)
                if response.status_code == 200:
                    filtered_variations = response.json()
                    results.add_test("Фильтр доступных вариаций", True, f"Доступных: {filtered_variations['total']}")
                else:
                    results.add_test("Фильтр доступных вариаций", False, f"Код ответа: {response.status_code}")
            except Exception as e:
                results.add_test("Фильтр доступных вариаций", False, f"Ошибка: {str(e)}")
        
        # Обновляем created_ids для очистки
        created_ids['dish_variation'] = dish_variation_id
        created_ids['second_dish_variation'] = second_variation_id

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
        if created_ids['table'] and created_ids['dish'] and created_ids.get('second_dish_variation'):
            try:
                new_order_data = {
                    "table_id": created_ids['table'],
                    "order_type": "dine_in",  # Добавляем тип заказа
                    "items": [
                        {
                            "dish_id": created_ids['dish'],
                            "dish_variation_id": created_ids['second_dish_variation'],  # Используем вторую вариацию, которая доступна
                            "quantity": 2,
                            "comment": "Без соли"
                        }
                    ],
                    "notes": "Тестовый заказ"
                }
                response = await client.post(f"{BASE_URL}/orders/", json=new_order_data, headers=auth_headers)
                if response.status_code == 201:
                    created_order = response.json()
                    created_ids['order'] = created_order['id']
                    results.add_test("Создание заказа", True, f"order_id={created_order['id']}, items={len(created_order.get('items', []))}")
                else:
                    results.add_test("Создание заказа", False, f"Код ответа: {response.status_code}, ответ: {response.text}")
            except Exception as e:
                results.add_test("Создание заказа", False, f"Ошибка: {str(e)}")
        
        # 11. ТЕСТИРОВАНИЕ ОШИБОК И ГРАНИЧНЫХ СЛУЧАЕВ
        print("\n⚠️ 11. ТЕСТИРОВАНИЕ ОШИБОК И ГРАНИЧНЫХ СЛУЧАЕВ")
        print("-" * 40)
        
        # Тест удаления единственной вариации блюда (должен завершиться ошибкой)
        if created_ids['dish'] and created_ids.get('dish_variation') and created_ids.get('second_dish_variation'):
            try:
                # Сначала удаляем вторую вариацию
                response = await client.delete(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/{created_ids['second_dish_variation']}", headers=auth_headers)
                if response.status_code == 200:
                    # Теперь пытаемся удалить последнюю вариацию (должен быть отказ)
                    response = await client.delete(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/{created_ids['dish_variation']}", headers=auth_headers)
                    if response.status_code == 400:
                        results.add_test("Защита от удаления единственной вариации", True, "Возвращает 400 как ожидается")
                    else:
                        results.add_test("Защита от удаления единственной вариации", False, f"Код ответа: {response.status_code}")
                    # Восстанавливаем вариацию для корректной очистки
                    created_ids['second_dish_variation'] = None
                else:
                    results.add_test("Удаление второй вариации для теста", False, f"Код ответа: {response.status_code}")
            except Exception as e:
                results.add_test("Защита от удаления единственной вариации", False, f"Ошибка: {str(e)}")
        
        # Тест создания вариации с дублирующимся SKU
        if created_ids['dish'] and created_ids.get('dish_variation'):
            try:
                duplicate_sku_data = {
                    "name": "Дублирующая вариация",
                    "description": "Тест дублирования SKU",
                    "price": 299.99,
                    "sku": f"VAR_{int(time.time())}_ORIG",  # Используем тот же SKU
                    "is_default": False,
                    "is_available": True,
                    "sort_order": 3
                }
                # Сначала создаем вариацию с уникальным SKU
                response1 = await client.post(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/", json=duplicate_sku_data, headers=auth_headers)
                if response1.status_code == 201:
                    temp_variation = response1.json()
                    # Теперь пытаемся создать вариацию с тем же SKU
                    response2 = await client.post(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/", json=duplicate_sku_data, headers=auth_headers)
                    if response2.status_code == 400:
                        results.add_test("Защита от дублирования SKU", True, "Возвращает 400 для дублирующего SKU")
                    else:
                        results.add_test("Защита от дублирования SKU", False, f"Код ответа: {response2.status_code}")
                    
                    # Удаляем временную вариацию
                    await client.delete(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/{temp_variation['id']}", headers=auth_headers)
                else:
                    results.add_test("Защита от дублирования SKU", False, f"Не удалось создать первую вариацию: {response1.status_code}")
            except Exception as e:
                results.add_test("Защита от дублирования SKU", False, f"Ошибка: {str(e)}")
        
        # Тест получения несуществующей вариации
        if created_ids['dish']:
            try:
                response = await client.get(f"{BASE_URL}/dishes/{created_ids['dish']}/variations/99999", headers=auth_headers)
                if response.status_code == 404:
                    results.add_test("Несуществующая вариация", True, "Возвращает 404")
                else:
                    results.add_test("Несуществующая вариация", False, f"Код ответа: {response.status_code}")
            except Exception as e:
                results.add_test("Несуществующая вариация", False, f"Ошибка: {str(e)}")
        
        # Тест вариации для несуществующего блюда
        try:
            response = await client.get(f"{BASE_URL}/dishes/99999/variations/", headers=auth_headers)
            if response.status_code == 404:
                results.add_test("Вариации несуществующего блюда", True, "Возвращает 404")
            else:
                results.add_test("Вариации несуществующего блюда", False, f"Код ответа: {response.status_code}")
        except Exception as e:
            results.add_test("Вариации несуществующего блюда", False, f"Ошибка: {str(e)}")

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
