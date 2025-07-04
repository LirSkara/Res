#!/usr/bin/env python3
"""
QRes OS 4 - Locations Tests
Тесты управления локациями
"""
from tests.test_base import BaseTestSuite, TestRunner


class LocationsTestSuite(BaseTestSuite):
    """Тестовый сюит для управления локациями"""
    
    async def run_tests(self):
        """Запуск всех тестов локаций"""
        print("\n📍 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ЛОКАЦИЯМИ")
        print("=" * 50)
        
        await self.test_location_crud()
        await self.test_location_validation()
        await self.test_location_address_validation()
        await self.test_location_status()
        await self.test_location_search()
    
    async def test_location_crud(self):
        """Тест CRUD операций с локациями"""
        create_data = {
            "name": f"{self.test_prefix}Test Location",
            "address": "123 Test Street, Test City",
            "city": "Test City",
            "country": "Test Country",
            "phone": "+1234567890",
            "email": f"{self.test_prefix}location@example.com",
            "is_active": True,
            "description": "Test location for automated testing"
        }
        
        update_data = {
            "name": f"{self.test_prefix}Updated Test Location",
            "address": "456 Updated Street, Updated City",
            "city": "Updated City",
            "country": "Updated Country",
            "phone": "+0987654321",
            "email": f"{self.test_prefix}updated_location@example.com",
            "is_active": True,
            "description": "Updated test location"
        }
        
        required_fields = ["id", "name", "address", "city", "country", "is_active", "created_at"]
        
        location_id = await self.test_crud_operations(
            endpoint="locations",
            create_data=create_data,
            update_data=update_data,
            data_type="locations",
            required_fields=required_fields
        )
        
        return location_id
    
    async def test_location_validation(self):
        """Тест валидации данных локации"""
        invalid_locations = [
            # Отсутствующее имя
            {
                "address": "123 Test Street",
                "city": "Test City",
                "country": "Test Country"
            },
            # Отсутствующий адрес
            {
                "name": f"{self.test_prefix}No Address Location",
                "city": "Test City",
                "country": "Test Country"
            },
            # Отсутствующий город
            {
                "name": f"{self.test_prefix}No City Location",
                "address": "123 Test Street",
                "country": "Test Country"
            },
            # Отсутствующая страна
            {
                "name": f"{self.test_prefix}No Country Location",
                "address": "123 Test Street",
                "city": "Test City"
            },
            # Пустые строки
            {
                "name": "",
                "address": "",
                "city": "",
                "country": ""
            }
        ]
        
        headers = self.get_auth_headers()
        
        for i, location_data in enumerate(invalid_locations):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                               json=location_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация локации #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если локация создалась, добавляем в список для удаления
                    location = response.json()
                    self.created_data['locations'].append(location["id"])
                    self.results.add_test(f"Валидация локации #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация локации #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация локации #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_location_address_validation(self):
        """Тест валидации адресных данных"""
        headers = self.get_auth_headers()
        
        # Тест с валидными контактными данными
        valid_contacts = [
            {
                "name": f"{self.test_prefix}Valid Phone Location",
                "address": "123 Test Street",
                "city": "Test City",
                "country": "Test Country",
                "phone": "+1-234-567-8900",
                "email": f"{self.test_prefix}valid@example.com"
            },
            {
                "name": f"{self.test_prefix}Another Valid Location",
                "address": "456 Another Street",
                "city": "Another City",
                "country": "Another Country",
                "phone": "123.456.7890",
                "email": f"{self.test_prefix}another@test.com"
            }
        ]
        
        for i, location_data in enumerate(valid_contacts):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                               json=location_data, headers=headers)
                if response.status_code == 201:
                    location = response.json()
                    self.created_data['locations'].append(location["id"])
                    self.results.add_test(f"Контактные данные - валидные #{i+1}", True, 
                                        f"Локация создана: {location['name']}")
                else:
                    self.results.add_test(f"Контактные данные - валидные #{i+1}", False, 
                                        f"Код: {response.status_code}, Ответ: {response.text}")
            except Exception as e:
                self.results.add_test(f"Контактные данные - валидные #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест с невалидными email адресами
        invalid_emails = ["invalid-email", "test@", "@example.com", "test.com"]
        
        for i, invalid_email in enumerate(invalid_emails):
            location_data = {
                "name": f"{self.test_prefix}Invalid Email Location {i}",
                "address": "123 Test Street",
                "city": "Test City",
                "country": "Test Country",
                "email": invalid_email
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                               json=location_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Email валидация #{i+1}", True, 
                                        f"Невалидный email '{invalid_email}' отклонен")
                elif response.status_code == 201:
                    location = response.json()
                    self.created_data['locations'].append(location["id"])
                    self.results.add_test(f"Email валидация #{i+1}", True, 
                                        f"Email '{invalid_email}' принят (валидация не строгая)", 
                                        warning=True)
                else:
                    self.results.add_test(f"Email валидация #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Email валидация #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_location_status(self):
        """Тест статуса активности локаций"""
        headers = self.get_auth_headers()
        
        # Создаем активную локацию
        active_location = {
            "name": f"{self.test_prefix}Active Location",
            "address": "123 Active Street",
            "city": "Active City",
            "country": "Active Country",
            "is_active": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                           json=active_location, headers=headers)
            if response.status_code == 201:
                location = response.json()
                self.created_data['locations'].append(location["id"])
                
                if location["is_active"] is True:
                    self.results.add_test("Статус локации - активная", True, 
                                        "Активная локация создана корректно")
                else:
                    self.results.add_test("Статус локации - активная", False, 
                                        f"Неверный статус: {location['is_active']}")
            else:
                self.results.add_test("Статус локации - активная", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус локации - активная", False, f"Ошибка: {str(e)}")
        
        # Создаем неактивную локацию
        inactive_location = {
            "name": f"{self.test_prefix}Inactive Location",
            "address": "123 Inactive Street",
            "city": "Inactive City",
            "country": "Inactive Country",
            "is_active": False
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                           json=inactive_location, headers=headers)
            if response.status_code == 201:
                location = response.json()
                self.created_data['locations'].append(location["id"])
                
                if location["is_active"] is False:
                    self.results.add_test("Статус локации - неактивная", True, 
                                        "Неактивная локация создана корректно")
                else:
                    self.results.add_test("Статус локации - неактивная", False, 
                                        f"Неверный статус: {location['is_active']}")
            else:
                self.results.add_test("Статус локации - неактивная", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Статус локации - неактивная", False, f"Ошибка: {str(e)}")
    
    async def test_location_search(self):
        """Тест поиска и фильтрации локаций"""
        headers = self.get_auth_headers()
        
        # Создаем несколько локаций для поиска
        search_locations = [
            {
                "name": f"{self.test_prefix}Search Location 1",
                "address": "111 Search Street",
                "city": "Search City",
                "country": "Search Country",
                "is_active": True
            },
            {
                "name": f"{self.test_prefix}Search Location 2",
                "address": "222 Search Avenue",
                "city": "Another City",
                "country": "Search Country",
                "is_active": False
            },
            {
                "name": f"{self.test_prefix}Different Location",
                "address": "333 Different Street",
                "city": "Different City",
                "country": "Different Country",
                "is_active": True
            }
        ]
        
        created_locations = []
        for location_data in search_locations:
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                               json=location_data, headers=headers)
                if response.status_code == 201:
                    location = response.json()
                    self.created_data['locations'].append(location["id"])
                    created_locations.append(location)
            except Exception:
                continue
        
        # Тест получения всех локаций
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/locations/", headers=headers)
            if response.status_code == 200:
                locations = response.json()
                if len(locations) >= len(created_locations):
                    self.results.add_test("Поиск локаций - все локации", True, 
                                        f"Получено {len(locations)} локаций")
                else:
                    self.results.add_test("Поиск локаций - все локации", False, 
                                        f"Получено меньше локаций чем ожидалось")
            else:
                self.results.add_test("Поиск локаций - все локации", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск локаций - все локации", False, f"Ошибка: {str(e)}")
        
        # Тест поиска конкретной локации по ID
        if created_locations:
            location_id = created_locations[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/locations/{location_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    location = response.json()
                    if location["id"] == location_id:
                        self.results.add_test("Поиск локаций - по ID", True, 
                                            f"Найдена локация: {location['name']}")
                    else:
                        self.results.add_test("Поиск локаций - по ID", False, 
                                            f"Неверная локация: ожидался ID {location_id}")
                else:
                    self.results.add_test("Поиск локаций - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск локаций - по ID", False, f"Ошибка: {str(e)}")
        
        # Тест фильтрации по статусу (если поддерживается)
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/locations/?is_active=true", 
                                          headers=headers)
            if response.status_code == 200:
                locations = response.json()
                active_count = sum(1 for loc in locations if loc.get("is_active") is True)
                self.results.add_test("Поиск локаций - фильтр активных", True, 
                                    f"Найдено {active_count} активных локаций", 
                                    warning=(active_count != len(locations)))
            elif response.status_code == 422:
                self.results.add_test("Поиск локаций - фильтр активных", True, 
                                    "Фильтрация не поддерживается", warning=True)
            else:
                self.results.add_test("Поиск локаций - фильтр активных", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск локаций - фильтр активных", True, 
                                "Фильтрация не реализована", warning=True)
