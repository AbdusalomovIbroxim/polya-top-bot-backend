from django.db import migrations

def add_initial_playground_types(apps, schema_editor):
    PlaygroundType = apps.get_model('playgrounds', 'PlaygroundType')
    types = [
        ('Футбол', 'Футбольное поле'),
        ('Баскетбол', 'Баскетбольная площадка'),
        ('Теннис', 'Теннисный корт'),
        ('Волейбол', 'Волейбольная площадка'),
        ('Другое', 'Другое игровое поле'),
    ]
    for name, description in types:
        PlaygroundType.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )

def remove_playground_types(apps, schema_editor):
    PlaygroundType = apps.get_model('playgrounds', 'PlaygroundType')
    PlaygroundType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('playgrounds', '0006_playground_latitude_playground_longitude'),
    ]

    operations = [
        migrations.RunPython(add_initial_playground_types, remove_playground_types),
    ] 