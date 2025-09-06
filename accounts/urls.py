from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AuthViewSet, FootballChoicesView, FootballExperienceView, FootballFrequencyView, FootballPositionView, FootballFormatView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
    
    # Один эндпоинт для всех выборов
    path('auth/football-choices/', FootballChoicesView.as_view(), name='football-choices'),

    # Отдельные эндпоинты
    path('auth/football-experience/', FootballExperienceView.as_view(), name='football-experience'),
    path('auth/football-frequency/', FootballFrequencyView.as_view(), name='football-frequency'),
    path('auth/football-position/', FootballPositionView.as_view(), name='football-position'),
    path('auth/football-format/', FootballFormatView.as_view(), name='football-format'),
]
