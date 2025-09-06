import pytest
from django.contrib.auth import get_user_model
from playgrounds.models import SportVenue, SportVenueType, Region, FavoriteSportVenue

User = get_user_model()

@pytest.mark.django_db
def test_create_sport_venue():
    region = Region.objects.create(name='Ташкент')
    venue_type = SportVenueType.objects.create(name='Футбол')
    user = User.objects.create_user(username='owner', password='pass123')
    venue = SportVenue.objects.create(
        name='Центральный стадион',
        description='Главный стадион',
        price_per_hour=1000,
        deposit_amount=500,
        city='Ташкент',
        address='ул. Центральная, 1',
        sport_venue_type=venue_type,
        region=region,
        owner=user
    )
    assert venue.name == 'Центральный стадион'
    assert venue.region.name == 'Ташкент'
    assert venue.owner.username == 'owner'

@pytest.mark.django_db
def test_add_favorite():
    user = User.objects.create_user(username='user1', password='pass123')
    region = Region.objects.create(name='Ташкент')
    venue_type = SportVenueType.objects.create(name='Футбол')
    venue = SportVenue.objects.create(
        name='Центральный стадион',
        description='Главный стадион',
        price_per_hour=1000,
        deposit_amount=500,
        city='Ташкент',
        address='ул. Центральная, 1',
        sport_venue_type=venue_type,
        region=region,
        owner=user
    )
    favorite = FavoriteSportVenue.objects.create(user=user, sport_venue=venue)
    assert favorite.user == user
    assert favorite.sport_venue == venue

@pytest.mark.django_db
def test_unique_favorite_constraint():
    user = User.objects.create_user(username='user2', password='pass123')
    region = Region.objects.create(name='Самарканд')
    venue_type = SportVenueType.objects.create(name='Футбол')
    venue = SportVenue.objects.create(
        name='Стадион Самарканд',
        description='Главный стадион',
        price_per_hour=800,
        deposit_amount=400,
        city='Самарканд',
        address='ул. Ленина, 5',
        sport_venue_type=venue_type,
        region=region,
        owner=user
    )
    FavoriteSportVenue.objects.create(user=user, sport_venue=venue)
    with pytest.raises(Exception):
        # Попытка добавить повторно
        FavoriteSportVenue.objects.create(user=user, sport_venue=venue)
