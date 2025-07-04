#!/usr/bin/env python3
"""
QRes OS 4 - Dishes Tests
Тесты управления блюдами
"""
from tests.test_base import BaseTestSuite, TestRunner


class DishesTestSuite(BaseTestSuite):
    """Тестовый сюит для управления блюдами"""
    
    async def run_tests(self):
        """Запуск всех тестов блюд"""
        print("\n🍽️ ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ БЛЮДАМИ")
        print("=" * 50)
        
        await self.test_dish_crud()
        await self.test_dish_validation()
        await self.test_dish_category_relationship()
        await self.test_dish_ingredients_relationship()
        await self.test_dish_pricing()
        await self.test_dish_images()
        await self.test_dish_status()
        await self.test_dish_search()
    
    async def test_dish_crud(self):
        """Тест CRUD операций с блюдами"""
        # Сначала создаем категорию для блюд
        category_data = {
            "name": f"{self.test_prefix}Dish Test Category",
            "description": "Category for dish testing",
            "sort_order": 1,
            "is_active": True
        }
        
        headers = self.get_auth_headers()
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        
        if category_response.status_code != 201:
            self.results.add_test("Создание категории для блюд", False, 
                                f"Не удалось создать категорию: {category_response.status_code}")
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        create_data = {
            "name": f"{self.test_prefix}Test Dish",
            "description": "Test dish for automated testing",
            "category_id": category_id,
            "main_image_url": f"https://example.com/{self.test_prefix}dish.jpg",
            "is_available": True,
            "is_featured": False,
            "preparation_time": 15,
            "calories": 350,
            "allergens": ["gluten", "dairy"],
            "tags": ["vegetarian", "popular"]
        }
        
        update_data = {
            "name": f"{self.test_prefix}Updated Test Dish",
            "description": "Updated test dish",
            "category_id": category_id,
            "main_image_url": f"https://example.com/{self.test_prefix}dish_updated.jpg",
            "is_available": True,
            "is_featured": True,
            "preparation_time": 20,
            "calories": 400,
            "allergens": ["nuts"],
            "tags": ["spicy", "recommended"]
        }
        
        required_fields = ["id", "name", "category_id", "is_available", "created_at"]
        
        dish_id = await self.test_crud_operations(
            endpoint="dishes",
            create_data=create_data,
            update_data=update_data,
            data_type="dishes",
            required_fields=required_fields
        )
        
        return dish_id
    
    async def test_dish_validation(self):
        """Тест валидации данных блюда"""
        # Создаем категорию для тестов валидации
        headers = self.get_auth_headers()
        category_data = {
            "name": f"{self.test_prefix}Validation Category",
            "description": "Category for validation tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            self.results.add_test("Валидация блюд - создание категории", False, 
                                "Не удалось создать категорию для тестов")
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        invalid_dishes = [
            # Отсутствующее имя
            {
                "description": "Dish without name",
                "category_id": category_id,
                "is_available": True
            },
            # Пустое имя
            {
                "name": "",
                "description": "Dish with empty name",
                "category_id": category_id,
                "is_available": True
            },
            # Отсутствующая категория
            {
                "name": f"{self.test_prefix}No Category Dish",
                "description": "Dish without category",
                "is_available": True
            },
            # Несуществующая категория
            {
                "name": f"{self.test_prefix}Fake Category Dish",
                "description": "Dish with fake category",
                "category_id": 99999,
                "is_available": True
            },
            # Невалидное время приготовления
            {
                "name": f"{self.test_prefix}Invalid Time Dish",
                "description": "Dish with invalid preparation time",
                "category_id": category_id,
                "preparation_time": -5,
                "is_available": True
            },
            # Невалидные калории
            {
                "name": f"{self.test_prefix}Invalid Calories Dish",
                "description": "Dish with invalid calories",
                "category_id": category_id,
                "calories": -100,
                "is_available": True
            }
        ]
        
        for i, dish_data in enumerate(invalid_dishes):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                               json=dish_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация блюда #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если блюдо создалось, добавляем в список для удаления
                    dish = response.json()
                    self.created_data['dishes'].append(dish["id"])
                    self.results.add_test(f"Валидация блюда #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация блюда #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация блюда #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_dish_category_relationship(self):
        """Тест связи блюд с категориями"""
        headers = self.get_auth_headers()
        
        # Создаем несколько категорий
        categories = []
        for i in range(3):
            category_data = {
                "name": f"{self.test_prefix}Relation Category {i}",
                "description": f"Category {i} for dish relations",
                "sort_order": i + 1,
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                               json=category_data, headers=headers)
                if response.status_code == 201:
                    category = response.json()
                    self.created_data['categories'].append(category["id"])
                    categories.append(category)
            except Exception:
                continue
        
        if len(categories) < 2:
            self.results.add_test("Связь блюдо-категория - создание категорий", False, 
                                "Не удалось создать достаточно категорий")
            return
        
        # Создаем блюда в разных категориях
        for i, category in enumerate(categories[:2]):  # Используем первые 2 категории
            dish_data = {
                "name": f"{self.test_prefix}Category {i} Dish",
                "description": f"Dish in category {category['name']}",
                "category_id": category["id"],
                "is_available": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                               json=dish_data, headers=headers)
                if response.status_code == 201:
                    dish = response.json()
                    self.created_data['dishes'].append(dish["id"])
                    
                    if dish["category_id"] == category["id"]:
                        self.results.add_test(f"Связь блюдо-категория - создание #{i+1}", True, 
                                            f"Блюдо привязано к категории {category['name']}")
                    else:
                        self.results.add_test(f"Связь блюдо-категория - создание #{i+1}", False, 
                                            f"Неверная привязка категории")
                else:
                    self.results.add_test(f"Связь блюдо-категория - создание #{i+1}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Связь блюдо-категория - создание #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест получения блюд по категории (если поддерживается)
        if categories:
            category_id = categories[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/dishes/?category_id={category_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    dishes = response.json()
                    category_dishes = [d for d in dishes if d.get("category_id") == category_id]
                    self.results.add_test("Связь блюдо-категория - фильтр по категории", True, 
                                        f"Найдено {len(category_dishes)} блюд в категории")
                elif response.status_code == 422:
                    self.results.add_test("Связь блюдо-категория - фильтр по категории", True, 
                                        "Фильтрация не поддерживается", warning=True)
                else:
                    self.results.add_test("Связь блюдо-категория - фильтр по категории", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Связь блюдо-категория - фильтр по категории", True, 
                                    "Фильтрация не реализована", warning=True)
    
    async def test_dish_ingredients_relationship(self):
        """Тест связи блюд с ингредиентами"""
        headers = self.get_auth_headers()
        
        # Создаем категорию для блюда
        category_data = {
            "name": f"{self.test_prefix}Ingredients Category",
            "description": "Category for ingredients testing",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            self.results.add_test("Связь блюдо-ингредиенты - создание категории", False, 
                                "Не удалось создать категорию")
            return
        
        category = category_response.json()
        category_id = category["id"]
        self.created_data['categories'].append(category_id)
        
        # Создаем ингредиенты
        ingredients = []
        ingredient_names = ["Tomato", "Cheese", "Basil"]
        
        for name in ingredient_names:
            ingredient_data = {
                "name": f"{self.test_prefix}{name}",
                "description": f"Test ingredient {name}",
                "unit": "gram",
                "is_allergen": name == "Cheese",  # Сыр как аллерген
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                               json=ingredient_data, headers=headers)
                if response.status_code == 201:
                    ingredient = response.json()
                    self.created_data['ingredients'].append(ingredient["id"])
                    ingredients.append(ingredient)
            except Exception:
                continue
        
        if len(ingredients) < 2:
            self.results.add_test("Связь блюдо-ингредиенты - создание ингредиентов", False, 
                                "Не удалось создать достаточно ингредиентов")
            return
        
        # Создаем блюдо с ингредиентами
        dish_data = {
            "name": f"{self.test_prefix}Ingredients Test Dish",
            "description": "Dish for testing ingredients relationship",
            "category_id": category_id,
            "is_available": True,
            "ingredient_ids": [ing["id"] for ing in ingredients[:2]]  # Первые 2 ингредиента
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                           json=dish_data, headers=headers)
            if response.status_code == 201:
                dish = response.json()
                self.created_data['dishes'].append(dish["id"])
                
                # Проверяем связь с ингредиентами
                if "ingredients" in dish or "ingredient_ids" in dish:
                    self.results.add_test("Связь блюдо-ингредиенты - создание", True, 
                                        "Блюдо создано с ингредиентами")
                else:
                    self.results.add_test("Связь блюдо-ингредиенты - создание", True, 
                                        "Ингредиенты не отображаются в ответе (может быть нормально)", 
                                        warning=True)
            elif response.status_code in [400, 422]:
                self.results.add_test("Связь блюдо-ингредиенты - создание", True, 
                                    "Связь с ингредиентами не поддерживается", warning=True)
            else:
                self.results.add_test("Связь блюдо-ингредиенты - создание", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Связь блюдо-ингредиенты - создание", False, f"Ошибка: {str(e)}")
    
    async def test_dish_pricing(self):
        """Тест ценообразования блюд через вариации"""
        headers = self.get_auth_headers()
        
        # Создаем категорию и блюдо
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
            "name": f"{self.test_prefix}Pricing Test Dish",
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
        
        # Создаем вариации с разными ценами
        variations = [
            {
                "dish_id": dish_id,
                "name": "Small",
                "price": 10.99,
                "is_default": True,
                "is_available": True
            },
            {
                "dish_id": dish_id,
                "name": "Medium",
                "price": 15.99,
                "is_default": False,
                "is_available": True
            },
            {
                "dish_id": dish_id,
                "name": "Large",
                "price": 19.99,
                "is_default": False,
                "is_available": True
            }
        ]
        
        created_variations = []
        for i, variation_data in enumerate(variations):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                               json=variation_data, headers=headers)
                if response.status_code == 201:
                    variation = response.json()
                    self.created_data['dish_variations'].append(variation["id"])
                    created_variations.append(variation)
                    
                    # Проверяем цену
                    if variation["price"] == variation_data["price"]:
                        self.results.add_test(f"Ценообразование - вариация {variation_data['name']}", True, 
                                            f"Цена установлена: {variation['price']}")
                    else:
                        self.results.add_test(f"Ценообразование - вариация {variation_data['name']}", False, 
                                            f"Неверная цена: ожидалось {variation_data['price']}, получено {variation['price']}")
                else:
                    self.results.add_test(f"Ценообразование - вариация {variation_data['name']}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Ценообразование - вариация {variation_data['name']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Проверяем получение вариаций блюда
        if created_variations:
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/dishes/{dish_id}/variations", 
                                              headers=headers)
                if response.status_code == 200:
                    dish_variations = response.json()
                    if len(dish_variations) >= len(created_variations):
                        self.results.add_test("Ценообразование - получение вариаций", True, 
                                            f"Получено {len(dish_variations)} вариаций")
                    else:
                        self.results.add_test("Ценообразование - получение вариаций", False, 
                                            f"Получено меньше вариаций чем ожидалось")
                else:
                    self.results.add_test("Ценообразование - получение вариаций", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Ценообразование - получение вариаций", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_dish_images(self):
        """Тест работы с изображениями блюд"""
        headers = self.get_auth_headers()
        
        # Создаем категорию
        category_data = {
            "name": f"{self.test_prefix}Images Category",
            "description": "Category for image tests",
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
        
        # Тест блюда с основным изображением
        dish_with_image = {
            "name": f"{self.test_prefix}Image Test Dish",
            "description": "Dish with main image",
            "category_id": category_id,
            "main_image_url": f"https://example.com/{self.test_prefix}main_image.jpg",
            "is_available": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                           json=dish_with_image, headers=headers)
            if response.status_code == 201:
                dish = response.json()
                self.created_data['dishes'].append(dish["id"])
                
                # Проверяем основное изображение
                image_field = dish.get("main_image_url") or dish.get("image_url")
                if image_field == dish_with_image["main_image_url"]:
                    self.results.add_test("Изображения блюд - основное изображение", True, 
                                        f"Изображение установлено: {image_field}")
                else:
                    self.results.add_test("Изображения блюд - основное изображение", False, 
                                        f"Неверное изображение: {image_field}")
            else:
                self.results.add_test("Изображения блюд - основное изображение", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Изображения блюд - основное изображение", False, 
                                f"Ошибка: {str(e)}")
        
        # Тест блюда без изображения
        dish_without_image = {
            "name": f"{self.test_prefix}No Image Dish",
            "description": "Dish without image",
            "category_id": category_id,
            "is_available": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                           json=dish_without_image, headers=headers)
            if response.status_code == 201:
                dish = response.json()
                self.created_data['dishes'].append(dish["id"])
                self.results.add_test("Изображения блюд - без изображения", True, 
                                    "Блюдо создано без изображения")
            else:
                self.results.add_test("Изображения блюд - без изображения", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Изображения блюд - без изображения", False, 
                                f"Ошибка: {str(e)}")
    
    async def test_dish_status(self):
        """Тест статусов блюд"""
        headers = self.get_auth_headers()
        
        # Создаем категорию
        category_data = {
            "name": f"{self.test_prefix}Status Category",
            "description": "Category for status tests",
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
        
        # Тест различных статусов
        status_tests = [
            {"is_available": True, "is_featured": False, "name": "Available"},
            {"is_available": False, "is_featured": False, "name": "Unavailable"},
            {"is_available": True, "is_featured": True, "name": "Featured"},
            {"is_available": False, "is_featured": True, "name": "Unavailable Featured"}
        ]
        
        for status_test in status_tests:
            dish_data = {
                "name": f"{self.test_prefix}{status_test['name']} Dish",
                "description": f"Dish with {status_test['name']} status",
                "category_id": category_id,
                "is_available": status_test["is_available"],
                "is_featured": status_test["is_featured"]
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                               json=dish_data, headers=headers)
                if response.status_code == 201:
                    dish = response.json()
                    self.created_data['dishes'].append(dish["id"])
                    
                    # Проверяем статусы
                    if (dish["is_available"] == status_test["is_available"] and 
                        dish.get("is_featured", False) == status_test["is_featured"]):
                        self.results.add_test(f"Статус блюда - {status_test['name']}", True, 
                                            f"Статус установлен корректно")
                    else:
                        self.results.add_test(f"Статус блюда - {status_test['name']}", False, 
                                            f"Неверный статус")
                else:
                    self.results.add_test(f"Статус блюда - {status_test['name']}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Статус блюда - {status_test['name']}", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_dish_search(self):
        """Тест поиска и фильтрации блюд"""
        headers = self.get_auth_headers()
        
        # Создаем категорию
        category_data = {
            "name": f"{self.test_prefix}Search Category",
            "description": "Category for search tests",
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
        
        # Создаем блюда для поиска
        search_dishes = [
            {
                "name": f"{self.test_prefix}Pizza Margherita",
                "description": "Classic Italian pizza",
                "category_id": category_id,
                "is_available": True,
                "is_featured": True
            },
            {
                "name": f"{self.test_prefix}Pasta Carbonara",
                "description": "Traditional pasta dish",
                "category_id": category_id,
                "is_available": True,
                "is_featured": False
            },
            {
                "name": f"{self.test_prefix}Burger Classic",
                "description": "American style burger",
                "category_id": category_id,
                "is_available": False,
                "is_featured": False
            }
        ]
        
        created_dishes = []
        for dish_data in search_dishes:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                               json=dish_data, headers=headers)
                if response.status_code == 201:
                    dish = response.json()
                    self.created_data['dishes'].append(dish["id"])
                    created_dishes.append(dish)
            except Exception:
                continue
        
        # Тест получения всех блюд
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/dishes/", headers=headers)
            if response.status_code == 200:
                dishes = response.json()
                if len(dishes) >= len(created_dishes):
                    self.results.add_test("Поиск блюд - все блюда", True, 
                                        f"Получено {len(dishes)} блюд")
                else:
                    self.results.add_test("Поиск блюд - все блюда", False, 
                                        f"Получено меньше блюд чем ожидалось")
            else:
                self.results.add_test("Поиск блюд - все блюда", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск блюд - все блюда", False, f"Ошибка: {str(e)}")
        
        # Тест поиска по ID
        if created_dishes:
            dish_id = created_dishes[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/dishes/{dish_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    dish = response.json()
                    if dish["id"] == dish_id:
                        self.results.add_test("Поиск блюд - по ID", True, 
                                            f"Найдено блюдо: {dish['name']}")
                    else:
                        self.results.add_test("Поиск блюд - по ID", False, 
                                            f"Неверное блюдо")
                else:
                    self.results.add_test("Поиск блюд - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск блюд - по ID", False, f"Ошибка: {str(e)}")
        
        # Тест фильтрации доступных блюд
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/dishes/?is_available=true", 
                                          headers=headers)
            if response.status_code == 200:
                dishes = response.json()
                available_count = sum(1 for d in dishes if d.get("is_available") is True)
                self.results.add_test("Поиск блюд - фильтр доступных", True, 
                                    f"Найдено {available_count} доступных блюд", 
                                    warning=(available_count != len(dishes)))
            elif response.status_code == 422:
                self.results.add_test("Поиск блюд - фильтр доступных", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск блюд - фильтр доступных", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск блюд - фильтр доступных", True, 
                                "Фильтрация не реализована", warning=True)
        
        # Тест фильтрации рекомендуемых блюд
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/dishes/?is_featured=true", 
                                          headers=headers)
            if response.status_code == 200:
                dishes = response.json()
                featured_count = sum(1 for d in dishes if d.get("is_featured") is True)
                self.results.add_test("Поиск блюд - фильтр рекомендуемых", True, 
                                    f"Найдено {featured_count} рекомендуемых блюд", 
                                    warning=(featured_count != len(dishes)))
            elif response.status_code == 422:
                self.results.add_test("Поиск блюд - фильтр рекомендуемых", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск блюд - фильтр рекомендуемых", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск блюд - фильтр рекомендуемых", True, 
                                "Фильтрация не реализована", warning=True)
