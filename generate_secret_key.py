#!/usr/bin/env python3
"""
Генератор безопасного SECRET_KEY для QRes OS 4
"""
import secrets
import string

def generate_secret_key(length: int = 64) -> str:
    """Генерирует криптографически стойкий секретный ключ"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    key = generate_secret_key()
    print(f"🔐 Новый безопасный SECRET_KEY (длина: {len(key)}):")
    print(f"SECRET_KEY={key}")
    print(f"\n📋 Скопируйте и вставьте в ваш .env файл:")
    print(f"# Generated secure key - {secrets.token_hex(8)}")
    print(f"SECRET_KEY={key}")
    
    print(f"\n🛡️  Проверка безопасности:")
    print(f"   ✅ Длина: {len(key)} символов (рекомендуется 64+)")
    print(f"   ✅ Содержит буквы: {any(c.isalpha() for c in key)}")
    print(f"   ✅ Содержит цифры: {any(c.isdigit() for c in key)}")
    print(f"   ✅ Содержит спецсимволы: {any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?' for c in key)}")
    print(f"   ✅ Криптографически стойкий: Да (secrets module)")
