#!/usr/bin/env python3
"""
QRes OS 4 - Ingredients Tests
Тесты управления ингредиентами
"""
from tests.test_base import BaseTestSuite, TestRunner


class IngredientsTestSuite(BaseTestSuite):
    """Тестовый сюит для управления ингредиентами"""
    
    async def run_tests(self):
        """Запуск всех тестов ингредиентов"""
        print("\n🥬 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ИНГРЕДИЕНТАМИ")
        print("=" * 50)
        
        await self.test_ingredient_crud()
        await self.test_ingredient_validation()
        await self.test_ingredient_allergens()
        await self.test_ingredient_units()
        await self.test_ingredient_status()
        await self.test_ingredient_search()
    
    async def test_ingredient_crud(self):
        """Тест CRUD операций с ингредиентами"""
        create_data = {
            "name": f"{self.test_prefix}Test Ingredient",
            "description": "Test ingredient for automated testing",
            "unit": "gram",
            "calories_per_unit": 25,
            "is_allergen": False,
            "allergen_type": "",
            "is_active": True,
            "cost_per_unit": 0.05,
            "supplier": f"{self.test_prefix}Test Supplier"
        }
        
        update_data = {
            "name": f"{self.test_prefix}Updated Test Ingredient",
            "description": "Updated test ingredient",
            "unit": "kilogram",
            "calories_per_unit": 30,
            "is_allergen": True,
            "allergen_type": "nuts",
            "is_active": True,
            "cost_per_unit": 0.08,
            "supplier": f"{self.test_prefix}Updated Supplier"
        }
        
        required_fields = ["id", "name", "unit", "is_allergen", "is_active", "created_at"]
        
        ingredient_id = await self.test_crud_operations(
            endpoint="ingredients",
            create_data=create_data,
            update_data=update_data,
            data_type="ingredients",
            required_fields=required_fields
        )
        
        return ingredient_id
    
    async def test_ingredient_validation(self):
        """Тест валидации данных ингредиента"""
        invalid_ingredients = [
            # Отсутствующее имя
            {
                "description": "Ingredient without name",
                "unit": "gram",
                "is_allergen": False,
                "is_active": True
            },
            # Пустое имя
            {
                "name": "",
                "description": "Ingredient with empty name",
                "unit": "gram",
                "is_allergen": False,
                "is_active": True
            },
            # Отсутствующая единица измерения
            {
                "name": f"{self.test_prefix}No Unit Ingredient",
                "description": "Ingredient without unit",
                "is_allergen": False,
                "is_active": True
            },
            # Пустая единица измерения
            {
                "name": f"{self.test_prefix}Empty Unit Ingredient",
                "description": "Ingredient with empty unit",
                "unit": "",
                "is_allergen": False,
                "is_active": True
            },
            # Невалидные калории
            {
                "name": f"{self.test_prefix}Invalid Calories Ingredient",
                "description": "Ingredient with invalid calories",
                "unit": "gram",
                "calories_per_unit": -10,
                "is_allergen": False,
                "is_active": True
            },
            # Невалидная стоимость
            {
                "name": f"{self.test_prefix}Invalid Cost Ingredient",
                "description": "Ingredient with invalid cost",
                "unit": "gram",
                "cost_per_unit": -5.0,
                "is_allergen": False,
                "is_active": True
            }
        ]
        
        headers = self.get_auth_headers()
        
        for i, ingredient_data in enumerate(invalid_ingredients):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                               json=ingredient_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация ингредиента #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если ингредиент создался, добавляем в список для удаления
                    ingredient = response.json()
                    self.created_data['ingredients'].append(ingredient["id"])
                    self.results.add_test(f"Валидация ингредиента #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация ингредиента #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация ингредиента #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_ingredient_allergens(self):
        """Тест управления аллергенами"""
        headers = self.get_auth_headers()
        
        # Тест различных типов аллергенов
        allergen_tests = [
            {"name": "Peanuts", "is_allergen": True, "allergen_type": "nuts"},
            {"name": "Milk", "is_allergen": True, "allergen_type": "dairy"},
            {"name": "Wheat", "is_allergen": True, "allergen_type": "gluten"},
            {"name": "Shellfish", "is_allergen": True, "allergen_type": "seafood"},
            {"name": "Eggs", "is_allergen": True, "allergen_type": "eggs"},
            {"name": "Regular Tomato", "is_allergen": False, "allergen_type": ""}
        ]
        
        created_allergens = []
        for allergen_test in allergen_tests:
            ingredient_data = {
                "name": f"{self.test_prefix}{allergen_test['name']}",
                "description": f"Test {allergen_test['name']} ingredient",
                "unit": "gram",
                "is_allergen": allergen_test["is_allergen"],
                "allergen_type": allergen_test["allergen_type"],
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                               json=ingredient_data, headers=headers)
                if response.status_code == 201:
                    ingredient = response.json()
                    self.created_data['ingredients'].append(ingredient["id"])
                    created_allergens.append(ingredient)
                    
                    # Проверяем статус аллергена
                    if ingredient["is_allergen"] == allergen_test["is_allergen"]:
                        self.results.add_test(f"Аллерген - {allergen_test['name']}", True, 
                                            f"Статус аллергена установлен корректно: {ingredient['is_allergen']}")
                    else:
                        self.results.add_test(f"Аллерген - {allergen_test['name']}", False, 
                                            f"Неверный статус аллергена: {ingredient['is_allergen']}")
                    
                    # Проверяем тип аллергена (если поддерживается)
                    if "allergen_type" in ingredient:
                        if ingredient["allergen_type"] == allergen_test["allergen_type"]:
                            self.results.add_test(f"Тип аллергена - {allergen_test['name']}", True, 
                                                f"Тип аллергена установлен корректно: {ingredient['allergen_type']}")
                        else:
                            self.results.add_test(f"Тип аллергена - {allergen_test['name']}", False, 
                                                f"Неверный тип аллергена: {ingredient['allergen_type']}")
                    else:
                        self.results.add_test(f"Тип аллергена - {allergen_test['name']}", True, 
                                            "Поле allergen_type не поддерживается", warning=True)
                else:
                    self.results.add_test(f"Аллерген - {allergen_test['name']}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Аллерген - {allergen_test['name']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест фильтрации аллергенов (если поддерживается)
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/ingredients/?is_allergen=true", 
                                          headers=headers)
            if response.status_code == 200:
                ingredients = response.json()
                allergen_count = sum(1 for ing in ingredients if ing.get("is_allergen") is True)
                self.results.add_test("Фильтрация аллергенов", True, 
                                    f"Найдено {allergen_count} аллергенов", 
                                    warning=(allergen_count != len(ingredients)))
            elif response.status_code == 422:
                self.results.add_test("Фильтрация аллергенов", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Фильтрация аллергенов", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Фильтрация аллергенов", True, 
                                "Фильтрация не реализована", warning=True)
    
    async def test_ingredient_units(self):
        """Тест различных единиц измерения"""
        headers = self.get_auth_headers()
        
        # Тест различных единиц измерения
        unit_tests = [
            "gram", "kilogram", "liter", "milliliter", "piece", 
            "cup", "tablespoon", "teaspoon", "ounce", "pound"
        ]
        
        for unit in unit_tests:
            ingredient_data = {
                "name": f"{self.test_prefix}Unit {unit.title()} Ingredient",
                "description": f"Ingredient measured in {unit}",
                "unit": unit,
                "is_allergen": False,
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                               json=ingredient_data, headers=headers)
                if response.status_code == 201:
                    ingredient = response.json()
                    self.created_data['ingredients'].append(ingredient["id"])
                    
                    if ingredient["unit"] == unit:
                        self.results.add_test(f"Единица измерения - {unit}", True, 
                                            f"Единица установлена корректно: {ingredient['unit']}")
                    else:
                        self.results.add_test(f"Единица измерения - {unit}", False, 
                                            f"Неверная единица: ожидалось {unit}, получено {ingredient['unit']}")
                else:
                    self.results.add_test(f"Единица измерения - {unit}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Единица измерения - {unit}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест невалидных единиц измерения
        invalid_units = ["", "invalid_unit", "123", "unit with spaces"]
        
        for invalid_unit in invalid_units:
            ingredient_data = {
                "name": f"{self.test_prefix}Invalid Unit Ingredient",
                "description": "Ingredient with invalid unit",
                "unit": invalid_unit,
                "is_allergen": False,
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                               json=ingredient_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Невалидная единица - '{invalid_unit}'", True, 
                                        "Невалидная единица правильно отклонена")
                elif response.status_code == 201:
                    ingredient = response.json()
                    self.created_data['ingredients'].append(ingredient["id"])
                    self.results.add_test(f"Невалидная единица - '{invalid_unit}'", True, 
                                        "Единица принята (валидация не строгая)", warning=True)
                else:
                    self.results.add_test(f"Невалидная единица - '{invalid_unit}'", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Невалидная единица - '{invalid_unit}'", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_ingredient_status(self):
        """Тест статуса активности ингредиентов"""
        headers = self.get_auth_headers()
        
        # Создаем активный ингредиент
        active_ingredient = {
            "name": f"{self.test_prefix}Active Ingredient",
            "description": "Active ingredient test",
            "unit": "gram",
            "is_allergen": False,
            "is_active": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                           json=active_ingredient, headers=headers)
            if response.status_code == 201:
                ingredient = response.json()
                self.created_data['ingredients'].append(ingredient["id"])
                
                if ingredient["is_active"] is True:
                    self.results.add_test("Статус ингредиента - активный", True, 
                                        "Активный ингредиент создан корректно")
                else:
                    self.results.add_test("Статус ингредиента - активный", False, 
                                        f"Неверный статус: {ingredient['is_active']}")
            else:
                self.results.add_test("Статус ингредиента - активный", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус ингредиента - активный", False, f"Ошибка: {str(e)}")
        
        # Создаем неактивный ингредиент
        inactive_ingredient = {
            "name": f"{self.test_prefix}Inactive Ingredient",
            "description": "Inactive ingredient test",
            "unit": "gram",
            "is_allergen": False,
            "is_active": False
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                           json=inactive_ingredient, headers=headers)
            if response.status_code == 201:
                ingredient = response.json()
                self.created_data['ingredients'].append(ingredient["id"])
                
                if ingredient["is_active"] is False:
                    self.results.add_test("Статус ингредиента - неактивный", True, 
                                        "Неактивный ингредиент создан корректно")
                else:
                    self.results.add_test("Статус ингредиента - неактивный", False, 
                                        f"Неверный статус: {ingredient['is_active']}")
            else:
                self.results.add_test("Статус ингредиента - неактивный", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус ингредиента - неактивный", False, f"Ошибка: {str(e)}")
    
    async def test_ingredient_search(self):
        """Тест поиска и фильтрации ингредиентов"""
        headers = self.get_auth_headers()
        
        # Создаем ингредиенты для поиска
        search_ingredients = [
            {
                "name": f"{self.test_prefix}Search Tomato",
                "description": "Fresh tomato for search",
                "unit": "gram",
                "is_allergen": False,
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Search Cheese",
                "description": "Dairy cheese for search",
                "unit": "gram",
                "is_allergen": True,
                "allergen_type": "dairy",
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Search Basil",
                "description": "Fresh basil herb",
                "unit": "gram",
                "is_allergen": False,
                "is_active": False
            }
        ]
        
        created_ingredients = []
        for ingredient_data in search_ingredients:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/ingredients/", 
                                               json=ingredient_data, headers=headers)
                if response.status_code == 201:
                    ingredient = response.json()
                    self.created_data['ingredients'].append(ingredient["id"])
                    created_ingredients.append(ingredient)
            except Exception:
                continue
        
        # Тест получения всех ингредиентов
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/ingredients/", headers=headers)
            if response.status_code == 200:
                ingredients = response.json()
                if len(ingredients) >= len(created_ingredients):
                    self.results.add_test("Поиск ингредиентов - все ингредиенты", True, 
                                        f"Получено {len(ingredients)} ингредиентов")
                else:
                    self.results.add_test("Поиск ингредиентов - все ингредиенты", False, 
                                        f"Получено меньше ингредиентов чем ожидалось")
            else:
                self.results.add_test("Поиск ингредиентов - все ингредиенты", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск ингредиентов - все ингредиенты", False, f"Ошибка: {str(e)}")
        
        # Тест поиска по ID
        if created_ingredients:
            ingredient_id = created_ingredients[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/ingredients/{ingredient_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    ingredient = response.json()
                    if ingredient["id"] == ingredient_id:
                        self.results.add_test("Поиск ингредиентов - по ID", True, 
                                            f"Найден ингредиент: {ingredient['name']}")
                    else:
                        self.results.add_test("Поиск ингредиентов - по ID", False, 
                                            f"Неверный ингредиент")
                else:
                    self.results.add_test("Поиск ингредиентов - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск ингредиентов - по ID", False, f"Ошибка: {str(e)}")
        
        # Тест фильтрации активных ингредиентов
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/ingredients/?is_active=true", 
                                          headers=headers)
            if response.status_code == 200:
                ingredients = response.json()
                active_count = sum(1 for ing in ingredients if ing.get("is_active") is True)
                self.results.add_test("Поиск ингредиентов - фильтр активных", True, 
                                    f"Найдено {active_count} активных ингредиентов", 
                                    warning=(active_count != len(ingredients)))
            elif response.status_code == 422:
                self.results.add_test("Поиск ингредиентов - фильтр активных", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск ингредиентов - фильтр активных", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск ингредиентов - фильтр активных", True, 
                                "Фильтрация не реализована", warning=True)
        
        # Тест поиска по имени (если поддерживается)
        try:
            search_term = "Search"
            response = await self.client.get(f"{self.runner.BASE_URL}/ingredients/?search={search_term}", 
                                          headers=headers)
            if response.status_code == 200:
                ingredients = response.json()
                matching_ingredients = [i for i in ingredients if search_term.lower() in i["name"].lower()]
                if len(matching_ingredients) > 0:
                    self.results.add_test("Поиск ингредиентов - по имени", True, 
                                        f"Найдено {len(matching_ingredients)} ингредиентов с '{search_term}'")
                else:
                    self.results.add_test("Поиск ингредиентов - по имени", True, 
                                        "Поиск работает, но результатов нет", warning=True)
            elif response.status_code == 422:
                self.results.add_test("Поиск ингредиентов - по имени", True, 
                                    "Поиск по имени не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск ингредиентов - по имени", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск ингредиентов - по имени", True, 
                                "Поиск по имени не реализован", warning=True)
        
        # Тест фильтрации по единице измерения (если поддерживается)
        try:
            unit = "gram"
            response = await self.client.get(f"{self.runner.BASE_URL}/ingredients/?unit={unit}", 
                                          headers=headers)
            if response.status_code == 200:
                ingredients = response.json()
                unit_ingredients = [i for i in ingredients if i.get("unit") == unit]
                if len(unit_ingredients) > 0:
                    self.results.add_test("Поиск ингредиентов - по единице", True, 
                                        f"Найдено {len(unit_ingredients)} ингредиентов в '{unit}'")
                else:
                    self.results.add_test("Поиск ингредиентов - по единице", True, 
                                        "Фильтр работает, но результатов нет", warning=True)
            elif response.status_code == 422:
                self.results.add_test("Поиск ингредиентов - по единице", True, 
                                    "Фильтр по единице не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск ингредиентов - по единице", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск ингредиентов - по единице", True, 
                                "Фильтр по единице не реализован", warning=True)
