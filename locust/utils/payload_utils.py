import json
import logging

from common.bindings.cp_online.cp_online import custom_query_builder
from tests.load.locust.constants import map_constants


# Получаем логгер с именем 'locust', чтобы все логи писались в одном потоке
logger = logging.getLogger("locust")


def build_payloads(keys_imsi, keys_msisdn, keys_guid, scenario, schema, endpoint):
    """

    """
    payloads = {
        scenario: [],
    }

    if endpoint == "public":
        fields_spec = map_constants.SCENARIO_BODY_MAP_PUBLIC[scenario]
        scenario_table_map = map_constants.SCENARIO_TABLES_MAP_PUBLIC[scenario]

    else:
        fields_spec = map_constants.SCENARIO_BODY_MAP_PRIVACY[scenario]
        scenario_table_map = map_constants.SCENARIO_TABLES_MAP_PRIVACY[scenario]

    is_all_fields = True if fields_spec == {} else False

    if "dragonfly" in scenario_table_map:
        for imsi in keys_imsi:
            query, vars = custom_query_builder(
                key="imsi",
                key_value=imsi,
                schema_metadata=schema,
                fields_spec=fields_spec,
                is_all_fields=is_all_fields,
            )
            body = json.dumps({"query": query, "variables": vars}).encode("utf-8")
            payloads[scenario].append(body)

        for msisdn in keys_msisdn:
            query, vars = custom_query_builder(
                key="msisdn",
                key_value=msisdn,
                schema_metadata=schema,
                fields_spec=fields_spec,
                is_all_fields=is_all_fields,
            )
            body = json.dumps({"query": query, "variables": vars}).encode("utf-8")
            payloads[scenario].append(body)

        for guid in keys_guid:
            query, vars = custom_query_builder(
                key="guid",
                key_value=guid,
                schema_metadata=schema,
                fields_spec=fields_spec,
                is_all_fields=is_all_fields,
            )
            body = json.dumps({"query": query, "variables": vars}).encode("utf-8")
            payloads[scenario].append(body)

    # Cassandra
    else:

        used_keys = []

        for table in scenario_table_map:

            key = map_constants.TABLE_KEY_MAP[table]

            if key in used_keys:
                continue

            used_keys.append(key)

            if key == "imsi":
                target_id = keys_imsi
            elif key == "msisdn":
                target_id = keys_msisdn
            elif key == "guid":
                target_id = keys_guid
            else:
                raise ValueError("Не удалось смэтчить key")

            for id in target_id:
                query, vars = custom_query_builder(
                    key=key,
                    key_value=id,
                    schema_metadata=schema,
                    fields_spec=fields_spec,
                    is_all_fields=is_all_fields,
                )
                body = json.dumps({"query": query, "variables": vars}).encode("utf-8")
                payloads[scenario].append(body)

    if not payloads[scenario]:
        raise ValueError("Пустой payloads")

    # Сохранение payloads в минимизированный JSON-файл перед возвратом
    data_to_save = {
        scenario: [body.decode("utf-8") for body in payloads[scenario]]
    }
    try:
        with open("built_payloads.json", "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=None, separators=(',', ':'))
        logger.info("Payloads успешно сохранены в built_payloads.json")
    except Exception as e:
        logger.error("Ошибка сохранения payloads в файл", exc_info=True)

    return payloads
