import hashlib
import hmac
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
    """
    Check incoming WebApp init data signature (Telegram official way)
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        return False
    if "hash" not in parsed_data:
        return False

    hash_ = parsed_data.pop('hash')
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    # Ключ — SHA256(token)
    secret_key = hashlib.sha256(token.encode()).digest()
    calculated_hash = hmac.new(
        key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return calculated_hash == hash_ 