import hmac
import hashlib
import json
from urllib.parse import parse_qs

def check_telegram_auth(init_data: str, bot_token: str):
    try:
        parsed = parse_qs(init_data)
        data_dict = {k: v[0] for k, v in parsed.items()}

        hash_value = data_dict.pop("hash", None)
        if not hash_value:
            return None

        data_check_string = "\n".join(
            [f"{k}={v}" for k, v in sorted(data_dict.items())]
        )

        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_string = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if hmac_string != hash_value:
            return None

        # только теперь парсим user
        if "user" in data_dict:
            data_dict["user"] = json.loads(data_dict["user"])

        return data_dict
    except Exception as e:
        print("Ошибка при разборе initData:", e)
        return None
