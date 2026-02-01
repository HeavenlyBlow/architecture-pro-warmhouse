# SmartHome Platform - Проектная работа

## Задание 1. Анализ и планирование

### 1. Описание функциональности монолитного приложения

**Управление отоплением:**
- Пользователи могут создавать и настраивать датчики температуры
- Система поддерживает CRUD операции над сенсорами
- Пользователи могут обновлять показания датчиков

**Мониторинг температуры:**
- Пользователи могут просматривать текущие показания всех датчиков
- Система поддерживает получение температуры по локации через внешний API
- Данные хранятся в PostgreSQL базе данных

### 2. Анализ архитектуры монолитного приложения

1. Язык программирования: Go
2. Web-фреймворк: Gin
3. База данных: PostgreSQL
4. Драйвер БД: pgx (native driver)
5. Архитектура: монолит 
6. API: REST, синхронное взаимодействие

Структура кода:
- `handlers/` - HTTP обработчики (SensorHandler)
- `services/` - бизнес-логика (TemperatureService)
- `db/` - слой работы с БД
- `models/` - модели данных (Sensor)

### 3. Определение доменов и границы контекстов (As-Is)

В монолите выделен единственный домен:

1. **Сенсоры (Sensors)** - управление датчиками температуры
   - CRUD операции над сенсорами (создание, чтение, обновление, удаление)
   - Получение показаний температуры по локации через внешний Temperature API
   - Обновление значений и статуса датчиков
   - Хранение данных в единой таблице `sensors`

Границы контекста размыты - вся логика (работа с БД, вызов внешнего API, HTTP обработка) находится в одном приложении без чёткого разделения ответственности.

### 4. Проблемы монолитного решения

1. Единая точка отказа - падение приложения останавливает всю систему
2. Сложность масштабирования - нельзя масштабировать отдельные компоненты
3. Синхронное взаимодействие - блокирующие вызовы к внешнему Temperature API
4. Единая БД - все данные в одной базе, сложно изолировать нагрузку
5. Монолитный деплой - любое изменение требует пересборки всего приложения
6. Технологический стек - привязка к одному языку (Go)

### 5. Визуализация системы As-Is — диаграммы С4

- [C4 Context (As-Is)](apps/schemas/asis/c4-context.puml) - контекст монолита
- [C4 Container (As-Is)](apps/schemas/asis/c4-container.puml) - внутренняя структура
- [Code Classes (As-Is)](apps/schemas/asis/code-classes.puml) - UML классы (SensorHandler, DB, TemperatureService)
- [Code Sequence (As-Is)](apps/schemas/asis/code-sequence.puml) - последовательность вызовов GET /api/v1/sensors

---

## Задание 2. Проектирование микросервисной архитектуры

### Диаграмма контейнеров (Containers)

- [C4 Context (To-Be)](apps/schemas/tobe/c4-context.puml)
- [C4 Container (To-Be)](apps/schemas/tobe/c4-container.puml)

### Диаграмма компонентов (Components)

- [C4 Components](apps/schemas/tobe/c4-components.puml)

### Диаграмма кода (Code)

- [Code Classes (To-Be)](apps/schemas/tobe/code-classes.puml) - UML классы микросервисов
- [Code Sequence (To-Be)](apps/schemas/tobe/code-sequence.puml) - последовательность /api/v2/devices
- [Привязка устройства](apps/schemas/tobe/sequence-device-pairing.puml)
- [Отправка команды](apps/schemas/tobe/sequence-command.puml)
- [Сбор телеметрии](apps/schemas/tobe/sequence-telemetry.puml)

---

## Задание 3. Разработка ER-диаграммы

- [ER Diagram](apps/schemas/tobe/er-diagram.puml)

Ключевые сущности: users, devices, sensors, telemetry, commands

---

## Задание 4. Создание и документирование API

### 1. Тип API

REST API для синхронного взаимодействия клиентов с микросервисами. MQTT для асинхронного взаимодействия между сервисами (телеметрия, команды, события).

Обоснование: REST обеспечивает простоту интеграции для клиентов, MQTT - эффективную асинхронную коммуникацию для IoT устройств.

### 2. Документация API (Swagger)

1. Smart Home: http://localhost:8081/swagger/index.html
2. Telemetry: http://localhost:8082/swagger/index.html
3. Command: http://localhost:8083/docs
4. Simulator: http://localhost:8084/docs

---

## Задание 5. Работа с Docker и docker-compose

Структура:
- `docker-compose.yml` - оркестрация всех сервисов
- `init.sh` - скрипт запуска
- `init-databases.sh` - инициализация БД

Запуск:
```bash
./init.sh
```

Тестирование: импортируйте `smarthome-api.postman_collection.json`

---

## Задание 6. Разработка MVP

### Созданные микросервисы

1. **smart-home** (Go, порт 8081) - v1: legacy сенсоры, v2: пользователи, устройства
2. **telemetry-service** (C# .NET 8, порт 8082) - сбор телеметрии через MQTT
3. **command-service** (Python FastAPI, порт 8083) - отправка команд, отслеживание статуса
4. **device-simulator** (Python FastAPI, порт 8084) - симуляция IoT устройств

### Интеграция

1. API Gateway (Nginx) - единая точка входа на порту 8080
2. MQTT (Mosquitto) - асинхронная коммуникация между сервисами
3. PostgreSQL - отдельные базы для каждого домена (smarthome, telemetry, command)
