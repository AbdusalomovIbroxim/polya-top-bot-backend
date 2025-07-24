import hashlib
import hmac
import json
from operator import itemgetter
from urllib.parse import parse_qsl

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def csrf_exempt_api(view_class):
    for method in ['dispatch']:
        setattr(view_class, method, csrf_exempt(getattr(view_class, method)))
    return view_class

def check_webapp_signature(token: str, init_data: str) -> bool:
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return False
    hash_ = data.pop('hash', None)
    if not hash_:
        return False
    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(token.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return calculated_hash == hash_

def parse_telegram_init_data(init_data: str):
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        user_json = parsed.get('user')
        if not user_json:
            return None
        user_data = json.loads(user_json)
        return user_data
    except Exception:
        return None