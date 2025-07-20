# 🌐 Настройка сетевого интерфейса для QRes OS 4

Для корректной работы QRes OS 4 на фиксированном IP-адресе `192.168.4.1` необходимо настроить сетевой интерфейс.

## � Быстрый старт для разработки

### На Mac/Linux (для разработки)

Используйте скрипт разработки:

```bash
./start-dev.sh
```

Этот скрипт автоматически:
- Создаст виртуальное окружение
- Установит зависимости  
- Настроит локальную конфигурацию (127.0.0.1:8000)
- Запустит сервер в режиме разработки

### На Raspberry Pi (для продакшена)

Используйте обычный скрипт:

```bash
./start.sh
```

Он автоматически определит доступность IP 192.168.4.1 и выберет подходящий адрес.

## 📋 Настройка фиксированного IP (только для Raspberry Pi)

### 1. Создание netplan конфигурации

Создайте файл `/etc/netplan/99-qresos.yaml`:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: true
  wifis:
    wlan0:
      access-points:
        "QRes-WiFi":
          password: "qresos123"
      addresses:
        - 192.168.4.1/24
      dhcp4: false
```

### 2. Применение настроек

```bash
sudo netplan apply
```

### 3. Настройка точки доступа Wi-Fi (опционально)

Установите hostapd и dnsmasq:

```bash
sudo apt update
sudo apt install hostapd dnsmasq
```

Конфигурация hostapd (`/etc/hostapd/hostapd.conf`):

```
interface=wlan0
driver=nl80211
ssid=QRes-WiFi
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=qresos123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Конфигурация dnsmasq (`/etc/dnsmasq.conf`):

```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

### 4. Включение сервисов

```bash
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

## 🔧 Проверка конфигурации

### Проверка IP адреса

```bash
ip addr show
```

### Проверка доступности сервиса

```bash
curl http://192.168.4.1:8000/docs
```

### Проверка статуса QRes OS 4

```bash
sudo qresos-control info
```

## 🐛 Устранение неполадок

### Если IP не назначается

1. Проверьте сетевые интерфейсы:
   ```bash
   ip link show
   ```

2. Перезапустите сетевые сервисы:
   ```bash
   sudo systemctl restart systemd-networkd
   sudo netplan apply
   ```

### Если сервис недоступен по IP

1. Проверьте, запущен ли сервис:
   ```bash
   sudo qresos-control status
   ```

2. Проверьте открытые порты:
   ```bash
   sudo ss -tulpn | grep :8000
   ```

3. Проверьте файрвол:
   ```bash
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

## 📱 Доступ с устройств

После настройки QRes OS 4 будет доступен:

- **Веб-интерфейс**: http://192.168.4.1:8000
- **API документация**: http://192.168.4.1:8000/docs
- **ReDoc**: http://192.168.4.1:8000/redoc

Устройства должны быть подключены к той же сети или к созданной Wi-Fi точке доступа.
