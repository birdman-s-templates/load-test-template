# Нагрузочный скрипт для CP Online (Locust)

Этот скрипт предназначен для нагрузочного тестирования API CP Online с использованием Locust на разных окружениях. Он поддерживает различные сценарии запросов к публичным и приватным эндпоинтам, извлекая данные из баз данных Cassandra и Dragonfly.

## Общее workflow скрипта

1. **Инициализация параметров**: Скрипт парсит аргументы командной строки (scenario, endpoint, db-limit, api-env) для настройки сценария, эндпоинта, лимита данных и окружения.

2. **Настройка окружения**: Устанавливаются хост, заголовки запросов. Из Vault извлекаются credentials. Загружаются ключи (IMSI, MSISDN, GUID) из баз данных в зависимости от сценария.

3. **Парсинг схемы**: Загружается и парсится GraphQL-схема из `released_schema.graphql`.

4. **Построение payloads**: На основе ключей и схемы генерируются GraphQL-запросы (payloads) для выбранного сценария.

5. **Выполнение задач**: Locust-юзеры выполняют POST-запросы к API с использованием цикличного итератора по payloads. Поддерживаются сценарии вроде full_data, slow_data, fast_data и другие.

6. **Логирование ошибок**: Ошибки запросов логируются в файл `error.log` (первые 10 ошибок с деталями).

Скрипт запускается через Locust, например: `locust -f load_cp_online.py --scenario=full_data --endpoint=privacy --db-limit=1000 --api-env=prep1`.

## Описание главного файла и служебных файлов

- **load_cp_online.py** (главный файл): Основной скрипт Locust. Определяет парсинг аргументов, инициализацию (fetch keys, parse schema, build payloads), класс юзера с задачами (@task) для каждого сценария. Обрабатывает запросы и ошибки.

- **constants/db_constants.py**: Содержит константы настройки БД (Cassandra, Dragonfly).
- **constants/map_constants.py**: Содержит константы для маппинга таблиц, сценариев, полей для запросов (SCENARIO_TABLES_MAP, SCENARIO_BODY_MAP и т.д.).
- **constants/url_constants.py**: Содержит константы для URL эндпоинтов.

- **utils/fetch_utils.py**: Функция для извлечения ключей (IMSI, MSISDN, GUID) из Cassandra и Dragonfly. Использует credentials из Vault, парсит результаты.
- **utils/payload_utils.py**: Строит GraphQL-payloads на основе ключей, схемы и спецификаций полей. Использует custom_query_builder из common.
- **utils/parse_utils.py**: Парсит списки ключей из формата 'key:value' в отдельные списки для IMSI, MSISDN, GUID.
- **utils/encoder_utils.py**: Кастомный JSON-энкодер для обработки специфических типов данных (например, для сохранения схемы).
- **utils/secret_utils.py**: Извлекает credentials и токены из Vault для доступа к БД и API.
- **schema.graphql**: Файл с GraphQL-схемой, используемый для генерации запросов.

- **__init__.py**: Пустой файл для обозначения пакета.

## Инструкция по добавлению нового сценария

Чтобы добавить новый сценарий (например, "new_scenario"):

1. **Обновите constants.py**:
   - Добавьте сценарий в SCENARIO_TABLES_MAP_PRIVACY и/или SCENARIO_TABLES_MAP_PUBLIC (список таблиц для извлечения ключей).
   - Добавьте в SCENARIO_BODY_MAP_PRIVACY и/или SCENARIO_BODY_MAP_PUBLIC спецификацию полей (fields_spec) для запросов (словарь с полями или {} для всех полей).
   - Если нужно, обновите TABLE_KEY_MAP или другие маппинги.

2. **Обновите init_parser в load_cp_online.py**:
   - Добавьте новый сценарий в choices для --scenario.

3. **Добавьте задачу в LoadTestingUser**:
   - Создайте метод @task(1), например:
     ```
     @task(1)
     def perform_request_new_scenario(self):
         self._execute_task("new_scenario", "perform_request_new_scenario")
     ```
   - Убедитесь, что _execute_task обрабатывает новый флаг.

4. **Обновите fetch_keys и build_payloads (если нужно, но такой нужды возникать не должно, ибо там универсализированный подход)**:
   - В fetch_utils.py добавьте логику для новых таблиц или ключей.
   - В payload_utils.py убедитесь, что сценарий обрабатывается в циклах по ключам.

5. **Тестирование**:
   - Запустите скрипт с новым сценарием: `locust -f load_cp_online.py --scenario=new_scenario ...`
   - Проверьте логи, error.log и сгенерированные файлы (fetched_keys.json, built_payloads.json, schema_metadata.json).

После добавления сценарий будет доступен для нагрузочного тестирования с автоматической генерацией запросов.