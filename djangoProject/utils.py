from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def csrf_exempt_api(view_class):
    """
    Decorator to exempt API views from CSRF protection
    """
    for method in ['dispatch']:
        setattr(view_class, method, csrf_exempt(getattr(view_class, method)))
    return view_class 