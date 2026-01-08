import logging


# Получаем логгер с именем 'locust', чтобы все логи писались в одном потоке
logger = logging.getLogger("locust")


def parse_telecom_list(input_list):
    """
    Разбивает список строк вида ['key:value', ...] на три списка: msisdn_list, imsi_list, guid_list.
    """
    msisdn_list = []
    imsi_list = []
    guid_list = []

    for item in input_list:
        item = item.strip().replace("'", "").replace('"', '')
        if ':' in item:
            key, value = item.split(':', 1)
            key = key.strip().lower()
            value = value.strip()

            if key == 'msisdn':
                msisdn_list.append(value)
            elif key == 'imsi':
                imsi_list.append(value)
            elif key == 'guid':
                guid_list.append(value)

    return msisdn_list, imsi_list, guid_list
