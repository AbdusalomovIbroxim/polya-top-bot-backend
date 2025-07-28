from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer
from djangoProject.utils import csrf_exempt_api


@csrf_exempt_api
class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Авторизация пользователя по логину (username/телефон) и паролю",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'login': openapi.Schema(type=openapi.TYPE_STRING, description='Логин (username или телефон)'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль')
            },
            required=['login', 'password']
        ),
        responses={
            200: "Успешная авторизация",
            400: "Ошибка валидации"
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            login = serializer.validated_data['login']
            password = serializer.validated_data['password']

            # Пытаемся найти пользователя по username или телефону
            try:
                if '@' in login:
                    user = User.objects.get(email=login)
                else:
                    user = User.objects.get(username=login)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Пользователь не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверяем пароль
            if not user.check_password(password):
                return Response(
                    {'error': 'Неверный пароль'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Создаем токены
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Авторизуем пользователя
            login(request, user)

            return Response({
                'message': 'Успешная авторизация',
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Ошибка валидации данных'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Телефон')
            },
            required=['username', 'email', 'password']
        ),
        responses={
            201: "Пользователь создан",
            400: "Ошибка валидации"
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'message': 'Пользователь успешно создан',
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Ошибка валидации данных'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Выход из системы",
        responses={
            200: "Успешный выход"
        }
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'message': 'Успешный выход'})


@csrf_exempt_api
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()

    @swagger_auto_schema(
        operation_description="Получить информацию о текущем пользователе",
        responses={
            200: "Информация о пользователе"
        },
        methods=['get']
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Обновить информацию о текущем пользователе",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Телефон'),
                'photo': openapi.Schema(type=openapi.TYPE_FILE, description='Фото профиля')
            }
        ),
        responses={
            200: "Информация обновлена",
            400: "Ошибка валидации"
        },
        methods=['put', 'patch']
    )
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Ошибка валидации данных'},
                status=status.HTTP_400_BAD_REQUEST
            )
