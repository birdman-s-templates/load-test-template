import json


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom encoder для сериализации неподдерживаемых типов в JSON.
    - Объекты: Конвертирует в dict (vars(obj) или __dict__).
    - Sets: В list.
    - Другие: str(obj) или default.
    """
    def default(self, obj):
        if hasattr(obj, '__dict__'):  # Для custom объектов
            return vars(obj)  # Или obj.__dict__ если нет vars
        elif isinstance(obj, set):
            return list(obj)  # Sets в lists
        elif isinstance(obj, (bytes, bytearray)):
            return obj.decode('utf-8')  # Bytes в str
        elif hasattr(obj, '__str__'):
            return str(obj)  # Fallback: str
        return super().default(obj)  # Стандартный encoder