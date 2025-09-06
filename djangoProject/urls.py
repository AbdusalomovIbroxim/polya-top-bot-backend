from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve   
from djangoProject.settings import BASE_DIR
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from playgrounds.views import welcome, custom_page_not_found_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
import os

schema_view = get_schema_view(
    openapi.Info(
        title="Playground Booking API",
        default_version='v1',
        description="API для системы бронирования игровых полей",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(name="Telegram ->", url="https://t.me/ibr6xim")
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url="https://polya.top/api",  # Your API base URL
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('playgrounds.urls')),
    path('api/', include('bookings.urls')),
    path('api/', include('customers.urls')),
    path('', welcome, name='welcome'),

    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^robots\.txt$', serve, {
        'path': "robots.txt", 
        'document_root': os.path.join(BASE_DIR, "static")
    }),
    re_path(r'^sitemap\.xml$', serve, {
        'path': "sitemap.xml", 
        'document_root': os.path.join(BASE_DIR, "static")
    }),

]


handler404 = custom_page_not_found_view

