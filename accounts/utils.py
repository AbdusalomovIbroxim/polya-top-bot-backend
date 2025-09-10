import hmac
import hashlib
import json
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)

def check_telegram_auth(init_data: str, bot_token: str):
    try:
        logger.error(f"RAW initData: {init_data}")

        parsed = parse_qs(init_data, strict_parsing=True)
        data_dict = {k: v[0] for k, v in parsed.items()}

        # достаем hash
        hash_value = data_dict.pop("hash", None)
        if not hash_value:
            logger.error("❌ Hash отсутствует")
            return None

        # готовим data_check_string
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(data_dict.items())
        )

        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_string = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        logger.error(f"DATA_CHECK_STRING: {data_check_string}")
        logger.error(f"HASH (из initData): {hash_value}")
        logger.error(f"HMAC (вычисленный): {hmac_string}")

        if hmac_string != hash_value:
            logger.error("❌ Подписи не совпадают!")
            return None

        if "user" in data_dict:
            data_dict["user"] = json.loads(data_dict["user"])

        logger.error(f"✅ Проверка успешна: {data_dict}")
        return data_dict

    except Exception as e:
        logger.error(f"Ошибка при разборе initData: {e}")
        return None
