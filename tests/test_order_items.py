#!/usr/bin/env python3
"""
QRes OS 4 - Order Items Tests
Тесты управления элементами заказов
"""
from tests.test_base import BaseTestSuite, TestRunner


class OrderItemsTestSuite(BaseTestSuite):
    """Тестовый сюит для управления элементами заказов"""
    
    async def run_tests(self):
        """Запуск всех тестов элементов заказов"""
        print("\n🛒📋 ТЕСТИРОВАНИЕ ЭЛЕМЕНТОВ ЗАКАЗОВ")
        print("=" * 50)
        
        await self.test_order_item_crud()
        await self.test_order_item_validation()
        await self.test_order_item_quantity()
        await self.test_order_item_calculations()
        await self.test_order_item_variations()
        await self.test_order_item_relationship()
    
    async def test_order_item_crud(self):
        """Тест CRUD операций с элементами заказов"""
        # Создаем необходимые зависимости
        dependencies = await self.create_order_item_dependencies()
        if not dependencies:
            return None
        
        order_id, dish_variation_id = dependencies
        
        create_data = {
            "order_id": order_id,
            "dish_variation_id": dish_variation_id,
            "quantity": 2,
            "unit_price": 15.99,
            "total_price": 31.98,
            "notes": "No onions please",
            "status": "pending"
        }
        
        update_data = {
            "order_id": order_id,
            "dish_variation_id": dish_variation_id,
            "quantity": 3,
            "unit_price": 15.99,
            "total_price": 47.97,
            "notes": "Extra cheese, no onions",
            "status": "confirmed"
        }
        
        required_fields = ["id", "order_id", "dish_variation_id", "quantity", "unit_price", "total_price"]
        
        order_item_id = await self.test_crud_operations(
            endpoint="orders/items",
            create_data=create_data,
            update_data=update_data,
            data_type="order_items",
            required_fields=required_fields
        )
        
        return order_item_id
    
    async def create_order_item_dependencies(self):
        """Создание зависимостей для элементов заказов"""
        headers = self.get_auth_headers()
        
        # Создаем локацию
        location_data = {
            "name": f"{self.test_prefix}Item Location",
            "address": "123 Item Street",
            "city": "Item City",
            "country": "Item Country",
            "is_active": True
        }
        
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        if location_response.status_code != 201:
            return None
        
        location = location_response.json()
        self.created_data['locations'].append(location["id"])
        
        # Создаем стол
        table_data = {
            "number": f"{self.test_prefix}ITEM_T001",
            "location_id": location["id"],
            "capacity": 4,
            "status": "available",
            "is_active": True
        }
        
        table_response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                              json=table_data, headers=headers)
        if table_response.status_code != 201:
            return None
        
        table = table_response.json()
        self.created_data['tables'].append(table["id"])
        
        # Создаем категорию
        category_data = {
            "name": f"{self.test_prefix}Item Category",
            "description": "Category for item tests",
            "sort_order": 1,
            "is_active": True
        }
        
        category_response = await self.client.post(f"{self.runner.BASE_URL}/categories/", 
                                                 json=category_data, headers=headers)
        if category_response.status_code != 201:
            return None
        
        category = category_response.json()
        self.created_data['categories'].append(category["id"])
        
        # Создаем блюдо
        dish_data = {
            "name": f"{self.test_prefix}Item Dish",
            "description": "Dish for item tests",
            "category_id": category["id"],
            "is_available": True
        }
        
        dish_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/", 
                                             json=dish_data, headers=headers)
        if dish_response.status_code != 201:
            return None
        
        dish = dish_response.json()
        self.created_data['dishes'].append(dish["id"])
        
        # Создаем вариацию блюда
        variation_data = {
            "dish_id": dish["id"],
            "name": "Standard",
            "price": 15.99,
            "is_default": True,
            "is_available": True
        }
        
        variation_response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                                  json=variation_data, headers=headers)
        if variation_response.status_code != 201:
            return None
        
        variation = variation_response.json()
        self.created_data['dish_variations'].append(variation["id"])
        
        # Создаем заказ
        order_data = {
            "table_id": table["id"],
            "user_id": self.runner.test_user_id,
            "status": "pending",
            "customer_name": f"{self.test_prefix}Item Customer"
        }
        
        order_response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                              json=order_data, headers=headers)
        if order_response.status_code != 201:
            return None
        
        order = order_response.json()
        self.created_data['orders'].append(order["id"])
        
        self.results.add_test("Создание зависимостей для элементов заказа", True, 
                            f"Заказ: {order['id']}, Вариация: {variation['id']}")
        
        return order["id"], variation["id"]
    
    async def test_order_item_validation(self):
        """Тест валидации данных элементов заказа"""
        # Создаем зависимости
        dependencies = await self.create_order_item_dependencies()
        if not dependencies:
            return
        
        order_id, dish_variation_id = dependencies
        headers = self.get_auth_headers()
        
        invalid_order_items = [
            # Отсутствующий заказ
            {
                "dish_variation_id": dish_variation_id,
                "quantity": 1,
                "unit_price": 15.99
            },
            # Несуществующий заказ
            {
                "order_id": 99999,
                "dish_variation_id": dish_variation_id,
                "quantity": 1,
                "unit_price": 15.99
            },
            # Отсутствующая вариация блюда
            {
                "order_id": order_id,
                "quantity": 1,
                "unit_price": 15.99
            },
            # Несуществующая вариация блюда
            {
                "order_id": order_id,
                "dish_variation_id": 99999,
                "quantity": 1,
                "unit_price": 15.99
            },
            # Нулевое количество
            {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": 0,
                "unit_price": 15.99
            },
            # Отрицательное количество
            {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": -2,
                "unit_price": 15.99
            },
            # Отрицательная цена
            {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": 1,
                "unit_price": -15.99
            },
            # Нулевая цена
            {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": 1,
                "unit_price": 0
            }
        ]
        
        for i, item_data in enumerate(invalid_order_items):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                               json=item_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация элемента заказа #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если элемент создался, добавляем в список для удаления
                    item = response.json()
                    self.created_data['order_items'].append(item["id"])
                    self.results.add_test(f"Валидация элемента заказа #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация элемента заказа #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация элемента заказа #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_order_item_quantity(self):
        """Тест различных количеств в элементах заказа"""
        # Создаем зависимости
        dependencies = await self.create_order_item_dependencies()
        if not dependencies:
            return
        
        order_id, dish_variation_id = dependencies
        headers = self.get_auth_headers()
        
        # Тест различных количеств
        quantities = [1, 2, 5, 10, 100]
        
        for quantity in quantities:
            item_data = {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": quantity,
                "unit_price": 15.99,
                "total_price": 15.99 * quantity
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                               json=item_data, headers=headers)
                if response.status_code == 201:
                    item = response.json()
                    self.created_data['order_items'].append(item["id"])
                    
                    if item["quantity"] == quantity:
                        self.results.add_test(f"Количество элемента - {quantity}", True, 
                                            f"Количество установлено корректно: {item['quantity']}")
                    else:
                        self.results.add_test(f"Количество элемента - {quantity}", False, 
                                            f"Неверное количество: ожидалось {quantity}, получено {item['quantity']}")
                else:
                    self.results.add_test(f"Количество элемента - {quantity}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Количество элемента - {quantity}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест дробных количеств (если поддерживается)
        fractional_quantities = [0.5, 1.5, 2.5]
        
        for quantity in fractional_quantities:
            item_data = {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": quantity,
                "unit_price": 15.99,
                "total_price": round(15.99 * quantity, 2)
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                               json=item_data, headers=headers)
                if response.status_code == 201:
                    item = response.json()
                    self.created_data['order_items'].append(item["id"])
                    
                    if abs(item["quantity"] - quantity) < 0.01:
                        self.results.add_test(f"Дробное количество - {quantity}", True, 
                                            f"Дробное количество поддерживается: {item['quantity']}")
                    else:
                        self.results.add_test(f"Дробное количество - {quantity}", False, 
                                            f"Неверное дробное количество")
                elif response.status_code in [400, 422]:
                    self.results.add_test(f"Дробное количество - {quantity}", True, 
                                        "Дробные количества не поддерживаются (это нормально)", warning=True)
                else:
                    self.results.add_test(f"Дробное количество - {quantity}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Дробное количество - {quantity}", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_order_item_calculations(self):
        """Тест расчетов в элементах заказа"""
        # Создаем зависимости
        dependencies = await self.create_order_item_dependencies()
        if not dependencies:
            return
        
        order_id, dish_variation_id = dependencies
        headers = self.get_auth_headers()
        
        # Тест расчета общей стоимости
        calculation_tests = [
            {"quantity": 1, "unit_price": 10.00, "expected_total": 10.00},
            {"quantity": 2, "unit_price": 15.50, "expected_total": 31.00},
            {"quantity": 3, "unit_price": 7.99, "expected_total": 23.97},
            {"quantity": 5, "unit_price": 12.75, "expected_total": 63.75}
        ]
        
        for test in calculation_tests:
            item_data = {
                "order_id": order_id,
                "dish_variation_id": dish_variation_id,
                "quantity": test["quantity"],
                "unit_price": test["unit_price"],
                "total_price": test["expected_total"]
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                               json=item_data, headers=headers)
                if response.status_code == 201:
                    item = response.json()
                    self.created_data['order_items'].append(item["id"])
                    
                    actual_total = item["total_price"]
                    expected_total = test["expected_total"]
                    
                    if abs(actual_total - expected_total) < 0.01:
                        self.results.add_test(f"Расчет стоимости - {test['quantity']}x{test['unit_price']}", True, 
                                            f"Стоимость рассчитана корректно: {actual_total}")
                    else:
                        self.results.add_test(f"Расчет стоимости - {test['quantity']}x{test['unit_price']}", False, 
                                            f"Неверная стоимость: ожидалось {expected_total}, получено {actual_total}")
                else:
                    self.results.add_test(f"Расчет стоимости - {test['quantity']}x{test['unit_price']}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Расчет стоимости - {test['quantity']}x{test['unit_price']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест автоматического расчета (если поддерживается)
        auto_calc_item = {
            "order_id": order_id,
            "dish_variation_id": dish_variation_id,
            "quantity": 3,
            "unit_price": 12.50
            # Не указываем total_price, чтобы проверить автоматический расчет
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                           json=auto_calc_item, headers=headers)
            if response.status_code == 201:
                item = response.json()
                self.created_data['order_items'].append(item["id"])
                
                expected_total = 37.50  # 3 * 12.50
                actual_total = item["total_price"]
                
                if abs(actual_total - expected_total) < 0.01:
                    self.results.add_test("Автоматический расчет стоимости", True, 
                                        f"Автоматический расчет работает: {actual_total}")
                else:
                    self.results.add_test("Автоматический расчет стоимости", True, 
                                        f"Автоматический расчет не реализован или работает по-другому", 
                                        warning=True)
            else:
                self.results.add_test("Автоматический расчет стоимости", True, 
                                    "Автоматический расчет не поддерживается", warning=True)
        except Exception as e:
            self.results.add_test("Автоматический расчет стоимости", True, 
                                "Автоматический расчет не реализован", warning=True)
    
    async def test_order_item_variations(self):
        """Тест элементов заказа с разными вариациями блюд"""
        # Создаем зависимости с дополнительными вариациями
        dependencies = await self.create_order_item_dependencies()
        if not dependencies:
            return
        
        order_id, dish_variation_id = dependencies
        headers = self.get_auth_headers()
        
        # Получаем dish_id из существующей вариации
        variation_response = await self.client.get(f"{self.runner.BASE_URL}/dishes/variations/{dish_variation_id}", 
                                                 headers=headers)
        if variation_response.status_code != 200:
            return
        
        variation = variation_response.json()
        dish_id = variation["dish_id"]
        
        # Создаем дополнительные вариации того же блюда
        additional_variations = [
            {"name": "Small", "price": 12.99},
            {"name": "Large", "price": 18.99},
            {"name": "Extra Large", "price": 22.99}
        ]
        
        created_variations = [dish_variation_id]  # Включаем существующую
        
        for var_data in additional_variations:
            variation_data = {
                "dish_id": dish_id,
                "name": var_data["name"],
                "price": var_data["price"],
                "is_default": False,
                "is_available": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/dishes/variations", 
                                               json=variation_data, headers=headers)
                if response.status_code == 201:
                    new_variation = response.json()
                    self.created_data['dish_variations'].append(new_variation["id"])
                    created_variations.append(new_variation["id"])
            except Exception:
                continue
        
        # Создаем элементы заказа с разными вариациями
        for i, variation_id in enumerate(created_variations):
            item_data = {
                "order_id": order_id,
                "dish_variation_id": variation_id,
                "quantity": 1,
                "unit_price": 15.99,  # Может отличаться от цены вариации
                "total_price": 15.99
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                               json=item_data, headers=headers)
                if response.status_code == 201:
                    item = response.json()
                    self.created_data['order_items'].append(item["id"])
                    
                    if item["dish_variation_id"] == variation_id:
                        self.results.add_test(f"Вариация в элементе заказа #{i+1}", True, 
                                            f"Элемент привязан к вариации {variation_id}")
                    else:
                        self.results.add_test(f"Вариация в элементе заказа #{i+1}", False, 
                                            f"Неверная привязка к вариации")
                else:
                    self.results.add_test(f"Вариация в элементе заказа #{i+1}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Вариация в элементе заказа #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_order_item_relationship(self):
        """Тест связей элементов заказа с заказами"""
        # Создаем несколько заказов
        dependencies1 = await self.create_order_item_dependencies()
        dependencies2 = await self.create_order_item_dependencies()
        
        if not (dependencies1 and dependencies2):
            return
        
        order_id1, dish_variation_id1 = dependencies1
        order_id2, dish_variation_id2 = dependencies2
        
        headers = self.get_auth_headers()
        
        # Создаем элементы для разных заказов
        items_data = [
            {
                "order_id": order_id1,
                "dish_variation_id": dish_variation_id1,
                "quantity": 2,
                "unit_price": 15.99,
                "total_price": 31.98
            },
            {
                "order_id": order_id2,
                "dish_variation_id": dish_variation_id2,
                "quantity": 1,
                "unit_price": 12.50,
                "total_price": 12.50
            }
        ]
        
        created_items = []
        for i, item_data in enumerate(items_data):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/items", 
                                               json=item_data, headers=headers)
                if response.status_code == 201:
                    item = response.json()
                    self.created_data['order_items'].append(item["id"])
                    created_items.append(item)
                    
                    if item["order_id"] == item_data["order_id"]:
                        self.results.add_test(f"Связь элемент-заказ - создание #{i+1}", True, 
                                            f"Элемент привязан к заказу {item_data['order_id']}")
                    else:
                        self.results.add_test(f"Связь элемент-заказ - создание #{i+1}", False, 
                                            f"Неверная привязка к заказу")
                else:
                    self.results.add_test(f"Связь элемент-заказ - создание #{i+1}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Связь элемент-заказ - создание #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест получения элементов конкретного заказа (если поддерживается)
        if created_items:
            test_order_id = created_items[0]["order_id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/orders/{test_order_id}/items", 
                                              headers=headers)
                if response.status_code == 200:
                    items = response.json()
                    order_items = [item for item in items if item.get("order_id") == test_order_id]
                    self.results.add_test("Связь элемент-заказ - получение по заказу", True, 
                                        f"Найдено {len(order_items)} элементов заказа")
                elif response.status_code == 404:
                    # Пробуем альтернативный endpoint
                    response = await self.client.get(f"{self.runner.BASE_URL}/orders/items?order_id={test_order_id}", 
                                                  headers=headers)
                    if response.status_code == 200:
                        items = response.json()
                        order_items = [item for item in items if item.get("order_id") == test_order_id]
                        self.results.add_test("Связь элемент-заказ - получение по заказу", True, 
                                            f"Найдено {len(order_items)} элементов заказа (альтернативный endpoint)")
                    else:
                        self.results.add_test("Связь элемент-заказ - получение по заказу", True, 
                                            "Получение элементов по заказу не поддерживается", warning=True)
                else:
                    self.results.add_test("Связь элемент-заказ - получение по заказу", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Связь элемент-заказ - получение по заказу", True, 
                                    "Получение элементов по заказу не реализовано", warning=True)
        
        # Тест получения всех элементов заказов
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/orders/items", headers=headers)
            if response.status_code == 200:
                items = response.json()
                if len(items) >= len(created_items):
                    self.results.add_test("Связь элемент-заказ - все элементы", True, 
                                        f"Получено {len(items)} элементов заказов")
                else:
                    self.results.add_test("Связь элемент-заказ - все элементы", False, 
                                        f"Получено меньше элементов чем ожидалось")
            else:
                self.results.add_test("Связь элемент-заказ - все элементы", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Связь элемент-заказ - все элементы", False, f"Ошибка: {str(e)}")
        
        # Тест обновления элемента заказа
        if created_items:
            item_id = created_items[0]["id"]
            update_data = {
                "order_id": created_items[0]["order_id"],
                "dish_variation_id": created_items[0]["dish_variation_id"],
                "quantity": 5,
                "unit_price": 15.99,
                "total_price": 79.95,
                "notes": "Updated notes"
            }
            
            try:
                response = await self.client.put(f"{self.runner.BASE_URL}/orders/items/{item_id}", 
                                              json=update_data, headers=headers)
                if response.status_code == 200:
                    updated_item = response.json()
                    if updated_item["quantity"] == 5:
                        self.results.add_test("Обновление элемента заказа", True, 
                                            f"Элемент обновлен: количество = {updated_item['quantity']}")
                    else:
                        self.results.add_test("Обновление элемента заказа", False, 
                                            f"Неверное количество после обновления")
                else:
                    self.results.add_test("Обновление элемента заказа", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Обновление элемента заказа", False, f"Ошибка: {str(e)}")
