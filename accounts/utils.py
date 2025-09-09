import hmac
import hashlib
from urllib.parse import parse_qsl

def check_telegram_auth(init_data: str, bot_token: str, debug: bool = True):
    """
    Проверка корректности initData от Telegram WebApp.
    Возвращает dict с данными пользователя или None.
    """
    try:
        if debug:
            print("\n[TelegramAuth] RAW init_data:", init_data)

        # Парсим initData (сохраняем оригинальные значения, не трогаем экранирование)
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        if debug:
            print("[TelegramAuth] Parsed dict:", parsed)

        hash_value = parsed.pop("hash", None)
        if not hash_value:
            if debug:
                print("[TelegramAuth] ❌ Hash отсутствует")
            return None

        # Формируем data_check_string
        data_check_string = "\n".join(
            [f"{k}={v}" for k, v in sorted(parsed.items())]
        )
        if debug:
            print("[TelegramAuth] Data check string:\n", data_check_string)

        # SHA256(bot_token)
        secret_key = hashlib.sha256(bot_token.encode()).digest()

        # HMAC-SHA256
        hmac_string = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if debug:
            print("[TelegramAuth] HMAC (calculated):", hmac_string)
            print("[TelegramAuth] Hash (from initData):", hash_value)

        # Проверяем подпись
        if not hmac.compare_digest(hmac_string, hash_value):
            if debug:
                print("[TelegramAuth] ❌ Подпись не совпала")
            return None

        if debug:
            print("[TelegramAuth] ✅ Проверка успешна!")

        return parsed
    except Exception as e:
        if debug:
            print("[TelegramAuth] ⚠️ Ошибка:", str(e))
        return None
