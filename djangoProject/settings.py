from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(".env_dev")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = int(os.getenv('DEBUG', 0)) == 1
print(f"DEBUG is set to: {DEBUG}")

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
if DEBUG:
    ALLOWED_HOSTS = ['*'] # Разрешить все хосты в режиме отладки


INSTALLED_APPS = [
    'unfold', 
    "unfold.contrib.filters",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'drf_yasg',
    'django_filters',
    'accounts.apps.AccountsConfig',
    'playgrounds.apps.PlaygroundsConfig',
    'bookings.apps.BookingsConfig',
    'customers.apps.CustomersConfig',
    
    # вспомогательные
    'django_admin_listfilter_dropdown',
]

MIDDLEWARE = [
    # 'djangoProject.middleware.RequestTimingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'unfold.context_processors.theme',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangoProject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        }
    }
    
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'polya_top_bot_database_vcvj',
#         'USER': 'polya_top_bot_database_vcvj_user',
#         'PASSWORD': 'pzOgYhcI2TKAnZgYI4Ttzu3piRxrVfaM',
#         'HOST': 'dpg-d1t2gs3e5dus73e37d80-a.oregon-postgres.render.com',
#         'PORT': '5432',
#         'OPTIONS': {
#             'sslmode': 'require',
#         },
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'


USE_TZ = True
TIME_ZONE = "Asia/Tashkent"


from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ('ru', _('Русский')),
    ('uz', _('O‘zbekcha')),
    ('en', _('English')),
]

USE_I18N = True

LOCALE_PATHS = [BASE_DIR / 'locale/']



STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    # "EXCEPTION_HANDLER": "djangoProject.exception_handler.custom_exception_handler",
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_ORDERING': ['-created_at'],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'patch',
        'delete',
    ],
    'DEFAULT_AUTO_SCHEMA_CLASS': 'drf_yasg.inspectors.SwaggerAutoSchema',
    'DEFAULT_SCHEMA_CLASS': 'drf_yasg.openapi.SwaggerSchema',
    'USE_SESSION_AUTH': False,
}


# --- Настройки безопасности (HTTPS) ---
# В режиме разработки (DEBUG=True) отключаем принудительный HTTPS
if DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'http')
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    # В продакшене (DEBUG=False) включаем принудительный HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Настройки CORS и CSRF (ВРЕМЕННОЕ РЕШЕНИЕ ДЛЯ ТЕСТИРОВАНИЯ) ---
# Читаем список разрешенных доменов из переменной окружения
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')

# 1. CORS_ALLOWED_ORIGINS
# Список доменов, которым разрешен кросс-доменный доступ.
# Используется 'corsheaders'.
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

# 2. CSRF_TRUSTED_ORIGINS (Решает проблему с VERIFY_CSRF_TOKEN)
# Домены, которым доверяет Django для получения CSRF токена.
# Добавляем конечный слэш для надежности.
CSRF_TRUSTED_ORIGINS = [
    f'{origin.strip()}/' 
    for origin in ALLOWED_ORIGINS 
    if origin.strip() and not origin.strip().endswith('/')
]

# Добавляем те, что уже есть, если они не заканчиваются слэшем 
CSRF_TRUSTED_ORIGINS.extend(
    [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip().endswith('/')]
)

# 3. Настройка для Web App (если Web App отправляет запросы из Telegram)
# Если ваш клиент Web App установлен в Telegram, вам может потребоваться разрешить
# поддомен telegram.org
# CORS_ALLOWED_ORIGIN_REGEXES = [
#    r"^https://.*\.telegram\.org$",
# ]



STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv('WEBAPP_URL')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    auto_session_tracking=False,
    traces_sample_rate=0
)


UNFOLD = {
    "SITE_TITLE": "PolyaTop Admin",
    "SITE_HEADER": "PolyaTop Панель управления",
    "SITE_SUBHEADER": "Статистика и управление",
    "SHOW_HISTORY": False,
    "SHOW_VIEW_ON_SITE": False,
    "DARK_MODE": True,
    "SIDEBAR_COLLAPSED": True,  # 👉 сворачивает боковую панель по умолчанию
    "MOBILE_MENU": True,        # 👉 включает мобильное меню (важно!)
    "CUSTOM_CSS": ["unfold_custom.css"],
    "DASHBOARD_CALLBACK": "accounts.admin_dashboard.dashboard_view",
}
