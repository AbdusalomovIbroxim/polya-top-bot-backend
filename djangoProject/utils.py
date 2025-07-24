import hashlib
import hmac
import json
from operator import itemgetter
from urllib.parse import parse_qsl

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def csrf_exempt_api(view_class):
    """
    Decorator to exempt API views from CSRF protection
    """
    for method in ['dispatch']:
        setattr(view_class, method, csrf_exempt(getattr(view_class, method)))
    return view_class

def check_webapp_signature(token: str, init_data: str) -> bool:
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        print('[DEBUG] Ошибка парсинга init_data')
        return False
    if "hash" not in parsed_data:
        print('[DEBUG] hash не найден в init_data')
        return False
    hash_ = parsed_data.pop('hash')
    if 'signature' in parsed_data:
        parsed_data.pop('signature')
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hashlib.sha256(token.encode()).digest()
    calculated_hash = hmac.new(
        key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    secret_key2 = hmac.new(
        key=b'WebAppData',
        msg=token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    calculated_hash2 = hmac.new(
        key=secret_key2,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    calculated_hash3 = hmac.new(
        key=token.encode(),
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    # DEBUG PRINTS
    print('=== TELEGRAM SIGNATURE DEBUG ===')
    print('Token:', token[:4] + '...' + token[-4:])
    print('init_data:', init_data)
    print('hash:', hash_)
    print('data_check_string:', repr(data_check_string))
    print('calculated_hash:', calculated_hash)
    print('calculated_hash2:', calculated_hash2)
    print('calculated_hash3:', calculated_hash3)
    print('Match1:', calculated_hash == hash_)
    print('Match2:', calculated_hash2 == hash_)
    print('Match3:', calculated_hash3 == hash_)
    print('=== END DEBUG ===')
    return calculated_hash == hash_ or calculated_hash2 == hash_ or calculated_hash3 == hash_

def parse_telegram_init_data(init_data: str):
    try:
        parsed = dict(parse_qsl(init_data))
        user_json = parsed.get('user')
        if not user_json:
            return None
        user_data = json.loads(user_json)
        return user_data
    except Exception:
        return None