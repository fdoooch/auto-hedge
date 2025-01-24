# Automatic open contr position for futures trading

## Установка

### 1. Установить Docker и Docker Compose
https://docs.docker.com/compose/install/

### 2. Настроить .env
- Переименовать .env.example в .env
- Заменить значения (после =) API_KEY и API_SECRET на свои ключи Binance Futures API

### 3. Прописать IP машины, на которой запускается скрипи в настройках API-ключа на Binance

### 3. Запустить Docker Compose
из директории с Dockerfile выполнить команду:
```
docker compose up -d
```

### 4. Проверить, что скрипт запустился
из директории с Dockerfile выполнить команду:
```
docker compose logs
```
Увидеть в логах, что скрипт запустился



