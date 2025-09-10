import hmac
import hashlib
import json
from urllib.parse import parse_qs, unquote_plus
import logging

logger = logging.getLogger(__name__)

def check_telegram_auth(init_data: str, bot_token: str):
    """
    Проверка initData от Telegram WebApp.
    Возвращает распарсенный dict или None.
    """
    try:
        logger.info("=== TELEGRAM AUTH DEBUG ===")
        logger.info("RAW initData: %s", init_data)
        logger.info("Bot token exists: %s", bool(bot_token))
        
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN не установлен!")
            return None

        # parse_qs раскодирует %-encoding
        parsed = parse_qs(init_data, strict_parsing=True, keep_blank_values=True)
        logger.info("Parsed data: %s", parsed)
        
        # получаем словарь ключ->значение (берём первый элемент из списка)
        data = {k: v[0] for k, v in parsed.items()}
        logger.info("Data dict: %s", data)

        # достаём hash и удаляем его из данных
        hash_value = data.pop("hash", None)
        data.pop("signature", None)  # удаляем signature если есть

        if not hash_value:
            logger.warning("initData не содержит hash")
            return None

        # Проверка времени жизни данных
        if "auth_date" in data:
            import time
            auth_date = int(data["auth_date"])
            current_time = int(time.time())
            age = current_time - auth_date
            
            logger.info("auth_date: %s, current_time: %s, age: %s seconds", 
                       auth_date, current_time, age)
            
            if age > 86400:  # 24 часа
                logger.warning("initData устарела: возраст %s секунд", age)
                return None

        # Формируем data_check_string: ключи в лексикографическом порядке
        data_check_pairs = []
        for key in sorted(data.keys()):
            data_check_pairs.append(f"{key}={data[key]}")
        data_check_string = "\n".join(data_check_pairs)

        logger.info("DATA_CHECK_STRING:\n%s", data_check_string)

        # секретный ключ = SHA-256(bot_token)
        secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
        hmac_obj = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256)
        hmac_hex = hmac_obj.hexdigest()

        logger.info("Calculated HMAC: %s", hmac_hex)
        logger.info("Hash from initData: %s", hash_value)

        # сравниваем безопасно
        if not hmac.compare_digest(hmac_hex, hash_value):
            logger.warning("Подпись не совпадает!")
            logger.warning("Expected: %s", hmac_hex)
            logger.warning("Received: %s", hash_value)
            return None

        logger.info("✅ Подпись совпадает! Аутентификация успешна.")

        # распарсим user JSON если есть
        if "user" in data:
            try:
                data["user"] = json.loads(data["user"])
                logger.info("User data parsed: %s", data["user"])
            except Exception as e:
                logger.exception("Не удалось распарсить user JSON: %s", str(e))

        logger.info("=== END TELEGRAM AUTH DEBUG ===")
        return data

    except Exception as e:
        logger.exception("Ошибка в check_telegram_auth: %s", str(e))
        return None