from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import SportField
from decimal import Decimal

class SportFieldModelTests(TestCase):
    def setUp(self):
        self.field_data = {
            'name': 'Тестовое поле',
            'sport_type': 'football',
            'description': 'Тестовое описание',
            'address': 'Тестовый адрес',
            'region': 'Москва',
            'district': 'Центральный',
            'price_per_hour': Decimal('1000.00'),
            'is_indoor': False,
            'rating': 4.5
        }
        self.field = SportField.objects.create(**self.field_data)

    def test_field_creation(self):
        self.assertEqual(self.field.name, 'Тестовое поле')
        self.assertEqual(self.field.sport_type, 'football')
        self.assertEqual(str(self.field), 'Тестовое поле (Футбольное поле)')

    def test_field_update(self):
        self.field.name = 'Обновленное поле'
        self.field.save()
        updated_field = SportField.objects.get(id=self.field.id)
        self.assertEqual(updated_field.name, 'Обновленное поле')

class SportFieldAPITests(APITestCase):
    def setUp(self):
        self.field_data = {
            'name': 'API Тестовое поле',
            'sport_type': 'basketball',
            'description': 'API Тестовое описание',
            'address': 'API Тестовый адрес',
            'region': 'Санкт-Петербург',
            'district': 'Василеостровский',
            'price_per_hour': '1500.00',
            'is_indoor': True,
            'rating': 4.0
        }
        self.field = SportField.objects.create(**self.field_data)
        self.list_url = '/api/fields/'
        self.detail_url = f'/api/fields/{self.field.id}/'

    def test_get_fields_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_field_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'API Тестовое поле')

    def test_create_field(self):
        new_field_data = {
            'name': 'Новое поле',
            'sport_type': 'volleyball',
            'description': 'Новое описание',
            'address': 'Новый адрес',
            'region': 'Казань',
            'price_per_hour': '2000.00',
            'is_indoor': False
        }
        response = self.client.post(self.list_url, new_field_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SportField.objects.count(), 2)

    def test_update_field(self):
        update_data = {'name': 'Обновленное API поле'}
        response = self.client.patch(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.field.refresh_from_db()
        self.assertEqual(self.field.name, 'Обновленное API поле')

    def test_delete_field(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SportField.objects.count(), 0)

    def test_filter_by_region(self):
        response = self.client.get(f'{self.list_url}?region=Санкт-Петербург')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_by_sport_type(self):
        response = self.client.get(f'{self.list_url}?sport_type=basketball')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_by_name(self):
        response = self.client.get(f'{self.list_url}?search=API')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
