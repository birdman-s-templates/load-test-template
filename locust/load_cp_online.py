import logging
from logging.handlers import RotatingFileHandler
import json
from itertools import cycle
from locust import FastHttpUser, task, events
from locust.runners import STATE_STOPPING, STATE_STOPPED

from common.bindings.cp_online.graphql_schema_analyzer.gql_query_generator import parse_current_schema
from tests.load.locust.constants import url_constants
from tests.load.locust.utils.encoder_utils import CustomJSONEncoder
from tests.load.locust.utils.fetch_utils import fetch_keys
from tests.load.locust.utils.payload_utils import build_payloads


# Получаем логгер с именем 'locust', чтобы все логи писались в одном потоке
logger = logging.getLogger("locust")

# Настройка логгера только для файла (без консоли)
error_logger = logging.getLogger("locust_errors")
error_logger.setLevel(logging.ERROR)
error_logger.propagate = False  # Не передавать логи вверх (в root logger, чтобы не выводить в консоль)

# Handler для файла
error_handler = RotatingFileHandler("error.log", maxBytes=10*1024*1024, backupCount=5)  # 10MB, 5 backups
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
error_logger.addHandler(error_handler)

# Глобальные для sampling (можно сделать атрибутами класса, если нужно)
error_count = 0
MAX_ERRORS_TO_LOG = 100  # Лог только первых 10 ошибок


@events.init_command_line_parser.add_listener
def init_parser(parser):
    """
    Добавление кастомных параметров для запуска скрипта.
        - scenario (откуда получаем идентификаторы - slow_data / fast_data / full_data)
        - endpoint: public / privacy
        - db-limit (количество imsi, которое забираем целевых БД)
        - api-env (окружение, под которое запускаем скрипт)
    """
    parser.add_argument(
        "--scenario",
        type=str,
        choices=[
            "slow_data", "fast_data",
            "full_data", "mixed_sample",
            "my_mts_info", "my_mts_info_limit",
            "mts_music", "mts_music_limit",
            "recsys"
        ],
        default="full_data",
        help="Источник данных для идентификаторов: "
             "slow_data - атрибуты из Cassandra, "
             "fast_data атрибуты из Dragonfly, "
             "full_data - все атрибуты, "
             "mixed_sample - один атрибут slow_data и один из fast_data для privacy, для public - один атрибут slow_data, "
             "my_mts_info - атрибуты по Моему МТС"
             "my_mts_info_limit - атрибуты по Моему МТС (лимит: 1)"
             "mts_music - атрибуты по МТС Музыке"
             "mts_music_limit - атрибуты по МТС Музыке (лимит: 1)"
             "recsys - атрибуты, использовавшиеся RecSys при тестировании публичного эндпоинта"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        choices=["privacy", "public"],
        default="privacy",
        help="Целевой идентификатор: privacy, public"
    )
    parser.add_argument(
        "--db-limit",
        type=int,
        default=1000,
        help="Лимит записей, забираемых из БД для использования в запросах"
    )
    parser.add_argument(
        "--api-env",
        type=str,
        choices=["prep1", "dev1", "test1", "prod1", "prod1_ip"],
        default="prep1",
        help="Целевое окружение: prep1, dev1, test1, prod1 или prod1_ip"
    )


