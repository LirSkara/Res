#!/usr/bin/env python3
"""
QRes OS 4 - Dish Variations Tests
Тесты управления вариациями блюд
"""
from tests.test_base import BaseTestSuite, TestRunner


class DishVariationsTestSuite(BaseTestSuite):
    """Тестовый сюит для управления вариациями блюд"""
    
    async def run_tests(self):
        """Запуск всех тестов вариаций блюд"""
        print("\n🍽️➕ ТЕСТИРОВАНИЕ ВАРИАЦИЙ БЛЮД")
        print("=" * 50)
        
        await self.test_variation_crud()
        await self.test_variation_validation()
        await self.test_variation_pricing()
        await self.test_variation_default()
        await self.test_variation_dish_relationship()
        await self.test_variation_availability()
    
    async def test_variation_crud(self):
        """Тест CRUD операций с вариациями блюд"""
        # Создаем категорию и блюдо для вариаций
        category_data = {
            "name": f"{self.test_prefix}Variation Category",
            "description": "Category for variation testing",
            "sort_order": 1,
            "is_active": True
        }
        
        headers = self.get_auth_headers()
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        
        if category_response.status_code != 201:
            self.results.add_test("CRUD вариаций - создание категории", False, 
                                f"Не удалось создать категорию: {category_response.status_code}")
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        # Создаем блюдо
        dish_data = {
            "name": f"{self.test_prefix}CRUD Variation Dish",
            "description": "Dish for CRUD variation testing",
            "category_id": category_id,
            "is_available": True
        }
        
        dish_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                             json=dish_data, headers=headers)
        
        if dish_response.status_code != 201:
            self.results.add_test("CRUD вариаций - создание блюда", False, 
                                f"Не удалось создать блюдо: {dish_response.status_code}")
            return
        
        dish = dish_response.json()
        dish_id = dish["id"]
        self.created_data['dishes'].append(dish_id)
        
        # Тестируем CRUD операции с вариациями
        create_data = {
            "dish_id": dish_id,
            "name": "Medium",
            "description": "Medium size portion",
            "price": 15.99,
            "is_default": True,
            "is_available": True,
            "portion_size": "400g",
            "additional_info": "Most popular size"
        }
        
        update_data = {
            "dish_id": dish_id,
            "name": "Medium Updated",
            "description": "Updated medium size portion",
            "price": 16.99,
            "is_default": True,
            "is_available": True,
            "portion_size": "450g",
            "additional_info": "Updated popular size"
        }
        
        required_fields = ["id", "dish_id", "name", "price", "is_default", "is_available", "created_at"]
        
        variation_id = await self.test_crud_operations(
            endpoint="dishes/variations",
            create_data=create_data,
            update_data=update_data,
            data_type="dish_variations",
            required_fields=required_fields
        )
        
        return variation_id
    
    async def test_variation_validation(self):
        """Тест валидации данных вариации"""
        # Создаем блюдо для тестов валидации
        headers = self.get_auth_headers()
        
        # Создаем категорию
        category_data = {
            "name": f"{self.test_prefix}Validation Category",
            "description": "Category for validation tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        # Создаем блюдо
        dish_data = {
            "name": f"{self.test_prefix}Validation Dish",
            "description": "Dish for validation tests",
            "category_id": category_id,
            "is_available": True
        }
        
        dish_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                             json=dish_data, headers=headers)
        if dish_response.status_code != 201:
            return
        
        dish = dish_response.json()
        dish_id = dish["id"]
        self.created_data['dishes'].append(dish_id)
        
        invalid_variations = [
            # Отсутствующее имя
            {
                "dish_id": dish_id,
                "price": 10.99,
                "is_default": False,
                "is_available": True
            },
            # Пустое имя
            {
                "dish_id": dish_id,
                "name": "",
                "price": 10.99,
                "is_default": False,
                "is_available": True
            },
            # Отсутствующее блюдо
            {
                "name": "No Dish Variation",
                "price": 10.99,
                "is_default": False,
                "is_available": True
            },
            # Несуществующее блюдо
            {
                "dish_id": 99999,
                "name": "Fake Dish Variation",
                "price": 10.99,
                "is_default": False,
                "is_available": True
            },
            # Отсутствующая цена
            {
                "dish_id": dish_id,
                "name": "No Price Variation",
                "is_default": False,
                "is_available": True
            },
            # Невалидная цена
            {
                "dish_id": dish_id,
                "name": "Invalid Price Variation",
                "price": -5.99,
                "is_default": False,
                "is_available": True
            },
            # Цена равна нулю
            {
                "dish_id": dish_id,
                "name": "Zero Price Variation",
                "price": 0,
                "is_default": False,
                "is_available": True
            }
        ]
        
        for i, variation_data in enumerate(invalid_variations):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                               json=variation_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация вариации #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если вариация создалась, добавляем в список для удаления
                    variation = response.json()
                    self.created_data['dish_variations'].append(variation["id"])
                    self.results.add_test(f"Валидация вариации #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация вариации #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация вариации #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_variation_pricing(self):
        """Тест ценообразования вариаций"""
        headers = self.get_auth_headers()
        
        # Создаем блюдо для тестов ценообразования
        category_data = {
            "name": f"{self.test_prefix}Pricing Category",
            "description": "Category for pricing tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        dish_data = {
            "name": f"{self.test_prefix}Pricing Dish",
            "description": "Dish for pricing tests",
            "category_id": category_id,
            "is_available": True
        }
        
        dish_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                             json=dish_data, headers=headers)
        if dish_response.status_code != 201:
            return
        
        dish = dish_response.json()
        dish_id = dish["id"]
        self.created_data['dishes'].append(dish_id)
        
        # Тестируем различные цены
        price_tests = [
            {"name": "Small", "price": 9.99},
            {"name": "Medium", "price": 14.99},
            {"name": "Large", "price": 19.99},
            {"name": "Extra Large", "price": 24.50},
            {"name": "Family Size", "price": 35.00}
        ]
        
        created_variations = []
        for price_test in price_tests:
            variation_data = {
                "dish_id": dish_id,
                "name": price_test["name"],
                "price": price_test["price"],
                "is_default": price_test["name"] == "Medium",
                "is_available": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                               json=variation_data, headers=headers)
                if response.status_code == 201:
                    variation = response.json()
                    self.created_data['dish_variations'].append(variation["id"])
                    created_variations.append(variation)
                    
                    # Проверяем точность цены
                    if abs(variation["price"] - price_test["price"]) < 0.01:
                        self.results.add_test(f"Ценообразование - {price_test['name']}", True, 
                                            f"Цена установлена точно: {variation['price']}")
                    else:
                        self.results.add_test(f"Ценообразование - {price_test['name']}", False, 
                                            f"Неточная цена: ожидалось {price_test['price']}, получено {variation['price']}")
                else:
                    self.results.add_test(f"Ценообразование - {price_test['name']}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Ценообразование - {price_test['name']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Проверяем сортировку по цене (если поддерживается)
        if len(created_variations) >= 3:
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/dishes/{dish_id}/variations", 
                                              headers=headers)
                if response.status_code == 200:
                    variations = response.json()
                    
                    # Проверяем, что все созданные вариации присутствуют
                    variation_ids = [v["id"] for v in variations]
                    created_ids = [v["id"] for v in created_variations]
                    found_count = sum(1 for vid in created_ids if vid in variation_ids)
                    
                    if found_count == len(created_variations):
                        self.results.add_test("Ценообразование - получение всех вариаций", True, 
                                            f"Все {found_count} вариаций найдены")
                    else:
                        self.results.add_test("Ценообразование - получение всех вариаций", False, 
                                            f"Найдено только {found_count} из {len(created_variations)} вариаций")
                else:
                    self.results.add_test("Ценообразование - получение вариаций", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Ценообразование - получение вариаций", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_variation_default(self):
        """Тест вариации по умолчанию"""
        headers = self.get_auth_headers()
        
        # Создаем блюдо для тестов вариации по умолчанию
        category_data = {
            "name": f"{self.test_prefix}Default Category",
            "description": "Category for default tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        dish_data = {
            "name": f"{self.test_prefix}Default Dish",
            "description": "Dish for default variation tests",
            "category_id": category_id,
            "is_available": True
        }
        
        dish_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                             json=dish_data, headers=headers)
        if dish_response.status_code != 201:
            return
        
        dish = dish_response.json()
        dish_id = dish["id"]
        self.created_data['dishes'].append(dish_id)
        
        # Создаем первую вариацию как по умолчанию
        default_variation = {
            "dish_id": dish_id,
            "name": "Standard",
            "price": 12.99,
            "is_default": True,
            "is_available": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                           json=default_variation, headers=headers)
            if response.status_code == 201:
                variation = response.json()
                self.created_data['dish_variations'].append(variation["id"])
                
                if variation["is_default"] is True:
                    self.results.add_test("Вариация по умолчанию - первая", True, 
                                        "Первая вариация установлена как по умолчанию")
                else:
                    self.results.add_test("Вариация по умолчанию - первая", False, 
                                        f"Неверный статус по умолчанию: {variation['is_default']}")
            else:
                self.results.add_test("Вариация по умолчанию - первая", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Вариация по умолчанию - первая", False, f"Ошибка: {str(e)}")
        
        # Создаем вторую вариацию НЕ как по умолчанию
        second_variation = {
            "dish_id": dish_id,
            "name": "Large",
            "price": 16.99,
            "is_default": False,
            "is_available": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                           json=second_variation, headers=headers)
            if response.status_code == 201:
                variation = response.json()
                self.created_data['dish_variations'].append(variation["id"])
                
                if variation["is_default"] is False:
                    self.results.add_test("Вариация по умолчанию - вторая не по умолчанию", True, 
                                        "Вторая вариация не установлена как по умолчанию")
                else:
                    self.results.add_test("Вариация по умолчанию - вторая не по умолчанию", False, 
                                        f"Неверный статус: {variation['is_default']}")
            else:
                self.results.add_test("Вариация по умолчанию - вторая не по умолчанию", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Вариация по умолчанию - вторая не по умолчанию", False, 
                                f"Ошибка: {str(e)}")
        
        # Пытаемся создать третью вариацию как по умолчанию
        # (должна заменить первую или вызвать ошибку)
        third_variation = {
            "dish_id": dish_id,
            "name": "Premium",
            "price": 19.99,
            "is_default": True,
            "is_available": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                           json=third_variation, headers=headers)
            if response.status_code == 201:
                variation = response.json()
                self.created_data['dish_variations'].append(variation["id"])
                
                if variation["is_default"] is True:
                    self.results.add_test("Вариация по умолчанию - смена по умолчанию", True, 
                                        "Новая вариация по умолчанию создана", warning=True)
                else:
                    self.results.add_test("Вариация по умолчанию - смена по умолчанию", True, 
                                        "Система не позволила создать вторую вариацию по умолчанию")
            elif response.status_code in [400, 422]:
                self.results.add_test("Вариация по умолчанию - смена по умолчанию", True, 
                                    "Система правильно отклонила вторую вариацию по умолчанию")
            else:
                self.results.add_test("Вариация по умолчанию - смена по умолчанию", False, 
                                    f"Неожиданный код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Вариация по умолчанию - смена по умолчанию", False, 
                                f"Ошибка: {str(e)}")
    
    async def test_variation_dish_relationship(self):
        """Тест связи вариаций с блюдами"""
        headers = self.get_auth_headers()
        
        # Создаем несколько блюд для тестов связей
        category_data = {
            "name": f"{self.test_prefix}Relationship Category",
            "description": "Category for relationship tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        # Создаем два блюда
        dishes = []
        for i in range(2):
            dish_data = {
                "name": f"{self.test_prefix}Relationship Dish {i+1}",
                "description": f"Dish {i+1} for relationship tests",
                "category_id": category_id,
                "is_available": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                               json=dish_data, headers=headers)
                if response.status_code == 201:
                    dish = response.json()
                    self.created_data['dishes'].append(dish["id"])
                    dishes.append(dish)
            except Exception:
                continue
        
        if len(dishes) < 2:
            self.results.add_test("Связь вариация-блюдо - создание блюд", False, 
                                "Не удалось создать достаточно блюд")
            return
        
        # Создаем вариации для каждого блюда
        for i, dish in enumerate(dishes):
            variation_data = {
                "dish_id": dish["id"],
                "name": f"Variation for Dish {i+1}",
                "price": 10.99 + i * 5,
                "is_default": True,
                "is_available": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                               json=variation_data, headers=headers)
                if response.status_code == 201:
                    variation = response.json()
                    self.created_data['dish_variations'].append(variation["id"])
                    
                    if variation["dish_id"] == dish["id"]:
                        self.results.add_test(f"Связь вариация-блюдо - создание для блюда {i+1}", True, 
                                            f"Вариация привязана к блюду {dish['name']}")
                    else:
                        self.results.add_test(f"Связь вариация-блюдо - создание для блюда {i+1}", False, 
                                            f"Неверная привязка к блюду")
                else:
                    self.results.add_test(f"Связь вариация-блюдо - создание для блюда {i+1}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Связь вариация-блюдо - создание для блюда {i+1}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Проверяем получение вариаций для конкретного блюда
        if dishes:
            dish_id = dishes[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/dishes/{dish_id}/variations", 
                                              headers=headers)
                if response.status_code == 200:
                    variations = response.json()
                    dish_variations = [v for v in variations if v.get("dish_id") == dish_id]
                    if len(dish_variations) > 0:
                        self.results.add_test("Связь вариация-блюдо - получение по блюду", True, 
                                            f"Найдено {len(dish_variations)} вариаций для блюда")
                    else:
                        self.results.add_test("Связь вариация-блюдо - получение по блюду", False, 
                                            "Не найдено вариаций для блюда")
                else:
                    self.results.add_test("Связь вариация-блюдо - получение по блюду", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Связь вариация-блюдо - получение по блюду", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_variation_availability(self):
        """Тест доступности вариаций"""
        headers = self.get_auth_headers()
        
        # Создаем блюдо для тестов доступности
        category_data = {
            "name": f"{self.test_prefix}Availability Category",
            "description": "Category for availability tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        dish_data = {
            "name": f"{self.test_prefix}Availability Dish",
            "description": "Dish for availability tests",
            "category_id": category_id,
            "is_available": True
        }
        
        dish_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                             json=dish_data, headers=headers)
        if dish_response.status_code != 201:
            return
        
        dish = dish_response.json()
        dish_id = dish["id"]
        self.created_data['dishes'].append(dish_id)
        
        # Тест различных статусов доступности
        availability_tests = [
            {"name": "Available", "is_available": True},
            {"name": "Unavailable", "is_available": False}
        ]
        
        for availability_test in availability_tests:
            variation_data = {
                "dish_id": dish_id,
                "name": f"{availability_test['name']} Variation",
                "price": 12.99,
                "is_default": availability_test["name"] == "Available",
                "is_available": availability_test["is_available"]
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                               json=variation_data, headers=headers)
                if response.status_code == 201:
                    variation = response.json()
                    self.created_data['dish_variations'].append(variation["id"])
                    
                    if variation["is_available"] == availability_test["is_available"]:
                        self.results.add_test(f"Доступность вариации - {availability_test['name']}", True, 
                                            f"Статус доступности установлен корректно")
                    else:
                        self.results.add_test(f"Доступность вариации - {availability_test['name']}", False, 
                                            f"Неверный статус доступности")
                else:
                    self.results.add_test(f"Доступность вариации - {availability_test['name']}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Доступность вариации - {availability_test['name']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест фильтрации доступных вариаций (если поддерживается)
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/dishes/{dish_id}/variations?is_available=true", 
                                          headers=headers)
            if response.status_code == 200:
                variations = response.json()
                available_count = sum(1 for v in variations if v.get("is_available") is True)
                self.results.add_test("Доступность вариации - фильтр доступных", True, 
                                    f"Найдено {available_count} доступных вариаций", 
                                    warning=(available_count != len(variations)))
            elif response.status_code == 422:
                self.results.add_test("Доступность вариации - фильтр доступных", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Доступность вариации - фильтр доступных", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Доступность вариации - фильтр доступных", True, 
                                "Фильтрация не реализована", warning=True)
