import logging

from common.bindings.vault_for_ci import Vault
from common.configs.vault_config import VaultCorp
from tests.load.locust.constants import db_constants


# Получаем логгер с именем 'locust', чтобы все логи писались в одном потоке
logger = logging.getLogger("locust")


def get_vault_credentials(env, endpoint):
    """
    Получение учетных данных из Vault и сохранение их в глобальное состояние.
    """
    vault = Vault()
    token = None

    try:
        if env == "prep1":
            user = vault.get_secret_value(
                path=VaultCorp.sa0000datariverprep,
                key="user"
            )
            password = vault.get_secret_value(
                path=VaultCorp.sa0000datariverprep,
                key="pass"
            )
            cassandra = db_constants.CASSANDRA_PREP
            dragonfly = db_constants.DRAGONFLY_PREP

        elif env == "dev1":
            user = vault.get_secret_value(
                path=VaultCorp.sa0000datariveradmin,
                key="user"
            )
            password = vault.get_secret_value(
                path=VaultCorp.sa0000datariveradmin,
                key="pass"
            )
            cassandra = db_constants.CASSANDRA_DEV
            dragonfly = db_constants.DRAGONFLY_DEV

        elif env == "test1":
            user = vault.get_secret_value(
                path=VaultCorp.sa0000datarivertest,
                key="user"
            )
            password = vault.get_secret_value(
                path=VaultCorp.sa0000datarivertest,
                key="pass"
            )
            cassandra = db_constants.CASSANDRA_TEST
            dragonfly = db_constants.DRAGONFLY_TEST

        elif "prod1" in env:
            user = vault.get_secret_value(
                path=VaultCorp.sa0000datariverprod,
                key="user"
            )
            password = vault.get_secret_value(
                path=VaultCorp.sa0000datariverprod,
                key="pass"
            )
            cassandra = db_constants.CASSANDRA_PROD
            dragonfly = db_constants.DRAGONFLY_PROD

            if env == "prod1_ip":
                if endpoint == "privacy":
                    token = Vault().get_secret_value(path=VaultCorp.api_ip_cp_api, key="token")
                elif endpoint == "public":
                    token = Vault().get_secret_value(path=VaultCorp.api_ip_cp_api_public, key="token")
                else:
                    raise ValueError("Передан некорректный эндпоинт. Доступны: privacy, public")

        else:
            raise ValueError("Задано некорректное окружение. Доступные варианты: prep1, dev1, test1, prod1 или prod1_ip")

    except Exception as e:
        logger.error("Ошибка получения учетных данных из Vault", exc_info=True)
        raise

    # Сохранение в файл перед возвратом (маскируем sensitive данные)
    # data_to_save = {
    #     "user": user,
    #     "password": "not empty" if password and isinstance(password, str) and password.strip() else ("empty" if password == "" else "None"),
    #     "cassandra": cassandra,
    #     "dragonfly": dragonfly,
    #     "token": "not empty" if token and isinstance(token, str) and token.strip() else ("empty" if token == "" else "None")
    # }
    # try:
    #     with open("vault_data.json", "w", encoding="utf-8") as f:
    #         json.dump(data_to_save, f, ensure_ascii=False, indent=None, separators=(',', ':'))
    #     logger.info(f"Данные из Vault успешно сохранены в vault_data.json")
    # except Exception as e:
    #     logger.error("Ошибка сохранения Vault credentials в файл", exc_info=True)

    return user, password, cassandra, dragonfly, token
