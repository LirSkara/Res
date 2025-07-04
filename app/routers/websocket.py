"""
QRes OS 4 - WebSocket Router
WebSocket для real-time коммуникации между официантами и кухней
"""
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio
from datetime import datetime

from ..deps import DatabaseSession
from ..services.auth import AuthService
from ..models import User, UserRole
from ..schemas import OrderWebSocketMessage


router = APIRouter()
security = HTTPBearer()


class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Словарь активных соединений: user_id -> websocket
        self.active_connections: Dict[int, WebSocket] = {}
        # Группы по ролям
        self.waiters: Dict[int, WebSocket] = {}
        self.kitchen: Dict[int, WebSocket] = {}
        self.admins: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user: User):
        """Подключение пользователя"""
        await websocket.accept()
        
        # Отключаем предыдущее соединение если есть
        if user.id in self.active_connections:
            try:
                await self.active_connections[user.id].close()
            except:
                pass
        
        # Добавляем новое соединение
        self.active_connections[user.id] = websocket
        
        # Добавляем в соответствующую группу по роли
        if user.role == UserRole.WAITER:
            self.waiters[user.id] = websocket
        elif user.role == UserRole.KITCHEN:
            self.kitchen[user.id] = websocket
        elif user.role == UserRole.ADMIN:
            self.admins[user.id] = websocket
        
        print(f"🔌 Пользователь {user.username} ({user.role}) подключился к WebSocket")
    
    def disconnect(self, user_id: int):
        """Отключение пользователя"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.waiters:
            del self.waiters[user_id]
        
        if user_id in self.kitchen:
            del self.kitchen[user_id]
        
        if user_id in self.admins:
            del self.admins[user_id]
        
        print(f"❌ Пользователь {user_id} отключился от WebSocket")
    
    async def send_personal_message(self, message: str, user_id: int):
        """Отправка личного сообщения"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except:
                self.disconnect(user_id)
    
    async def send_to_waiters(self, message: str):
        """Отправка сообщения всем официантам"""
        disconnected = []
        for user_id, websocket in self.waiters.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(user_id)
        
        # Удаляем отключенных
        for user_id in disconnected:
            self.disconnect(user_id)
    
    async def send_to_kitchen(self, message: str):
        """Отправка сообщения всей кухне"""
        disconnected = []
        for user_id, websocket in self.kitchen.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(user_id)
        
        # Удаляем отключенных
        for user_id in disconnected:
            self.disconnect(user_id)
    
    async def send_to_admins(self, message: str):
        """Отправка сообщения всем администраторам"""
        disconnected = []
        for user_id, websocket in self.admins.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(user_id)
        
        # Удаляем отключенных
        for user_id in disconnected:
            self.disconnect(user_id)
    
    async def broadcast(self, message: str):
        """Отправка сообщения всем подключенным"""
        disconnected = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(user_id)
        
        # Удаляем отключенных
        for user_id in disconnected:
            self.disconnect(user_id)
    
    def get_active_users(self) -> dict:
        """Получение статистики активных пользователей"""
        return {
            "total": len(self.active_connections),
            "waiters": len(self.waiters),
            "kitchen": len(self.kitchen),
            "admins": len(self.admins)
        }


# Глобальный менеджер соединений
manager = ConnectionManager()


async def get_current_user_ws(
    websocket: WebSocket,
    token: str,
    db: AsyncSession
) -> User:
    """Аутентификация пользователя для WebSocket"""
    try:
        token_data = AuthService.verify_token(token)
        user = await AuthService.get_user_by_id(db, token_data.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь неактивен"
            )
        
        return user
    
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации"
        )


@router.websocket("/orders")
async def websocket_orders(
    websocket: WebSocket,
    token: str,
    db: DatabaseSession
):
    """
    WebSocket эндпоинт для уведомлений о заказах
    
    Параметры:
    - token: JWT токен для аутентификации
    
    События:
    - order_created: Новый заказ создан
    - order_updated: Заказ обновлен
    - order_status_changed: Изменен статус заказа
    - item_status_changed: Изменен статус позиции заказа
    """
    
    # Аутентификация
    user = await get_current_user_ws(websocket, token, db)
    
    # Подключение
    await manager.connect(websocket, user)
    
    try:
        # Отправляем приветственное сообщение
        welcome_message = {
            "type": "connected",
            "message": f"Добро пожаловать, {user.full_name}!",
            "role": user.role.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_message, ensure_ascii=False))
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Ждем сообщения от клиента
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Обрабатываем разные типы сообщений
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    # Ответ на ping
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(pong_message))
                
                elif message_type == "get_stats":
                    # Статистика активных пользователей
                    stats = manager.get_active_users()
                    stats_message = {
                        "type": "stats",
                        "data": stats,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(stats_message, ensure_ascii=False))
                
                elif message_type == "broadcast" and user.role == UserRole.ADMIN:
                    # Широковещательное сообщение (только для админов)
                    broadcast_message = {
                        "type": "broadcast",
                        "message": message_data.get("message", ""),
                        "from": user.full_name,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.broadcast(json.dumps(broadcast_message, ensure_ascii=False))
                
                else:
                    # Неизвестный тип сообщения
                    error_message = {
                        "type": "error",
                        "message": f"Неизвестный тип сообщения: {message_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(error_message, ensure_ascii=False))
            
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Неверный формат JSON",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(error_message, ensure_ascii=False))
            
            except Exception as e:
                print(f"Ошибка в WebSocket: {e}")
                break
    
    except WebSocketDisconnect:
        manager.disconnect(user.id)
    except Exception as e:
        print(f"Ошибка WebSocket соединения: {e}")
        manager.disconnect(user.id)


# Функции для отправки уведомлений из других частей приложения
class WebSocketNotifier:
    """Класс для отправки уведомлений через WebSocket"""
    
    @staticmethod
    async def notify_order_created(order_id: int, table_number: int, waiter_name: str):
        """Уведомление о создании нового заказа"""
        message = {
            "type": "order_created",
            "data": {
                "order_id": order_id,
                "table_number": table_number,
                "waiter_name": waiter_name,
                "message": f"Новый заказ #{order_id} от столика {table_number}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Отправляем кухне и админам
        await manager.send_to_kitchen(json.dumps(message, ensure_ascii=False))
        await manager.send_to_admins(json.dumps(message, ensure_ascii=False))
    
    @staticmethod
    async def notify_order_ready(order_id: int, table_number: int, waiter_id: int):
        """Уведомление о готовности заказа"""
        message = {
            "type": "order_ready",
            "data": {
                "order_id": order_id,
                "table_number": table_number,
                "message": f"Заказ #{order_id} готов! Столик {table_number}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Отправляем конкретному официанту и админам
        await manager.send_personal_message(json.dumps(message, ensure_ascii=False), waiter_id)
        await manager.send_to_admins(json.dumps(message, ensure_ascii=False))
    
    @staticmethod
    async def notify_order_status_changed(order_id: int, old_status: str, new_status: str, table_number: int):
        """Уведомление об изменении статуса заказа"""
        message = {
            "type": "order_status_changed",
            "data": {
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status,
                "table_number": table_number,
                "message": f"Заказ #{order_id}: {old_status} → {new_status}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Отправляем всем
        await manager.broadcast(json.dumps(message, ensure_ascii=False))


# Экспортируем нотификатор для использования в других роутерах
notifier = WebSocketNotifier()
