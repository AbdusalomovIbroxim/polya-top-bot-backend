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
        print("RAW initData:", init_data)

        parsed = parse_qs(init_data)
        print("PARSED:", parsed)

        data_dict = {k: v[0] for k, v in parsed.items()}

        # Достаём hash и убираем лишнее
        hash_value = data_dict.pop("hash", None)
        data_dict.pop("signature", None)   # ⚡️ критично — не должно участвовать
        print("DATA_DICT (без hash и signature):", data_dict)
        print("HASH из initData:", hash_value)

        if not hash_value:
            print("❌ Hash отсутствует")
            return None

        # Формируем data_check_string (ключи отсортированы по алфавиту)
        data_check_string = "\n".join(
            [f"{k}={v}" for k, v in sorted(data_dict.items())]
        )
        print("DATA_CHECK_STRING:", data_check_string)

        # Проверка подписи
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_string = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        print("HMAC вычисленный:", hmac_string)

        if hmac_string != hash_value:
            print("❌ Подписи не совпадают!")
            return None

        # Парсим user
        if "user" in data_dict:
            data_dict["user"] = json.loads(data_dict["user"])

        print("✅ Проверка успешна, данные:", data_dict)
        return data_dict

    except Exception as e:
        print("Ошибка при разборе initData:", e)
        return None
