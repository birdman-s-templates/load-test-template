import logging
import json

from common.bindings.databases.dragonfly_db import Dragonfly
from common.bindings.databases.cassandra_db import Cassandra
from tests.load.locust.constants import map_constants
from tests.load.locust.utils import secret_utils, parse_utils


logger = logging.getLogger("locust")


def fetch_keys(scenario: str, db_limit: int, env: str, endpoint: str):
    keys_imsi = []
    keys_msisdn = []
    keys_guid = []

    # Получение данных для авторизации из Vault
    user, password, cassandra, dragonfly, token = secret_utils.get_vault_credentials(env=env, endpoint=endpoint)

    table_key_map = map_constants.TABLE_KEY_MAP
    if endpoint == "public":
        scenario_table_map = map_constants.SCENARIO_TABLES_MAP_PUBLIC[scenario]
    else:
        scenario_table_map = map_constants.SCENARIO_TABLES_MAP_PRIVACY[scenario]


    divider = len(scenario_table_map)

    try:
        for table in scenario_table_map:
            limit = db_limit // divider

            if table == "dragonfly":

                if endpoint == "public":
                    max_attempts = 5  # Лимит итераций, чтобы избежать бесконечного цикла
                    attempt = 0
                    current_limit = limit  # Стартовый limit, будем увеличивать
                    while not keys_guid and attempt < max_attempts:
                        attempt += 1
                        try:
                            with Dragonfly(host=dragonfly[0], port=dragonfly[1]) as db:
                                keys = db.get_all_keys(limit=current_limit)
                                msisdn_list, imsi_list, guid_list = parse_utils.parse_telecom_list(input_list=keys)
                                keys_guid.extend(guid_list)  # Только guid
                                logger.info(
                                    f"Dragonfly (public, попытка {attempt}): Извлечено {len(guid_list)} GUID (current limit={current_limit})")
                                # Увеличиваем limit для следующей итерации, если нужно
                                if not guid_list:
                                    current_limit *= 2  # Удваиваем для большего fetch
                        except Exception as e:
                            logger.error(f"Ошибка в Dragonfly при извлечении (public, попытка {attempt}): {e}", exc_info=True)
                            # Продолжаем цикл, но если max_attempts — raise ниже

                    if not keys_guid:
                        raise ValueError(
                            f"Не удалось извлечь непустой keys_guid для Dragonfly (public) после {max_attempts} попыток")

                elif endpoint == "privacy":
                    with Dragonfly(host=dragonfly[0], port=dragonfly[1]) as db:
                        keys = db.get_all_keys(limit=limit)
                        msisdn_list, imsi_list, guid_list = parse_utils.parse_telecom_list(input_list=keys)
                        keys_imsi.extend(imsi_list)
                        keys_msisdn.extend(msisdn_list)
                        keys_guid.extend(guid_list)
                        logger.info(
                            f"Dragonfly: Извлечено {len(imsi_list)} IMSI, {len(msisdn_list)} MSISDN, {len(guid_list)} GUID")

            else:
                try:
                    key_to_list = {
                        "imsi": keys_imsi,
                        "msisdn": keys_msisdn,
                        "guid": keys_guid,
                    }
                    current_key_name = table_key_map[table]

                    if current_key_name not in key_to_list:
                        raise ValueError(f"Неизвестный ключ '{current_key_name}' для таблицы '{table}'")

                    with Cassandra(
                            contact_points=cassandra[0],
                            port=cassandra[1],
                            local_dc=cassandra[2],
                            username=user,
                            password=password
                    ) as db:

                        rows = db.get_all_keys(table_name=table, limit=limit)
                        logger.info(f"Извлечено {len(rows)} строк из таблицы '{table}' (limit={limit})")

                        values = []
                        for row in rows:
                            if hasattr(row, current_key_name) or (isinstance(row, dict) and current_key_name in row):
                                value = getattr(row, current_key_name, None) if not isinstance(row, dict) else row.get(
                                    current_key_name)
                                if value is not None:  # Игнорируем None
                                    str_value = str(value)  # Преобразование в строку
                                    values.append(str_value)
                            else:
                                logger.warning(f"Ключ '{current_key_name}' не найден в cтроке: {row}")

                        key_to_list[current_key_name].extend(values)
                        logger.info(
                            f"{len(values)} значений извлечено для ключа '{current_key_name}' из {len(rows)} срок")

                except Exception as e:
                    logger.error(f"Ошибка при извлечении данных из Cassandra, таблица: '{table}': {e}", exc_info=True)
                    raise  # Propagate ошибку вверх (для краша в on_init)

    except Exception as e:
        logger.error(f"Ошибка в fetch_keys: {e}", exc_info=True)
        raise  # Raise, чтобы прервать, но finally выполнится

    finally:
        if not (keys_imsi or keys_msisdn or keys_guid):
            raise ValueError("Пустой результат в fetch_keys: нет ключей из БД")

    # Сохранение ключей в файл перед возвратом
    data_to_save = {
        "endpoint": endpoint,
        "scenario": scenario,
        "imsi": keys_imsi,
        "msisdn": keys_msisdn,
        "guid": keys_guid
    }
    try:
        with open("fetched_keys.json", "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=None, separators=(',', ':'))
        logger.info("Ключи успешно сохранены в fetched_keys.json")
    except Exception as e:
        logger.error("Ошибка сохранения ключей в файл", exc_info=True)

    return keys_imsi, keys_msisdn, keys_guid, token
