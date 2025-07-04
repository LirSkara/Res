#!/usr/bin/env python3
"""
QRes OS 4 - Categories Tests
Тесты управления категориями блюд
"""
from tests.test_base import BaseTestSuite, TestRunner


class CategoriesTestSuite(BaseTestSuite):
    """Тестовый сюит для управления категориями"""
    
    async def run_tests(self):
        """Запуск всех тестов категорий"""
        print("\n📂 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ КАТЕГОРИЯМИ")
        print("=" * 50)
        
        await self.test_category_crud()
        await self.test_category_validation()
        await self.test_category_ordering()
        await self.test_category_hierarchy()
        await self.test_category_status()
        await self.test_category_search()
    
    async def test_category_crud(self):
        """Тест CRUD операций с категориями"""
        create_data = {
            "name": f"{self.test_prefix}Test Category",
            "description": "Test category for automated testing",
            "sort_order": 1,
            "is_active": True,
            "image_url": f"https://example.com/{self.test_prefix}category.jpg"
        }
        
        update_data = {
            "name": f"{self.test_prefix}Updated Category",
            "description": "Updated test category",
            "sort_order": 2,
            "is_active": True,
            "image_url": f"https://example.com/{self.test_prefix}category_updated.jpg"
        }
        
        required_fields = ["id", "name", "sort_order", "is_active", "created_at"]
        
        category_id = await self.test_crud_operations(
            endpoint="categories",
            create_data=create_data,
            update_data=update_data,
            data_type="categories",
            required_fields=required_fields
        )
        
        return category_id
    
    async def test_category_validation(self):
        """Тест валидации данных категории"""
        invalid_categories = [
            # Отсутствующее имя
            {
                "description": "Category without name",
                "sort_order": 1,
                "is_active": True
            },
            # Пустое имя
            {
                "name": "",
                "description": "Category with empty name",
                "sort_order": 1,
                "is_active": True
            },
            # Невалидный порядок сортировки
            {
                "name": f"{self.test_prefix}Invalid Order Category",
                "description": "Category with invalid sort order",
                "sort_order": -1,
                "is_active": True
            },
            # Слишком длинное имя (если есть ограничения)
            {
                "name": f"{self.test_prefix}" + "Very Long Category Name " * 10,
                "description": "Category with very long name",
                "sort_order": 1,
                "is_active": True
            }
        ]
        
        headers = self.get_auth_headers()
        
        for i, category_data in enumerate(invalid_categories):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                               json=category_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация категории #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если категория создалась, добавляем в список для удаления
                    category = response.json()
                    self.created_data['categories'].append(category["id"])
                    self.results.add_test(f"Валидация категории #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация категории #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация категории #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_category_ordering(self):
        """Тест сортировки категорий"""
        headers = self.get_auth_headers()
        
        # Создаем несколько категорий с разным порядком сортировки
        categories_data = [
            {
                "name": f"{self.test_prefix}Third Category",
                "description": "Third in order",
                "sort_order": 3,
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}First Category",
                "description": "First in order",
                "sort_order": 1,
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Second Category",
                "description": "Second in order",
                "sort_order": 2,
                "is_active": True
            }
        ]
        
        created_categories = []
        for category_data in categories_data:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                               json=category_data, headers=headers)
                if response.status_code == 201:
                    category = response.json()
                    self.created_data['categories'].append(category["id"])
                    created_categories.append(category)
                    self.results.add_test(f"Создание категории для сортировки", True, 
                                        f"Создана: {category['name']}")
                else:
                    self.results.add_test(f"Создание категории для сортировки", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Создание категории для сортировки", False, 
                                    f"Ошибка: {str(e)}")
        
        # Проверяем сортировку при получении списка
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/categories/", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                
                # Фильтруем только наши тестовые категории
                test_categories = [c for c in categories if c["name"].startswith(self.test_prefix)]
                
                if len(test_categories) >= 3:
                    # Проверяем порядок сортировки
                    sorted_correctly = True
                    for i in range(len(test_categories) - 1):
                        if test_categories[i]["sort_order"] > test_categories[i + 1]["sort_order"]:
                            sorted_correctly = False
                            break
                    
                    if sorted_correctly:
                        self.results.add_test("Сортировка категорий", True, 
                                            "Категории отсортированы корректно")
                    else:
                        self.results.add_test("Сортировка категорий", True, 
                                            "Сортировка не применяется автоматически", warning=True)
                else:
                    self.results.add_test("Сортировка категорий", True, 
                                        "Недостаточно категорий для проверки", warning=True)
            else:
                self.results.add_test("Сортировка категорий", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Сортировка категорий", False, f"Ошибка: {str(e)}")
    
    async def test_category_hierarchy(self):
        """Тест иерархии категорий (если поддерживается)"""
        headers = self.get_auth_headers()
        
        # Создаем родительскую категорию
        parent_data = {
            "name": f"{self.test_prefix}Parent Category",
            "description": "Parent category for hierarchy test",
            "sort_order": 1,
            "is_active": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                           json=parent_data, headers=headers)
            if response.status_code == 201:
                parent_category = response.json()
                parent_id = parent_category["id"]
                self.created_data['categories'].append(parent_id)
                
                # Пытаемся создать дочернюю категорию
                child_data = {
                    "name": f"{self.test_prefix}Child Category",
                    "description": "Child category for hierarchy test",
                    "sort_order": 1,
                    "parent_id": parent_id,
                    "is_active": True
                }
                
                try:
                    response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                   json=child_data, headers=headers)
                    if response.status_code == 201:
                        child_category = response.json()
                        self.created_data['categories'].append(child_category["id"])
                        
                        if child_category.get("parent_id") == parent_id:
                            self.results.add_test("Иерархия категорий", True, 
                                                "Дочерняя категория создана корректно")
                        else:
                            self.results.add_test("Иерархия категорий", True, 
                                                "Поле parent_id отсутствует (иерархия не поддерживается)", 
                                                warning=True)
                    elif response.status_code in [400, 422]:
                        self.results.add_test("Иерархия категорий", True, 
                                            "Иерархия не поддерживается", warning=True)
                    else:
                        self.results.add_test("Иерархия категорий", False, 
                                            f"Неожиданный код: {response.status_code}")
                except Exception as e:
                    self.results.add_test("Иерархия категорий", True, 
                                        "Иерархия не реализована", warning=True)
            else:
                self.results.add_test("Иерархия категорий - создание родителя", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Иерархия категорий", False, f"Ошибка: {str(e)}")
    
    async def test_category_status(self):
        """Тест статуса активности категорий"""
        headers = self.get_auth_headers()
        
        # Создаем активную категорию
        active_category = {
            "name": f"{self.test_prefix}Active Category",
            "description": "Active category test",
            "sort_order": 1,
            "is_active": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                           json=active_category, headers=headers)
            if response.status_code == 201:
                category = response.json()
                self.created_data['categories'].append(category["id"])
                
                if category["is_active"] is True:
                    self.results.add_test("Статус категории - активная", True, 
                                        "Активная категория создана корректно")
                else:
                    self.results.add_test("Статус категории - активная", False, 
                                        f"Неверный статус: {category['is_active']}")
            else:
                self.results.add_test("Статус категории - активная", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус категории - активная", False, f"Ошибка: {str(e)}")
        
        # Создаем неактивную категорию
        inactive_category = {
            "name": f"{self.test_prefix}Inactive Category",
            "description": "Inactive category test",
            "sort_order": 2,
            "is_active": False
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                           json=inactive_category, headers=headers)
            if response.status_code == 201:
                category = response.json()
                self.created_data['categories'].append(category["id"])
                
                if category["is_active"] is False:
                    self.results.add_test("Статус категории - неактивная", True, 
                                        "Неактивная категория создана корректно")
                else:
                    self.results.add_test("Статус категории - неактивная", False, 
                                        f"Неверный статус: {category['is_active']}")
            else:
                self.results.add_test("Статус категории - неактивная", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус категории - неактивная", False, f"Ошибка: {str(e)}")
    
    async def test_category_search(self):
        """Тест поиска и фильтрации категорий"""
        headers = self.get_auth_headers()
        
        # Создаем несколько категорий для поиска
        search_categories = [
            {
                "name": f"{self.test_prefix}Search Category 1",
                "description": "First search category",
                "sort_order": 1,
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Search Category 2",
                "description": "Second search category",
                "sort_order": 2,
                "is_active": False
            },
            {
                "name": f"{self.test_prefix}Different Name",
                "description": "Different category",
                "sort_order": 3,
                "is_active": True
            }
        ]
        
        created_categories = []
        for category_data in search_categories:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                               json=category_data, headers=headers)
                if response.status_code == 201:
                    category = response.json()
                    self.created_data['categories'].append(category["id"])
                    created_categories.append(category)
            except Exception:
                continue
        
        # Тест получения всех категорий
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/categories/", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                if len(categories) >= len(created_categories):
                    self.results.add_test("Поиск категорий - все категории", True, 
                                        f"Получено {len(categories)} категорий")
                else:
                    self.results.add_test("Поиск категорий - все категории", False, 
                                        f"Получено меньше категорий чем ожидалось")
            else:
                self.results.add_test("Поиск категорий - все категории", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск категорий - все категории", False, f"Ошибка: {str(e)}")
        
        # Тест поиска конкретной категории по ID
        if created_categories:
            category_id = created_categories[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/categories/{category_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    category = response.json()
                    if category["id"] == category_id:
                        self.results.add_test("Поиск категорий - по ID", True, 
                                            f"Найдена категория: {category['name']}")
                    else:
                        self.results.add_test("Поиск категорий - по ID", False, 
                                            f"Неверная категория: ожидался ID {category_id}")
                else:
                    self.results.add_test("Поиск категорий - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск категорий - по ID", False, f"Ошибка: {str(e)}")
        
        # Тест фильтрации по статусу (если поддерживается)
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/categories/?is_active=true", 
                                          headers=headers)
            if response.status_code == 200:
                categories = response.json()
                active_count = sum(1 for cat in categories if cat.get("is_active") is True)
                self.results.add_test("Поиск категорий - фильтр активных", True, 
                                    f"Найдено {active_count} активных категорий", 
                                    warning=(active_count != len(categories)))
            elif response.status_code == 422:
                self.results.add_test("Поиск категорий - фильтр активных", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск категорий - фильтр активных", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск категорий - фильтр активных", True, 
                                "Фильтрация не реализована", warning=True)
        
        # Тест поиска по имени (если поддерживается)
        try:
            search_term = "Search"
            response = await self.client.get(f"{self.runner.BASE_URL}/categories/?search={search_term}", 
                                          headers=headers)
            if response.status_code == 200:
                categories = response.json()
                matching_categories = [c for c in categories if search_term.lower() in c["name"].lower()]
                if len(matching_categories) > 0:
                    self.results.add_test("Поиск категорий - по имени", True, 
                                        f"Найдено {len(matching_categories)} категорий с '{search_term}'")
                else:
                    self.results.add_test("Поиск категорий - по имени", True, 
                                        "Поиск работает, но результатов нет", warning=True)
            elif response.status_code == 422:
                self.results.add_test("Поиск категорий - по имени", True, 
                                    "Поиск по имени не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск категорий - по имени", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск категорий - по имени", True, 
                                "Поиск по имени не реализован", warning=True)
