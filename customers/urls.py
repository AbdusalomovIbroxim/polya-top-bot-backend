from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAuthViewSet

router = DefaultRouter()
router.register(r'admin-panel', AdminAuthViewSet, basename='admin-auth')

urlpatterns = [
    path('', include(router.urls)),
]
