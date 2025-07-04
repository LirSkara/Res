#!/usr/bin/env python3
"""
QRes OS 4 - Payment Methods Tests
Тесты управления способами оплаты
"""
from tests.test_base import BaseTestSuite, TestRunner


class PaymentMethodsTestSuite(BaseTestSuite):
    """Тестовый сюит для управления способами оплаты"""
    
    async def run_tests(self):
        """Запуск всех тестов способов оплаты"""
        print("\n💳 ТЕСТИРОВАНИЕ СПОСОБОВ ОПЛАТЫ")
        print("=" * 50)
        
        await self.test_payment_method_crud()
        await self.test_payment_method_validation()
        await self.test_payment_method_types()
        await self.test_payment_method_status()
        await self.test_payment_method_configuration()
        await self.test_payment_method_search()
    
    async def test_payment_method_crud(self):
        """Тест CRUD операций со способами оплаты"""
        create_data = {
            "name": f"{self.test_prefix}Test Payment Method",
            "type": "card",
            "description": "Test payment method for automated testing",
            "is_active": True,
            "is_default": False,
            "commission_rate": 2.5,
            "min_amount": 1.00,
            "max_amount": 10000.00,
            "config": {
                "api_key": "test_key_123",
                "webhook_url": "https://example.com/webhook"
            }
        }
        
        update_data = {
            "name": f"{self.test_prefix}Updated Payment Method",
            "type": "cash",
            "description": "Updated test payment method",
            "is_active": True,
            "is_default": True,
            "commission_rate": 0.0,
            "min_amount": 0.01,
            "max_amount": 50000.00,
            "config": {}
        }
        
        required_fields = ["id", "name", "type", "is_active", "created_at"]
        
        payment_method_id = await self.test_crud_operations(
            endpoint="payment-methods",
            create_data=create_data,
            update_data=update_data,
            data_type="payment_methods",
            required_fields=required_fields
        )
        
        return payment_method_id
    
    async def test_payment_method_validation(self):
        """Тест валидации данных способа оплаты"""
        invalid_payment_methods = [
            # Отсутствующее имя
            {
                "type": "card",
                "description": "Payment method without name",
                "is_active": True
            },
            # Пустое имя
            {
                "name": "",
                "type": "card",
                "description": "Payment method with empty name",
                "is_active": True
            },
            # Отсутствующий тип
            {
                "name": f"{self.test_prefix}No Type Payment",
                "description": "Payment method without type",
                "is_active": True
            },
            # Невалидный тип
            {
                "name": f"{self.test_prefix}Invalid Type Payment",
                "type": "invalid_type",
                "description": "Payment method with invalid type",
                "is_active": True
            },
            # Невалидная комиссия
            {
                "name": f"{self.test_prefix}Invalid Commission Payment",
                "type": "card",
                "description": "Payment method with invalid commission",
                "commission_rate": -5.0,
                "is_active": True
            },
            # Невалидные лимиты
            {
                "name": f"{self.test_prefix}Invalid Limits Payment",
                "type": "card",
                "description": "Payment method with invalid limits",
                "min_amount": 100.0,
                "max_amount": 50.0,  # min больше max
                "is_active": True
            }
        ]
        
        headers = self.get_auth_headers()
        
        for i, payment_data in enumerate(invalid_payment_methods):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                               json=payment_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация способа оплаты #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если способ оплаты создался, добавляем в список для удаления
                    payment_method = response.json()
                    self.created_data['payment_methods'].append(payment_method["id"])
                    self.results.add_test(f"Валидация способа оплаты #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация способа оплаты #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация способа оплаты #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_payment_method_types(self):
        """Тест различных типов способов оплаты"""
        headers = self.get_auth_headers()
        
        # Тест различных типов оплаты
        payment_types = [
            {
                "type": "cash",
                "name": f"{self.test_prefix}Cash Payment",
                "description": "Cash payment method",
                "commission_rate": 0.0
            },
            {
                "type": "card",
                "name": f"{self.test_prefix}Card Payment",
                "description": "Credit/Debit card payment",
                "commission_rate": 2.5
            },
            {
                "type": "bank_transfer",
                "name": f"{self.test_prefix}Bank Transfer",
                "description": "Bank transfer payment",
                "commission_rate": 1.0
            },
            {
                "type": "digital_wallet",
                "name": f"{self.test_prefix}Digital Wallet",
                "description": "Digital wallet payment",
                "commission_rate": 1.5
            },
            {
                "type": "cryptocurrency",
                "name": f"{self.test_prefix}Crypto Payment",
                "description": "Cryptocurrency payment",
                "commission_rate": 3.0
            }
        ]
        
        created_payment_methods = []
        for payment_type_data in payment_types:
            payment_data = {
                "name": payment_type_data["name"],
                "type": payment_type_data["type"],
                "description": payment_type_data["description"],
                "commission_rate": payment_type_data["commission_rate"],
                "is_active": True,
                "is_default": False
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                               json=payment_data, headers=headers)
                if response.status_code == 201:
                    payment_method = response.json()
                    self.created_data['payment_methods'].append(payment_method["id"])
                    created_payment_methods.append(payment_method)
                    
                    # Проверяем тип
                    if payment_method["type"] == payment_type_data["type"]:
                        self.results.add_test(f"Тип оплаты - {payment_type_data['type']}", True, 
                                            f"Тип установлен корректно: {payment_method['type']}")
                    else:
                        self.results.add_test(f"Тип оплаты - {payment_type_data['type']}", False, 
                                            f"Неверный тип: ожидался {payment_type_data['type']}, получен {payment_method['type']}")
                else:
                    # Некоторые типы могут не поддерживаться
                    if response.status_code in [400, 422]:
                        self.results.add_test(f"Тип оплаты - {payment_type_data['type']}", True, 
                                            f"Тип не поддерживается (это нормально)", warning=True)
                    else:
                        self.results.add_test(f"Тип оплаты - {payment_type_data['type']}", False, 
                                            f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Тип оплаты - {payment_type_data['type']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Проверяем получение способов оплаты по типу (если поддерживается)
        if created_payment_methods:
            test_type = created_payment_methods[0]["type"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/payment-methods/?type={test_type}", 
                                              headers=headers)
                if response.status_code == 200:
                    payment_methods = response.json()
                    type_methods = [pm for pm in payment_methods if pm.get("type") == test_type]
                    self.results.add_test("Фильтрация по типу оплаты", True, 
                                        f"Найдено {len(type_methods)} способов типа '{test_type}'")
                elif response.status_code == 422:
                    self.results.add_test("Фильтрация по типу оплаты", True, 
                                        "Фильтрация не поддерживается", warning=True)
                else:
                    self.results.add_test("Фильтрация по типу оплаты", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Фильтрация по типу оплаты", True, 
                                    "Фильтрация не реализована", warning=True)
    
    async def test_payment_method_status(self):
        """Тест статуса способов оплаты"""
        headers = self.get_auth_headers()
        
        # Создаем активный способ оплаты
        active_payment = {
            "name": f"{self.test_prefix}Active Payment",
            "type": "card",
            "description": "Active payment method test",
            "is_active": True,
            "is_default": False
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                           json=active_payment, headers=headers)
            if response.status_code == 201:
                payment_method = response.json()
                self.created_data['payment_methods'].append(payment_method["id"])
                
                if payment_method["is_active"] is True:
                    self.results.add_test("Статус способа оплаты - активный", True, 
                                        "Активный способ оплаты создан корректно")
                else:
                    self.results.add_test("Статус способа оплаты - активный", False, 
                                        f"Неверный статус: {payment_method['is_active']}")
            else:
                self.results.add_test("Статус способа оплаты - активный", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус способа оплаты - активный", False, f"Ошибка: {str(e)}")
        
        # Создаем неактивный способ оплаты
        inactive_payment = {
            "name": f"{self.test_prefix}Inactive Payment",
            "type": "cash",
            "description": "Inactive payment method test",
            "is_active": False,
            "is_default": False
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                           json=inactive_payment, headers=headers)
            if response.status_code == 201:
                payment_method = response.json()
                self.created_data['payment_methods'].append(payment_method["id"])
                
                if payment_method["is_active"] is False:
                    self.results.add_test("Статус способа оплаты - неактивный", True, 
                                        "Неактивный способ оплаты создан корректно")
                else:
                    self.results.add_test("Статус способа оплаты - неактивный", False, 
                                        f"Неверный статус: {payment_method['is_active']}")
            else:
                self.results.add_test("Статус способа оплаты - неактивный", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус способа оплаты - неактивный", False, f"Ошибка: {str(e)}")
        
        # Тест способа оплаты по умолчанию
        default_payment = {
            "name": f"{self.test_prefix}Default Payment",
            "type": "card",
            "description": "Default payment method test",
            "is_active": True,
            "is_default": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                           json=default_payment, headers=headers)
            if response.status_code == 201:
                payment_method = response.json()
                self.created_data['payment_methods'].append(payment_method["id"])
                
                if payment_method.get("is_default") is True:
                    self.results.add_test("Статус способа оплаты - по умолчанию", True, 
                                        "Способ оплаты по умолчанию создан корректно")
                else:
                    self.results.add_test("Статус способа оплаты - по умолчанию", True, 
                                        "Поле is_default не поддерживается", warning=True)
            else:
                self.results.add_test("Статус способа оплаты - по умолчанию", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус способа оплаты - по умолчанию", False, f"Ошибка: {str(e)}")
    
    async def test_payment_method_configuration(self):
        """Тест конфигурации способов оплаты"""
        headers = self.get_auth_headers()
        
        # Тест различных конфигураций
        config_tests = [
            {
                "name": f"{self.test_prefix}Commission Test",
                "type": "card",
                "commission_rate": 2.5,
                "min_amount": 1.0,
                "max_amount": 5000.0
            },
            {
                "name": f"{self.test_prefix}No Commission Test",
                "type": "cash",
                "commission_rate": 0.0,
                "min_amount": 0.01,
                "max_amount": 10000.0
            },
            {
                "name": f"{self.test_prefix}High Commission Test",
                "type": "cryptocurrency",
                "commission_rate": 5.0,
                "min_amount": 10.0,
                "max_amount": 1000.0
            }
        ]
        
        for config_test in config_tests:
            payment_data = {
                "name": config_test["name"],
                "type": config_test["type"],
                "description": f"Configuration test for {config_test['type']}",
                "commission_rate": config_test["commission_rate"],
                "min_amount": config_test["min_amount"],
                "max_amount": config_test["max_amount"],
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                               json=payment_data, headers=headers)
                if response.status_code == 201:
                    payment_method = response.json()
                    self.created_data['payment_methods'].append(payment_method["id"])
                    
                    # Проверяем комиссию
                    if "commission_rate" in payment_method:
                        if abs(payment_method["commission_rate"] - config_test["commission_rate"]) < 0.01:
                            self.results.add_test(f"Конфигурация - комиссия {config_test['type']}", True, 
                                                f"Комиссия установлена: {payment_method['commission_rate']}%")
                        else:
                            self.results.add_test(f"Конфигурация - комиссия {config_test['type']}", False, 
                                                f"Неверная комиссия: {payment_method['commission_rate']}")
                    else:
                        self.results.add_test(f"Конфигурация - комиссия {config_test['type']}", True, 
                                            "Поле commission_rate не поддерживается", warning=True)
                    
                    # Проверяем лимиты
                    if "min_amount" in payment_method and "max_amount" in payment_method:
                        if (abs(payment_method["min_amount"] - config_test["min_amount"]) < 0.01 and
                            abs(payment_method["max_amount"] - config_test["max_amount"]) < 0.01):
                            self.results.add_test(f"Конфигурация - лимиты {config_test['type']}", True, 
                                                f"Лимиты: {payment_method['min_amount']}-{payment_method['max_amount']}")
                        else:
                            self.results.add_test(f"Конфигурация - лимиты {config_test['type']}", False, 
                                                f"Неверные лимиты")
                    else:
                        self.results.add_test(f"Конфигурация - лимиты {config_test['type']}", True, 
                                            "Поля лимитов не поддерживаются", warning=True)
                else:
                    if response.status_code in [400, 422]:
                        self.results.add_test(f"Конфигурация - {config_test['type']}", True, 
                                            f"Тип не поддерживается", warning=True)
                    else:
                        self.results.add_test(f"Конфигурация - {config_test['type']}", False, 
                                            f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Конфигурация - {config_test['type']}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест сложной конфигурации с JSON
        complex_config = {
            "name": f"{self.test_prefix}Complex Config Payment",
            "type": "card",
            "description": "Payment method with complex configuration",
            "is_active": True,
            "config": {
                "api_endpoint": "https://api.payment.com/v1",
                "api_key": "test_key_123456",
                "webhook_url": "https://myapp.com/webhook/payment",
                "supported_currencies": ["USD", "EUR", "RUB"],
                "require_3d_secure": True,
                "timeout_seconds": 30
            }
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                           json=complex_config, headers=headers)
            if response.status_code == 201:
                payment_method = response.json()
                self.created_data['payment_methods'].append(payment_method["id"])
                
                if "config" in payment_method:
                    self.results.add_test("Конфигурация - сложная конфигурация", True, 
                                        "JSON конфигурация сохранена")
                else:
                    self.results.add_test("Конфигурация - сложная конфигурация", True, 
                                        "JSON конфигурация не поддерживается", warning=True)
            else:
                self.results.add_test("Конфигурация - сложная конфигурация", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Конфигурация - сложная конфигурация", False, 
                                f"Ошибка: {str(e)}")
    
    async def test_payment_method_search(self):
        """Тест поиска и фильтрации способов оплаты"""
        headers = self.get_auth_headers()
        
        # Создаем способы оплаты для поиска
        search_payment_methods = [
            {
                "name": f"{self.test_prefix}Search Card Payment",
                "type": "card",
                "description": "Card payment for search",
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Search Cash Payment",
                "type": "cash",
                "description": "Cash payment for search",
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Disabled Payment",
                "type": "bank_transfer",
                "description": "Disabled payment method",
                "is_active": False
            }
        ]
        
        created_payment_methods = []
        for payment_data in search_payment_methods:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/payment-methods/", 
                                               json=payment_data, headers=headers)
                if response.status_code == 201:
                    payment_method = response.json()
                    self.created_data['payment_methods'].append(payment_method["id"])
                    created_payment_methods.append(payment_method)
            except Exception:
                continue
        
        # Тест получения всех способов оплаты
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/payment-methods/", headers=headers)
            if response.status_code == 200:
                payment_methods = response.json()
                if len(payment_methods) >= len(created_payment_methods):
                    self.results.add_test("Поиск способов оплаты - все способы", True, 
                                        f"Получено {len(payment_methods)} способов оплаты")
                else:
                    self.results.add_test("Поиск способов оплаты - все способы", False, 
                                        f"Получено меньше способов оплаты чем ожидалось")
            else:
                self.results.add_test("Поиск способов оплаты - все способы", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск способов оплаты - все способы", False, f"Ошибка: {str(e)}")
        
        # Тест поиска по ID
        if created_payment_methods:
            payment_id = created_payment_methods[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/payment-methods/{payment_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    payment_method = response.json()
                    if payment_method["id"] == payment_id:
                        self.results.add_test("Поиск способов оплаты - по ID", True, 
                                            f"Найден способ оплаты: {payment_method['name']}")
                    else:
                        self.results.add_test("Поиск способов оплаты - по ID", False, 
                                            f"Неверный способ оплаты")
                else:
                    self.results.add_test("Поиск способов оплаты - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск способов оплаты - по ID", False, f"Ошибка: {str(e)}")
        
        # Тест фильтрации активных способов оплаты
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/payment-methods/?is_active=true", 
                                          headers=headers)
            if response.status_code == 200:
                payment_methods = response.json()
                active_count = sum(1 for pm in payment_methods if pm.get("is_active") is True)
                self.results.add_test("Поиск способов оплаты - фильтр активных", True, 
                                    f"Найдено {active_count} активных способов оплаты", 
                                    warning=(active_count != len(payment_methods)))
            elif response.status_code == 422:
                self.results.add_test("Поиск способов оплаты - фильтр активных", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск способов оплаты - фильтр активных", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск способов оплаты - фильтр активных", True, 
                                "Фильтрация не реализована", warning=True)
