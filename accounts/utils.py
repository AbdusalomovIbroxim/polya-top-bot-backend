import hmac
import hashlib
import json
from urllib.parse import parse_qs

def check_telegram_auth(init_data: str, bot_token: str):
    """
    Проверка корректности initData от Telegram WebApp.
    Возвращает dict с данными пользователя или None.
    """
    try:
        parsed = parse_qs(init_data)
        data_dict = {k: v[0] for k, v in parsed.items()}

        # Достаём hash и убираем лишнее
        hash_value = data_dict.pop("hash", None)
        data_dict.pop("signature", None)   # ⚡️ критично — не должно участвовать

        if not hash_value:
            return None

        # Формируем data_check_string (ключи отсортированы по алфавиту)
        data_check_string = "\n".join(
            [f"{k}={v}" for k, v in sorted(data_dict.items())]
        )

        # Проверка подписи
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_string = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if hmac_string != hash_value:
            return None

        # Парсим user
        if "user" in data_dict:
            data_dict["user"] = json.loads(data_dict["user"])

        return data_dict
    except Exception as e:
        print("Ошибка при разборе initData:", e)
        return None
