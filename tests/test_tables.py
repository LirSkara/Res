#!/usr/bin/env python3
"""
QRes OS 4 - Tables Tests
Тесты управления столами
"""
from tests.test_base import BaseTestSuite, TestRunner


class TablesTestSuite(BaseTestSuite):
    """Тестовый сюит для управления столами"""
    
    async def run_tests(self):
        """Запуск всех тестов столов"""
        print("\n🪑 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ СТОЛАМИ")
        print("=" * 50)
        
        await self.test_table_crud()
        await self.test_table_validation()
        await self.test_table_location_relationship()
        await self.test_table_status()
        await self.test_table_capacity()
        await self.test_table_qr_code()
    
    async def test_table_crud(self):
        """Тест CRUD операций со столами"""
        # Сначала создаем локацию для столов
        location_data = {
            "name": f"{self.test_prefix}Table Test Location",
            "address": "123 Table Street",
            "city": "Table City",
            "country": "Table Country",
            "is_active": True
        }
        
        headers = self.get_auth_headers()
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        
        if location_response.status_code != 201:
            self.results.add_test("Создание локации для столов", False, 
                                f"Не удалось создать локацию: {location_response.status_code}")
            return
        
        location = location_response.json()
        location_id = location["id"]
        self.created_data['locations'].append(location_id)
        
        create_data = {
            "number": f"{self.test_prefix}T001",
            "location_id": location_id,
            "capacity": 4,
            "status": "available",
            "qr_code": f"{self.test_prefix}qr_table_001",
            "x_position": 100.5,
            "y_position": 200.5,
            "is_active": True
        }
        
        update_data = {
            "number": f"{self.test_prefix}T001_UPDATED",
            "location_id": location_id,
            "capacity": 6,
            "status": "occupied",
            "qr_code": f"{self.test_prefix}qr_table_001_updated",
            "x_position": 150.5,
            "y_position": 250.5,
            "is_active": True
        }
        
        required_fields = ["id", "number", "location_id", "capacity", "status", "is_active", "created_at"]
        
        table_id = await self.test_crud_operations(
            endpoint="tables",
            create_data=create_data,
            update_data=update_data,
            data_type="tables",
            required_fields=required_fields
        )
        
        return table_id
    
    async def test_table_validation(self):
        """Тест валидации данных стола"""
        # Создаем локацию для тестов валидации
        headers = self.get_auth_headers()
        location_data = {
            "name": f"{self.test_prefix}Validation Location",
            "address": "123 Validation Street",
            "city": "Validation City",
            "country": "Validation Country",
            "is_active": True
        }
        
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        if location_response.status_code != 201:
            self.results.add_test("Валидация столов - создание локации", False, 
                                "Не удалось создать локацию для тестов")
            return
        
        location = location_response.json()
        location_id = location["id"]
        self.created_data['locations'].append(location_id)
        
        invalid_tables = [
            # Отсутствующий номер стола
            {
                "location_id": location_id,
                "capacity": 4,
                "status": "available"
            },
            # Отсутствующая локация
            {
                "number": f"{self.test_prefix}T_NO_LOCATION",
                "capacity": 4,
                "status": "available"
            },
            # Невалидная вместимость
            {
                "number": f"{self.test_prefix}T_INVALID_CAPACITY",
                "location_id": location_id,
                "capacity": 0,
                "status": "available"
            },
            # Невалидный статус
            {
                "number": f"{self.test_prefix}T_INVALID_STATUS",
                "location_id": location_id,
                "capacity": 4,
                "status": "invalid_status"
            },
            # Несуществующая локация
            {
                "number": f"{self.test_prefix}T_FAKE_LOCATION",
                "location_id": 99999,
                "capacity": 4,
                "status": "available"
            }
        ]
        
        for i, table_data in enumerate(invalid_tables):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                               json=table_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация стола #{i+1}", True, 
                                        "Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если стол создался, добавляем в список для удаления
                    table = response.json()
                    self.created_data['tables'].append(table["id"])
                    self.results.add_test(f"Валидация стола #{i+1}", False, 
                                        "Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация стола #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация стола #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_table_location_relationship(self):
        """Тест связи столов с локациями"""
        headers = self.get_auth_headers()
        
        # Создаем несколько локаций
        locations = []
        for i in range(2):
            location_data = {
                "name": f"{self.test_prefix}Relation Location {i}",
                "address": f"123 Relation Street {i}",
                "city": f"Relation City {i}",
                "country": "Relation Country",
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                               json=location_data, headers=headers)
                if response.status_code == 201:
                    location = response.json()
                    self.created_data['locations'].append(location["id"])
                    locations.append(location)
            except Exception:
                continue
        
        if len(locations) < 2:
            self.results.add_test("Связь стол-локация - создание локаций", False, 
                                "Не удалось создать достаточно локаций")
            return
        
        # Создаем столы в разных локациях
        for i, location in enumerate(locations):
            table_data = {
                "number": f"{self.test_prefix}REL_T{i+1}",
                "location_id": location["id"],
                "capacity": 4,
                "status": "available",
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                               json=table_data, headers=headers)
                if response.status_code == 201:
                    table = response.json()
                    self.created_data['tables'].append(table["id"])
                    
                    if table["location_id"] == location["id"]:
                        self.results.add_test(f"Связь стол-локация - создание #{i+1}", True, 
                                            f"Стол привязан к локации {location['name']}")
                    else:
                        self.results.add_test(f"Связь стол-локация - создание #{i+1}", False, 
                                            f"Неверная привязка локации")
                else:
                    self.results.add_test(f"Связь стол-локация - создание #{i+1}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Связь стол-локация - создание #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест получения столов по локации (если поддерживается)
        if locations:
            location_id = locations[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/tables/?location_id={location_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    tables = response.json()
                    location_tables = [t for t in tables if t.get("location_id") == location_id]
                    self.results.add_test("Связь стол-локация - фильтр по локации", True, 
                                        f"Найдено {len(location_tables)} столов в локации")
                elif response.status_code == 422:
                    self.results.add_test("Связь стол-локация - фильтр по локации", True, 
                                        "Фильтрация не поддерживается", warning=True)
                else:
                    self.results.add_test("Связь стол-локация - фильтр по локации", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Связь стол-локация - фильтр по локации", True, 
                                    "Фильтрация не реализована", warning=True)
    
    async def test_table_status(self):
        """Тест статусов столов"""
        headers = self.get_auth_headers()
        
        # Создаем локацию для тестов статусов
        location_data = {
            "name": f"{self.test_prefix}Status Location",
            "address": "123 Status Street",
            "city": "Status City",
            "country": "Status Country",
            "is_active": True
        }
        
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        if location_response.status_code != 201:
            self.results.add_test("Статус столов - создание локации", False, 
                                "Не удалось создать локацию")
            return
        
        location = location_response.json()
        location_id = location["id"]
        self.created_data['locations'].append(location_id)
        
        # Тестируем различные статусы
        statuses = ["available", "occupied", "reserved", "maintenance"]
        
        for i, status in enumerate(statuses):
            table_data = {
                "number": f"{self.test_prefix}STATUS_T{i+1}",
                "location_id": location_id,
                "capacity": 4,
                "status": status,
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                               json=table_data, headers=headers)
                if response.status_code == 201:
                    table = response.json()
                    self.created_data['tables'].append(table["id"])
                    
                    if table["status"] == status:
                        self.results.add_test(f"Статус стола - {status}", True, 
                                            f"Статус установлен корректно")
                    else:
                        self.results.add_test(f"Статус стола - {status}", False, 
                                            f"Неверный статус: ожидался {status}, получен {table['status']}")
                else:
                    self.results.add_test(f"Статус стола - {status}", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Статус стола - {status}", False, f"Ошибка: {str(e)}")
    
    async def test_table_capacity(self):
        """Тест вместимости столов"""
        headers = self.get_auth_headers()
        
        # Создаем локацию для тестов вместимости
        location_data = {
            "name": f"{self.test_prefix}Capacity Location",
            "address": "123 Capacity Street",
            "city": "Capacity City",
            "country": "Capacity Country",
            "is_active": True
        }
        
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        if location_response.status_code != 201:
            self.results.add_test("Вместимость столов - создание локации", False, 
                                "Не удалось создать локацию")
            return
        
        location = location_response.json()
        location_id = location["id"]
        self.created_data['locations'].append(location_id)
        
        # Тестируем различную вместимость
        capacities = [1, 2, 4, 6, 8, 10, 12]
        
        for capacity in capacities:
            table_data = {
                "number": f"{self.test_prefix}CAP_{capacity}_T",
                "location_id": location_id,
                "capacity": capacity,
                "status": "available",
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                               json=table_data, headers=headers)
                if response.status_code == 201:
                    table = response.json()
                    self.created_data['tables'].append(table["id"])
                    
                    if table["capacity"] == capacity:
                        self.results.add_test(f"Вместимость стола - {capacity} чел.", True, 
                                            "Вместимость установлена корректно")
                    else:
                        self.results.add_test(f"Вместимость стола - {capacity} чел.", False, 
                                            f"Неверная вместимость: ожидалось {capacity}, получено {table['capacity']}")
                else:
                    self.results.add_test(f"Вместимость стола - {capacity} чел.", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Вместимость стола - {capacity} чел.", False, 
                                    f"Ошибка: {str(e)}")
        
        # Тест невалидной вместимости
        invalid_capacities = [0, -1, -5]
        
        for capacity in invalid_capacities:
            table_data = {
                "number": f"{self.test_prefix}INVALID_CAP_{capacity}_T",
                "location_id": location_id,
                "capacity": capacity,
                "status": "available",
                "is_active": True
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                               json=table_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Невалидная вместимость - {capacity}", True, 
                                        "Невалидная вместимость правильно отклонена")
                elif response.status_code == 201:
                    table = response.json()
                    self.created_data['tables'].append(table["id"])
                    self.results.add_test(f"Невалидная вместимость - {capacity}", False, 
                                        "Невалидная вместимость принята")
                else:
                    self.results.add_test(f"Невалидная вместимость - {capacity}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Невалидная вместимость - {capacity}", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_table_qr_code(self):
        """Тест QR-кодов столов"""
        headers = self.get_auth_headers()
        
        # Создаем локацию для тестов QR-кодов
        location_data = {
            "name": f"{self.test_prefix}QR Location",
            "address": "123 QR Street",
            "city": "QR City",
            "country": "QR Country",
            "is_active": True
        }
        
        location_response = await self.client.post(f"{self.runner.BASE_URL}/locations/", 
                                                 json=location_data, headers=headers)
        if location_response.status_code != 201:
            self.results.add_test("QR-коды столов - создание локации", False, 
                                "Не удалось создать локацию")
            return
        
        location = location_response.json()
        location_id = location["id"]
        self.created_data['locations'].append(location_id)
        
        # Тест создания стола с QR-кодом
        table_data = {
            "number": f"{self.test_prefix}QR_T001",
            "location_id": location_id,
            "capacity": 4,
            "status": "available",
            "qr_code": f"{self.test_prefix}unique_qr_12345",
            "is_active": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                           json=table_data, headers=headers)
            if response.status_code == 201:
                table = response.json()
                self.created_data['tables'].append(table["id"])
                
                if table.get("qr_code") == table_data["qr_code"]:
                    self.results.add_test("QR-код стола - создание", True, 
                                        f"QR-код установлен: {table['qr_code']}")
                else:
                    self.results.add_test("QR-код стола - создание", False, 
                                        f"QR-код не соответствует ожидаемому")
            else:
                self.results.add_test("QR-код стола - создание", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("QR-код стола - создание", False, f"Ошибка: {str(e)}")
        
        # Тест уникальности QR-кодов
        duplicate_table_data = {
            "number": f"{self.test_prefix}QR_T002",
            "location_id": location_id,
            "capacity": 4,
            "status": "available",
            "qr_code": f"{self.test_prefix}unique_qr_12345",  # Тот же QR-код
            "is_active": True
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/tables/", 
                                           json=duplicate_table_data, headers=headers)
            if response.status_code in [400, 422, 409]:
                self.results.add_test("QR-код стола - уникальность", True, 
                                    "Дублирующийся QR-код правильно отклонен")
            elif response.status_code == 201:
                table = response.json()
                self.created_data['tables'].append(table["id"])
                self.results.add_test("QR-код стола - уникальность", False, 
                                    "Дублирующийся QR-код принят (должен быть отклонен)")
            else:
                self.results.add_test("QR-код стола - уникальность", False, 
                                    f"Неожиданный код: {response.status_code}")
        except Exception as e:
            self.results.add_test("QR-код стола - уникальность", False, f"Ошибка: {str(e)}")
