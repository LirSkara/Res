# 📶 Настройка WiFi точки доступа для QRes OS 4

## 🎯 Цель
Настроить Raspberry Pi как WiFi точку доступа, чтобы планшеты могли подключаться напрямую к серверу QRes OS 4.

## 🏗️ Архитектура сети

```
🍓 Raspberry Pi (192.168.4.1) - Сервер QRes OS 4 + WiFi AP
│
├── 📱 Планшет 1 (192.168.4.2)
├── 📱 Планшет 2 (192.168.4.3)  
├── 📱 Планшет 3 (192.168.4.4)
└── 📱 Планшет N (192.168.4.5-20)
```

## 🔧 Настройка WiFi точки доступа

### 1. Установка необходимых пакетов

```bash
sudo apt update
sudo apt install hostapd dnsmasq iptables-persistent
```

### 2. Настройка статического IP для wlan0

Создайте файл `/etc/dhcpcd.conf` или добавьте в конец:

```bash
# WiFi AP interface
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```

### 3. Настройка dnsmasq (DHCP сервер)

Создайте резервную копию конфига:
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

Создайте новый `/etc/dnsmasq.conf`:
```bash
# WiFi AP DHCP settings
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h

# DNS settings
dhcp-option=6,8.8.8.8,8.8.4.4

# Логирование
log-dhcp
log-queries
```

### 4. Настройка hostapd (WiFi AP)

Создайте файл `/etc/hostapd/hostapd.conf`:

```bash
# WiFi interface
interface=wlan0

# WiFi driver
driver=nl80211

# Network settings
ssid=QRes-Restaurant
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0

# Security settings
wpa=2
wpa_passphrase=qresos2024
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Performance settings
ieee80211n=1
require_ht=1
ht_capab=[SHORT-GI-20][SHORT-GI-40][HT40+]
```

Укажите путь к конфигу в `/etc/default/hostapd`:
```bash
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

### 5. Настройка маршрутизации (опционально)

Если нужен доступ в интернет через Ethernet:

```bash
# Включаем IP forwarding
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Настраиваем NAT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# Сохраняем правила
sudo sh -c "iptables-save > /etc/iptables/rules.v4"
```

### 6. Запуск сервисов

```bash
# Включаем сервисы
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Запускаем сервисы
sudo systemctl start hostapd
sudo systemctl start dnsmasq

# Перезагружаем сеть
sudo systemctl restart dhcpcd
```

## 🔍 Проверка настройки

### Проверка статуса сервисов

```bash
# Статус WiFi AP
sudo systemctl status hostapd

# Статус DHCP сервера
sudo systemctl status dnsmasq

# Проверка интерфейса
ip addr show wlan0
```

### Проверка подключенных устройств

```bash
# Активные DHCP аренды
cat /var/lib/dhcp/dhcpd.leases

# Или для dnsmasq
sudo cat /var/lib/dhcp/dhcpcd.leases

# ARP таблица (подключенные устройства)
arp -a
```

### Проверка доступности QRes OS 4

```bash
# С Raspberry Pi
curl http://192.168.4.1:8000/docs

# Логи подключений планшетов
sudo journalctl -u qresos-backend -f
```

## 📱 Подключение планшетов

### На планшете/устройстве:

1. **Найдите WiFi сеть**: `QRes-Restaurant`
2. **Введите пароль**: `qresos2024`
3. **Откройте браузер** и перейдите: `http://192.168.4.1:8000`

### Доступные интерфейсы:

- **API документация**: http://192.168.4.1:8000/docs
- **Админ панель**: http://192.168.4.1:8000/admin (если есть)
- **Меню для клиентов**: http://192.168.4.1:8000/menu

## 🛠️ Устранение неполадок

### WiFi AP не запускается

```bash
# Проверка конфликтов
sudo systemctl status hostapd -l

# Проверка интерфейса
iwconfig

# Проверка конфига
sudo hostapd -dd /etc/hostapd/hostapd.conf
```

### Планшеты не получают IP

```bash
# Проверка dnsmasq
sudo systemctl status dnsmasq -l

# Проверка портов
sudo ss -tulpn | grep :67  # DHCP

# Перезапуск DHCP
sudo systemctl restart dnsmasq
```

### Нет доступа к серверу

```bash
# Проверка файрвола
sudo ufw status

# Разрешить порт 8000
sudo ufw allow 8000/tcp

# Проверка QRes OS 4
sudo qresos-control status
```

## 🔒 Безопасность

### Рекомендации:

1. **Смените пароль WiFi** в `/etc/hostapd/hostapd.conf`
2. **Ограничьте количество подключений** в dnsmasq
3. **Настройте фильтрацию MAC адресов** (опционально)
4. **Регулярно обновляйте систему**

### Фильтрация MAC адресов (опционально):

В `/etc/hostapd/hostapd.conf`:
```bash
# Включить фильтрацию MAC
macaddr_acl=1
accept_mac_file=/etc/hostapd/hostapd.accept

# Запретить неизвестные устройства
deny_mac_file=/etc/hostapd/hostapd.deny
```

Создайте файл `/etc/hostapd/hostapd.accept`:
```bash
# Разрешенные MAC адреса планшетов
aa:bb:cc:dd:ee:ff  # Планшет 1
11:22:33:44:55:66  # Планшет 2
```

## 🚀 Автоматический запуск

Для автоматического запуска WiFi AP при загрузке системы все сервисы уже настроены через systemd.

После перезагрузки проверьте:

```bash
sudo systemctl status hostapd dnsmasq qresos-backend
```

## 📊 Мониторинг

### Скрипт для мониторинга подключений:

```bash
#!/bin/bash
# Создать файл /usr/local/bin/wifi-monitor.sh

echo "=== QRes WiFi AP Status ==="
echo "Date: $(date)"
echo ""

echo "=== Connected Devices ==="
arp -a | grep "192.168.4"
echo ""

echo "=== DHCP Leases ==="
if [ -f /var/lib/dhcp/dhcpcd.leases ]; then
    cat /var/lib/dhcp/dhcpcd.leases | tail -10
fi
echo ""

echo "=== QRes Server Status ==="
curl -s http://192.168.4.1:8000/health || echo "Server not responding"
echo ""
```

Сделать исполняемым и добавить в cron:
```bash
sudo chmod +x /usr/local/bin/wifi-monitor.sh
echo "*/5 * * * * /usr/local/bin/wifi-monitor.sh >> /var/log/wifi-monitor.log" | sudo crontab -
```
