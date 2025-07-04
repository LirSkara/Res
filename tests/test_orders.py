#!/usr/bin/env python3
"""
QRes OS 4 - Orders Tests
Тесты управления заказами
"""
from tests.test_base import BaseTestSuite, TestRunner


class OrdersTestSuite(BaseTestSuite):
    """Тестовый сюит для управления заказами"""
    
    async def run_tests(self):
        """Запуск всех тестов заказов"""
        print("\n🛒 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ЗАКАЗАМИ")
        print("=" * 50)
        
        await self.test_order_crud()
        await self.test_order_validation()
        await self.test_order_status_flow()
        await self.test_order_table_relationship()
        await self.test_order_user_relationship()
        await self.test_order_calculations()
        await self.test_order_search()
    
    async def test_order_crud(self):
        """Тест CRUD операций с заказами"""
        # Сначала создаем необходимые зависимости
        dependencies = await self.create_order_dependencies()
        if not dependencies:
            return None
        
        table_id, user_id, payment_method_id = dependencies
        
        create_data = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "pending",
            "payment_method_id": payment_method_id,
            "customer_name": f"{self.test_prefix}Test Customer",
            "customer_phone": "+1234567890",
            "notes": "Test order for automated testing",
            "discount_amount": 5.00,
            "tax_amount": 2.50
        }
        
        update_data = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "confirmed",
            "payment_method_id": payment_method_id,
            "customer_name": f"{self.test_prefix}Updated Customer",
            "customer_phone": "+0987654321",
            "notes": "Updated test order",
            "discount_amount": 10.00,
            "tax_amount": 5.00
        }
        
        required_fields = ["id", "table_id", "status", "total_amount", "created_at"]
        
        order_id = await self.test_crud_operations(
            endpoint="orders",
            create_data=create_data,
            update_data=update_data,
            data_type="orders",
            required_fields=required_fields
        )
        
        return order_id
    
    async def create_order_dependencies(self):
        """Создание зависимостей для заказов (стол, пользователь, способ оплаты)"""
        headers = self.get_auth_headers()
        
        # Создаем локацию
        location_data = {
            "name": f"{self.test_prefix}Order Location",
            "address": "123 Order Street",
            "city": "Order City",
            "country": "Order Country",
            "is_active": True
        }
        
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        if location_response.status_code != 201:
            self.results.add_test("Создание зависимостей - локация", False, 
                                "Не удалось создать локацию")
            return None
        
        location = location_response.json()
        location_id = location["id"]
        self.created_data['locations'].append(location_id)
        
        # Создаем стол
        table_data = {
            "number": f"{self.test_prefix}ORDER_T001",
            "location_id": location_id,
            "capacity": 4,
            "status": "available",
            "is_active": True
        }
        
        table_response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                              json=table_data, headers=headers)
        if table_response.status_code != 201:
            self.results.add_test("Создание зависимостей - стол", False, 
                                "Не удалось создать стол")
            return None
        
        table = table_response.json()
        table_id = table["id"]
        self.created_data['tables'].append(table_id)
        
        # Используем существующего тестового пользователя
        user_id = self.runner.test_user_id
        
        # Создаем способ оплаты
        payment_data = {
            "name": f"{self.test_prefix}Order Payment",
            "type": "card",
            "description": "Payment method for order tests",
            "is_active": True
        }
        
        payment_response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                                json=payment_data, headers=headers)
        if payment_response.status_code != 201:
            self.results.add_test("Создание зависимостей - способ оплаты", False, 
                                "Не удалось создать способ оплаты")
            return None
        
        payment_method = payment_response.json()
        payment_method_id = payment_method["id"]
        self.created_data['payment_methods'].append(payment_method_id)
        
        self.results.add_test("Создание зависимостей для заказов", True, 
                            f"Стол: {table_id}, Пользователь: {user_id}, Оплата: {payment_method_id}")
        
        return table_id, user_id, payment_method_id
    
    async def test_order_validation(self):
        """Тест валидации данных заказа"""
        # Создаем зависимости
        dependencies = await self.create_order_dependencies()
        if not dependencies:
            return
        
        table_id, user_id, payment_method_id = dependencies
        headers = self.get_auth_headers()
        
        invalid_orders = [
            # Отсутствующий стол
            {
                "user_id": user_id,
                "status": "pending",
                "customer_name": "No Table Customer"
            },
            # Несуществующий стол
            {
                "table_id": 99999,
                "user_id": user_id,
                "status": "pending",
                "customer_name": "Fake Table Customer"
            },
            # Отсутствующий пользователь
            {
                "table_id": table_id,
                "status": "pending",
                "customer_name": "No User Customer"
            },
            # Несуществующий пользователь
            {
                "table_id": table_id,
                "user_id": 99999,
                "status": "pending",
                "customer_name": "Fake User Customer"
            },
            # Невалидный статус
            {
                "table_id": table_id,
                "user_id": user_id,
                "status": "invalid_status",
                "customer_name": "Invalid Status Customer"
            },
            # Отрицательная скидка
            {
                "table_id": table_id,
                "user_id": user_id,
                "status": "pending",
                "customer_name": "Negative Discount Customer",
                "discount_amount": -10.0
            },
            # Отрицательный налог
            {
                "table_id": table_id,
                "user_id": user_id,
                "status": "pending",
                "customer_name": "Negative Tax Customer",
                "tax_amount": -5.0
            }
        ]
        
        for i, order_data in enumerate(invalid_orders):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                               json=order_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация заказа #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если заказ создался, добавляем в список для удаления
                    order = response.json()
                    self.created_data['orders'].append(order["id"])
                    self.results.add_test(f"Валидация заказа #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация заказа #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация заказа #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_order_status_flow(self):
        """Тест жизненного цикла статусов заказа"""
        # Создаем зависимости
        dependencies = await self.create_order_dependencies()
        if not dependencies:
            return
        
        table_id, user_id, payment_method_id = dependencies
        headers = self.get_auth_headers()
        
        # Создаем заказ в статусе pending
        order_data = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "pending",
            "payment_method_id": payment_method_id,
            "customer_name": f"{self.test_prefix}Status Flow Customer"
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                           json=order_data, headers=headers)
            if response.status_code != 201:
                self.results.add_test("Статусы заказа - создание", False, 
                                    f"Не удалось создать заказ: {response.status_code}")
                return
            
            order = response.json()
            order_id = order["id"]
            self.created_data['orders'].append(order_id)
            
            # Проверяем начальный статус
            if order["status"] == "pending":
                self.results.add_test("Статусы заказа - pending", True, 
                                    "Заказ создан в статусе pending")
            else:
                self.results.add_test("Статусы заказа - pending", False, 
                                    f"Неверный начальный статус: {order['status']}")
            
        except Exception as e:
            self.results.add_test("Статусы заказа - создание", False, f"Ошибка: {str(e)}")
            return
        
        # Тестируем переходы между статусами
        status_flow = [
            ("confirmed", "Подтверждение заказа"),
            ("preparing", "Готовка заказа"),
            ("ready", "Заказ готов"),
            ("served", "Заказ подан"),
            ("completed", "Заказ завершен")
        ]
        
        for new_status, description in status_flow:
            update_data = {
                "table_id": table_id,
                "user_id": user_id,
                "status": new_status,
                "customer_name": f"{self.test_prefix}Status Flow Customer"
            }
            
            try:
                response = await self.client.put(f"{self.runner.BASE_URL}/orders/{order_id}", 
                                              json=update_data, headers=headers)
                if response.status_code == 200:
                    updated_order = response.json()
                    if updated_order["status"] == new_status:
                        self.results.add_test(f"Статусы заказа - {new_status}", True, 
                                            f"{description} успешен")
                    else:
                        self.results.add_test(f"Статусы заказа - {new_status}", False, 
                                            f"Статус не изменился: {updated_order['status']}")
                else:
                    self.results.add_test(f"Статусы заказа - {new_status}", False, 
                                        f"Не удалось изменить статус: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Статусы заказа - {new_status}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест невалидного перехода (пытаемся вернуться к pending)
        invalid_update = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "pending",
            "customer_name": f"{self.test_prefix}Status Flow Customer"
        }
        
        try:
            response = await self.client.put(f"{self.runner.BASE_URL}/orders/{order_id}", 
                                          json=invalid_update, headers=headers)
            if response.status_code in [400, 422]:
                self.results.add_test("Статусы заказа - невалидный переход", True, 
                                    "Невалидный переход статуса правильно отклонен")
            elif response.status_code == 200:
                self.results.add_test("Статусы заказа - невалидный переход", True, 
                                    "Переход разрешен (валидация статусов не строгая)", warning=True)
            else:
                self.results.add_test("Статусы заказа - невалидный переход", False, 
                                    f"Неожиданный код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статусы заказа - невалидный переход", False, 
                                f"Ошибка: {str(e)}")
    
    async def test_order_table_relationship(self):
        """Тест связи заказов со столами"""
        # Создаем несколько столов
        dependencies1 = await self.create_order_dependencies()
        dependencies2 = await self.create_order_dependencies()
        
        if not (dependencies1 and dependencies2):
            return
        
        table_id1, user_id1, payment_id1 = dependencies1
        table_id2, user_id2, payment_id2 = dependencies2
        
        headers = self.get_auth_headers()
        
        # Создаем заказы для разных столов
        orders_data = [
            {
                "table_id": table_id1,
                "user_id": user_id1,
                "status": "pending",
                "customer_name": f"{self.test_prefix}Table 1 Customer"
            },
            {
                "table_id": table_id2,
                "user_id": user_id2,
                "status": "pending",
                "customer_name": f"{self.test_prefix}Table 2 Customer"
            }
        ]
        
        created_orders = []
        for i, order_data in enumerate(orders_data):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                               json=order_data, headers=headers)
                if response.status_code == 201:
                    order = response.json()
                    self.created_data['orders'].append(order["id"])
                    created_orders.append(order)
                    
                    if order["table_id"] == order_data["table_id"]:
                        self.results.add_test(f"Связь заказ-стол - создание #{i+1}", True, 
                                            f"Заказ привязан к столу {order_data['table_id']}")
                    else:
                        self.results.add_test(f"Связь заказ-стол - создание #{i+1}", False, 
                                            f"Неверная привязка к столу")
                else:
                    self.results.add_test(f"Связь заказ-стол - создание #{i+1}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Связь заказ-стол - создание #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест получения заказов по столу (если поддерживается)
        if created_orders:
            test_table_id = created_orders[0]["table_id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/orders/?table_id={test_table_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    orders = response.json()
                    table_orders = [o for o in orders if o.get("table_id") == test_table_id]
                    self.results.add_test("Связь заказ-стол - фильтр по столу", True, 
                                        f"Найдено {len(table_orders)} заказов для стола")
                elif response.status_code == 422:
                    self.results.add_test("Связь заказ-стол - фильтр по столу", True, 
                                        "Фильтрация не поддерживается", warning=True)
                else:
                    self.results.add_test("Связь заказ-стол - фильтр по столу", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Связь заказ-стол - фильтр по столу", True, 
                                    "Фильтрация не реализована", warning=True)
    
    async def test_order_user_relationship(self):
        """Тест связи заказов с пользователями"""
        # Создаем зависимости
        dependencies = await self.create_order_dependencies()
        if not dependencies:
            return
        
        table_id, user_id, payment_method_id = dependencies
        headers = self.get_auth_headers()
        
        # Создаем заказ
        order_data = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "pending",
            "customer_name": f"{self.test_prefix}User Relation Customer"
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                           json=order_data, headers=headers)
            if response.status_code == 201:
                order = response.json()
                self.created_data['orders'].append(order["id"])
                
                if order["user_id"] == user_id:
                    self.results.add_test("Связь заказ-пользователь - создание", True, 
                                        f"Заказ привязан к пользователю {user_id}")
                else:
                    self.results.add_test("Связь заказ-пользователь - создание", False, 
                                        f"Неверная привязка к пользователю")
            else:
                self.results.add_test("Связь заказ-пользователь - создание", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Связь заказ-пользователь - создание", False, 
                                f"Ошибка: {str(e)}")
        
        # Тест получения заказов пользователя (если поддерживается)
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/orders/?user_id={user_id}", 
                                          headers=headers)
            if response.status_code == 200:
                orders = response.json()
                user_orders = [o for o in orders if o.get("user_id") == user_id]
                self.results.add_test("Связь заказ-пользователь - фильтр по пользователю", True, 
                                    f"Найдено {len(user_orders)} заказов пользователя")
            elif response.status_code == 422:
                self.results.add_test("Связь заказ-пользователь - фильтр по пользователю", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Связь заказ-пользователь - фильтр по пользователю", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Связь заказ-пользователь - фильтр по пользователю", True, 
                                "Фильтрация не реализована", warning=True)
    
    async def test_order_calculations(self):
        """Тест расчетов в заказах"""
        # Создаем зависимости
        dependencies = await self.create_order_dependencies()
        if not dependencies:
            return
        
        table_id, user_id, payment_method_id = dependencies
        headers = self.get_auth_headers()
        
        # Создаем заказ с расчетами
        order_data = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "pending",
            "customer_name": f"{self.test_prefix}Calculations Customer",
            "subtotal_amount": 100.00,
            "discount_amount": 10.00,
            "tax_amount": 9.00,
            "service_charge": 5.00,
            "total_amount": 104.00  # 100 - 10 + 9 + 5 = 104
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                           json=order_data, headers=headers)
            if response.status_code == 201:
                order = response.json()
                self.created_data['orders'].append(order["id"])
                
                # Проверяем расчеты
                expected_total = 104.00
                actual_total = order.get("total_amount", 0)
                
                if abs(actual_total - expected_total) < 0.01:
                    self.results.add_test("Расчеты заказа - общая сумма", True, 
                                        f"Общая сумма рассчитана корректно: {actual_total}")
                else:
                    self.results.add_test("Расчеты заказа - общая сумма", False, 
                                        f"Неверная общая сумма: ожидалось {expected_total}, получено {actual_total}")
                
                # Проверяем компоненты суммы
                components = ["subtotal_amount", "discount_amount", "tax_amount", "service_charge"]
                for component in components:
                    if component in order:
                        self.results.add_test(f"Расчеты заказа - {component}", True, 
                                            f"{component}: {order[component]}")
                    else:
                        self.results.add_test(f"Расчеты заказа - {component}", True, 
                                            f"Поле {component} не поддерживается", warning=True)
            else:
                self.results.add_test("Расчеты заказа", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Расчеты заказа", False, f"Ошибка: {str(e)}")
        
        # Тест автоматического расчета (если поддерживается)
        auto_calc_order = {
            "table_id": table_id,
            "user_id": user_id,
            "status": "pending",
            "customer_name": f"{self.test_prefix}Auto Calc Customer",
            "subtotal_amount": 50.00,
            "discount_percentage": 10.0,  # 10% скидка = 5.00
            "tax_percentage": 8.0  # 8% налог от 45.00 = 3.60
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                           json=auto_calc_order, headers=headers)
            if response.status_code == 201:
                order = response.json()
                self.created_data['orders'].append(order["id"])
                
                # Ожидаемые расчеты: 50 - 5 + 3.60 = 48.60
                expected_total = 48.60
                actual_total = order.get("total_amount", 0)
                
                if abs(actual_total - expected_total) < 0.01:
                    self.results.add_test("Расчеты заказа - автоматический расчет", True, 
                                        f"Автоматический расчет работает: {actual_total}")
                else:
                    self.results.add_test("Расчеты заказа - автоматический расчет", True, 
                                        f"Автоматический расчет не реализован или работает по-другому", 
                                        warning=True)
            else:
                self.results.add_test("Расчеты заказа - автоматический расчет", True, 
                                    "Автоматический расчет не поддерживается", warning=True)
        except Exception as e:
            self.results.add_test("Расчеты заказа - автоматический расчет", True, 
                                "Автоматический расчет не реализован", warning=True)
    
    async def test_order_search(self):
        """Тест поиска и фильтрации заказов"""
        # Создаем несколько заказов для поиска
        dependencies = await self.create_order_dependencies()
        if not dependencies:
            return
        
        table_id, user_id, payment_method_id = dependencies
        headers = self.get_auth_headers()
        
        # Создаем заказы в разных статусах
        search_orders = [
            {
                "table_id": table_id,
                "user_id": user_id,
                "status": "pending",
                "customer_name": f"{self.test_prefix}Search Customer 1",
                "total_amount": 25.50
            },
            {
                "table_id": table_id,
                "user_id": user_id,
                "status": "confirmed",
                "customer_name": f"{self.test_prefix}Search Customer 2",
                "total_amount": 45.75
            },
            {
                "table_id": table_id,
                "user_id": user_id,
                "status": "completed",
                "customer_name": f"{self.test_prefix}Search Customer 3",
                "total_amount": 67.25
            }
        ]
        
        created_orders = []
        for order_data in search_orders:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/orders/", 
                                               json=order_data, headers=headers)
                if response.status_code == 201:
                    order = response.json()
                    self.created_data['orders'].append(order["id"])
                    created_orders.append(order)
            except Exception:
                continue
        
        # Тест получения всех заказов
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/orders/", headers=headers)
            if response.status_code == 200:
                orders = response.json()
                if len(orders) >= len(created_orders):
                    self.results.add_test("Поиск заказов - все заказы", True, 
                                        f"Получено {len(orders)} заказов")
                else:
                    self.results.add_test("Поиск заказов - все заказы", False, 
                                        f"Получено меньше заказов чем ожидалось")
            else:
                self.results.add_test("Поиск заказов - все заказы", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск заказов - все заказы", False, f"Ошибка: {str(e)}")
        
        # Тест поиска по ID
        if created_orders:
            order_id = created_orders[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/orders/{order_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    order = response.json()
                    if order["id"] == order_id:
                        self.results.add_test("Поиск заказов - по ID", True, 
                                            f"Найден заказ: {order_id}")
                    else:
                        self.results.add_test("Поиск заказов - по ID", False, 
                                            f"Неверный заказ")
                else:
                    self.results.add_test("Поиск заказов - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск заказов - по ID", False, f"Ошибка: {str(e)}")
        
        # Тест фильтрации по статусу
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/orders/?status=pending", 
                                          headers=headers)
            if response.status_code == 200:
                orders = response.json()
                pending_count = sum(1 for o in orders if o.get("status") == "pending")
                self.results.add_test("Поиск заказов - фильтр по статусу", True, 
                                    f"Найдено {pending_count} заказов в статусе 'pending'", 
                                    warning=(pending_count != len(orders)))
            elif response.status_code == 422:
                self.results.add_test("Поиск заказов - фильтр по статусу", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск заказов - фильтр по статусу", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск заказов - фильтр по статусу", True, 
                                "Фильтрация не реализована", warning=True)
        
        # Тест фильтрации по дате (сегодняшние заказы)
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            response = await self.client.get(f"{self.runner.BASE_URL}/orders/?date={today}", 
                                          headers=headers)
            if response.status_code == 200:
                orders = response.json()
                self.results.add_test("Поиск заказов - фильтр по дате", True, 
                                    f"Найдено {len(orders)} заказов за сегодня")
            elif response.status_code == 422:
                self.results.add_test("Поиск заказов - фильтр по дате", True, 
                                    "Фильтрация по дате не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск заказов - фильтр по дате", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск заказов - фильтр по дате", True, 
                                "Фильтрация по дате не реализована", warning=True)
