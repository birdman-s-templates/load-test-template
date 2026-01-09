## Описание

Этот репозиторий содержит пример скрипта для проведения нагрузочного тестирования GraphQL API. Проект структурирован для обеспечения масштабируемости, переиспользования кода и удобства поддержки.

## Архитектура проекта

```
load-test-template/
├── locust/
│   ├── load_cp_online.py          # Основной скрипт нагрузочного тестирования
│   ├── constants/                 # Конфигурационные константы
│   │   ├── __init__.py
│   │   ├── url_constants.py       # Endpoints API для разных окружений
│   │   ├── db_constants.py        # Параметры подключения к БД
│   │   └── map_constants.py       # Маппинг сценариев и таблиц
│   └── utils/                     # Вспомогательные модули
│       ├── __init__.py
│       ├── payload_utils.py       # Построение GraphQL запросов
│       ├── fetch_utils.py         # Получение тестовых данных из БД
│       ├── parse_utils.py         # Парсинг и обработка ответов
│       ├── encoder_utils.py       # Кодирование данных
│       └── secret_utils.py        # Работа с credentials и токенами
├── README.md
└── __init__.py
```

## Стек

| Компонент | Технология            | Назначение |
|-----------|-----------------------|-----------|
| **Framework** | Locust                | Open-source фреймворк для распределенного нагрузочного тестирования |
| **Язык** | Python 3.x            | Основной язык реализации |
| **API Protocol** | GraphQL               | Тестируемый протокол и тип API |
| **HTTP Client** | FastHttpUser (Locust) | Оптимизированный асинхронный HTTP клиент |
| **БД (источники данных)** | Cassandra, Dragonfly  | Получение тестовых данных (IMSI, MSISDN, GUID) |
| **Секреты** | Vault                 | Безопасное хранение credentials и токенов |

## Основные компоненты

### 1. **load_cp_online.py** — Основной сценарий нагрузочного теста

Центральный файл проекта, содержащий:

- **Парсинг аргументов командной строки**
  - `--scenario` — выбор сценария тестирования (full_data, fast_data, slow_data, mixed_sample, my_mts_info, mts_music, recsys и др.)
  - `--endpoint` — тип эндпоинта (privacy или public)
  - `--db-limit` — количество тестовых данных из БД (по умолчанию 1000)
  - `--api-env` — целевое окружение (dev1, test1, prep1, prod1, prod1_ip)

- **Инициализация тестового окружения** (обработчик `on_init`)
  - Загрузка credentials из Vault
  - Получение ключей (IMSI, MSISDN, GUID) из БД
  - Парсинг GraphQL схемы
  - Построение payload-ов для каждого сценария

- **Класс LoadTestingUser** (наследует FastHttpUser)
  - Определение задач (@task) для каждого сценария
  - Выполнение POST-запросов к GraphQL endpoint
  - Обработка ошибок и логирование

- **Логирование и обработка ошибок**
  - Запись ошибок в `error.log` (первые 100 ошибок)
  - Детальная информация о неудачных запросах (статус, body, response)

### 2. **Constants** — Конфигурационные параметры

#### `url_constants.py`
Хранит endpoints API для разных окружений:
```python
CP_ONLINE_DEV_PRIVACY = "https://dev-api.example.com/"
CP_ONLINE_TEST_PRIVACY = "https://test-api.example.com/"
CP_ONLINE_PREP_PRIVACY = "https://prep-api.example.com/"
CP_ONLINE_PROD_PRIVACY = "https://prod-api.example.com/"
CP_ONLINE_PROD_IP_PRIVACY = "https://prod-ip.example.com/"
# Аналогично для PUBLIC endpoints
```

#### `db_constants.py`
Параметры подключения к БД:
- Cassandra connection settings (hosts, port, keyspace)
- Dragonfly connection settings (host, port, credentials)
- Timeout и retry параметры

#### `map_constants.py`
Маппинги для сценариев:
- `SCENARIO_TABLES_MAP_PRIVACY / PUBLIC` — список таблиц для каждого сценария
- `SCENARIO_BODY_MAP_PRIVACY / PUBLIC` — спецификация полей для GraphQL запросов
- `TABLE_KEY_MAP` — маппинг таблиц на типы ключей (IMSI, MSISDN, GUID)

### 3. **Utils** — Вспомогательные модули

#### `fetch_utils.py`
Получение тестовых данных из баз данных:
- Подключение к Cassandra и Dragonfly
- Выполнение запросов SELECT для получения ключей
- Фильтрация данных по сценарию
- Кэширование результатов

#### `payload_utils.py`
Построение GraphQL запросов на основе ключей и схемы:
- Генерация GraphQL queries с переменными
- Форматирование JSON payload-ов
- Применение спецификаций полей из конфигурации
- Сериализация в bytes для отправки

#### `parse_utils.py`
Парсинг и обработка ответов от API:
- Извлечение данных из JSON ответов
- Валидация структуры ответов
- Преобразование форматов данных
- Обработка GraphQL ошибок

#### `encoder_utils.py`
Кастомный JSON энкодер для специфических типов данных:
- Сериализация нестандартных типов (datetime, UUID, etc.)
- Сохранение схемы в JSON файл
- Обработка сложных структур данных

#### `secret_utils.py`
Безопасная работа с credentials и токенами:
- Загрузка переменных окружения
- Получение credentials из Vault
- Управление токенами доступа к БД и API
- Обновление токенов при необходимости

## Параметры запуска

### --scenario
Выбор сценария тестирования:
- `full_data` — все доступные атрибуты из Cassandra и Dragonfly
- `fast_data` — только быстрые атрибуты из Dragonfly
- `slow_data` — только медленные атрибуты из Cassandra
- `mixed_sample` — смешанные атрибуты
- `my_mts_info` — атрибуты "Мой МТС"
- `my_mts_info_limit` — "Мой МТС" с лимитом
- `mts_music` — атрибуты "МТС Музыка"
- `mts_music_limit` — "МТС Музыка" с лимитом
- `recsys` — атрибуты для RecSys тестирования

### --endpoint
Тип эндпоинта:
- `privacy` — приватный эндпоинт (требует авторизации)
- `public` — публичный эндпоинт

### --db-limit
Количество записей для загрузки из БД (по умолчанию 1000):
```bash
--db-limit=5000  # Загрузить 5000 записей
```

### --api-env
Целевое окружение:
- `dev1` — разработка
- `test1` — тестирование
- `prep1` — препрод (по умолчанию)
- `prod1` — production
- `prod1_ip` — production IP (требует токена)

## Анализ результатов

После запуска теста Locust генерирует несколько файлов:

- **error.log** — детальный лог первых 100 ошибок с request/response body
- **fetched_keys.json** — загруженные ключи из БД
- **built_payloads.json** — сгенерированные GraphQL запросы
- **schema_metadata.json** — парсированная GraphQL схема
