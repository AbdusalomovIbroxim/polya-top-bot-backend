from django.db import models
from playgrounds.models import SportVenue

def remove_duplicates():
    duplicates = (
        SportVenue.objects
        .values("name", "address")
        .annotate(min_id=models.Min("id"), count_id=models.Count("id"))
        .filter(count_id__gt=1)
    )

    for dup in duplicates:
        SportVenue.objects.filter(
            name=dup["name"],
            address=dup["address"]
        ).exclude(id=dup["min_id"]).delete()

    print(f"Удалено {duplicates.count()} групп дубликатов")