@events.init.add_listener
def on_init(environment, **kwargs):
    base = None
    environment.iters = {}

    try:
        opts = getattr(environment, "parsed_options", None) or {}
        environment.api_env = getattr(opts, "api_env")
        environment.scenario = getattr(opts, "scenario")
        environment.endpoint = getattr(opts, "endpoint")
        environment.headers = {
                "Content-Type": "application/json",
                "Connection": "keep-alive",
            }

        if environment.api_env == "test1":
            if environment.endpoint == "public":
                base = url_constants.CP_ONLINE_TEST_PUBLIC
            elif environment.endpoint == "privacy":
                base = url_constants.CP_ONLINE_TEST_PRIVACY

        elif environment.api_env == "dev1":
            if environment.endpoint == "public":
                base = url_constants.CP_ONLINE_DEV_PUBLIC
            elif environment.endpoint == "privacy":
                base = url_constants.CP_ONLINE_DEV_PRIVACY

        elif environment.api_env == "prep1":
            if environment.endpoint == "public":
                base = url_constants.CP_ONLINE_PREP_PUBLIC
            elif environment.endpoint == "privacy":
                base = url_constants.CP_ONLINE_PREP_PRIVACY

        elif environment.api_env == "prod1":
            if environment.endpoint == "public":
                base = url_constants.CP_ONLINE_PROD_PUBLIC
            elif environment.endpoint == "privacy":
                base = url_constants.CP_ONLINE_PROD_PRIVACY

        elif environment.api_env == "prod1_ip":
            if environment.endpoint == "public":
                base = url_constants.CP_ONLINE_PROD_IP_PUBLIC
            elif environment.endpoint == "privacy":
                base = url_constants.CP_ONLINE_PROD_IP_PRIVACY

        else:
            raise ValueError("Не передано корректное окружение")

        if base is None:
            raise ValueError("Не передано корректное окружение")

        if environment.api_env != "prod1_ip":
            environment.host = base + "query"
        else:
            environment.host = base

        # Загружаем payloads во все процессы
        keys_imsi, keys_msisdn, keys_guid, token = fetch_keys(
            scenario=environment.scenario,
            db_limit=getattr(opts, "db_limit"),
            env=environment.api_env,
            endpoint=environment.endpoint
        )

        # Финализируем заголовок, если нужен token (только для IP)
        if environment.api_env == "prod1_ip" and token:
            environment.headers['Authorization'] = f"Bearer {token}"
        if environment.api_env == "prod1_ip" and not token:
            raise ValueError("Не удалось получить токен для Integration Platform")

        # Загружаем схему
        environment.schema = parse_current_schema(is_release_schema=True)

        # Сохранение схемы в файл
        data_to_save = {
            "schema": environment.schema,
        }
        try:
            with open("schema_metadata.json", "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4, cls=CustomJSONEncoder)
            logger.info(f"Сохранена схема 'schema_metadata.json'")
        except Exception as e:
            logger.error(f"Ошибка при сохранении схемы в файл: {e}", exc_info=True)

        # Готовим payloads
        environment.payloads = build_payloads(
            keys_imsi=keys_imsi,
            keys_msisdn=keys_msisdn,
            keys_guid=keys_guid,
            scenario=environment.scenario,
            schema=environment.schema,
            endpoint=environment.endpoint
        )

        # Создаём итератор по целевому сценарию
        environment.iters[environment.scenario] = cycle(environment.payloads[environment.scenario])

    except Exception as e:
        logger.exception("Критическая ошибка в on_init — завершаем. error=%s", e)
        try:
            environment.process_exit_code = 42
            if getattr(environment, "runner", None):
                environment.runner.quit()
            events.quit.fire(exit_code=42)  # Locust event для полного shutdown с кодом
        except:
            pass
        import sys
        sys.exit(42)  # Финальный exit


class LoadTestingUser(FastHttpUser):
    wait_time = lambda self: 0

    def on_start(self):
        self._post = self.client.post
        self._host = self.environment.host

        # Проверка и fallback для headers
        if not hasattr(self.environment, 'headers'):
            logger.error("environment.headers not initialized — using default")
            self._headers = {
                "Content-Type": "application/json",
                "Connection": "keep-alive",
            }
        self._headers = self.environment.headers

        self.client.http2 = True
        self.client.verify = False

    @task(1)
    def perform_request_full_query(self):
        self._execute_task("full_data", "perform_request_full_data")

    @task(1)
    def perform_request_mixed_sample(self):
        self._execute_task("mixed_sample", "perform_request_mixed_sample")

    @task(1)
    def perform_request_slow_data(self):
        self._execute_task("slow_data", "perform_request_slow_data")

    @task(1)
    def perform_request_fast_data(self):
        self._execute_task("fast_data", "perform_request_fast_data")

    @task(1)
    def perform_request_my_mts_info(self):
        self._execute_task("my_mts_info", "perform_request_my_mts")

    @task(1)
    def perform_request_my_mts_info_limit(self):
        self._execute_task("my_mts_info_limit", "perform_request_my_mts_info_limit")

    @task(1)
    def perform_request_mts_music(self):
        self._execute_task("mts_music", "perform_request_mts_music")

    @task(1)
    def perform_request_mts_music_limit(self):
        self._execute_task("mts_music_limit", "perform_request_mts_music_limit")

    @task(1)
    def perform_request_recsys(self):
        self._execute_task("recsys", "perform_request_recsys")

    def _execute_task(self, flag, name):
        if self.environment.runner.state in [STATE_STOPPING, STATE_STOPPED]:
            return

        # безопасно получить iters (если атрибут не существует — получим пустой dict)
        iters = getattr(self.environment, "iters", {}) or {}
        if flag not in iters:
            # нет итератора для этого флага — пропускаем
            return

        # Получаем тело запроса из iterator, с обработкой ошибок
        try:
            body = next(iters[flag])
        except StopIteration:
            logger.warning("Итератор для %s пуст", flag)
            return
        except Exception as e:
            logger.exception("Ошибка при получении следующего payload из iters[%s]: %s", flag, e)
            return

        try:
            with self.client.post(
                    url=self._host,
                    headers=self._headers,
                    data=body,
                    name=name,
                    catch_response=True
            ) as resp:
                if resp.status_code != 200:
                    global error_count
                    if error_count < MAX_ERRORS_TO_LOG:
                        body_str = body.decode('utf-8') if isinstance(body, bytes) else str(body)
                        error_details = {
                            "task": name,
                            "status": resp.status_code,
                            "response_body": resp.text,
                            "request_body": body_str
                        }
                        error_logger.error(json.dumps(error_details))  # Лог только в файл errors.log
                        error_count += 1
                    resp.failure(f"Status: {resp.status_code}")
        except Exception as e:
            # Логируем исключение тоже только в файл (без консоли)
            error_logger.exception("Исключение при выполнении запроса %s: %s", name, e)
