from django.db import migrations, models
import django.db.models.deletion

def convert_type_to_foreign_key(apps, schema_editor):
    Playground = apps.get_model('playgrounds', 'Playground')
    PlaygroundType = apps.get_model('playgrounds', 'PlaygroundType')
    
    # Словарь для сопоставления старых значений с новыми
    type_mapping = {
        'FOOTBALL': 'Футбол',
        'BASKETBALL': 'Баскетбол',
        'TENNIS': 'Теннис',
        'VOLLEYBALL': 'Волейбол',
        'OTHER': 'Другое'
    }
    
    for playground in Playground.objects.all():
        if playground.type:  # если тип был установлен
            new_type_name = type_mapping.get(playground.type)
            if new_type_name:
                new_type = PlaygroundType.objects.get(name=new_type_name)
                playground.type = new_type
                playground.save()

class Migration(migrations.Migration):
    dependencies = [
        ('playgrounds', '0007_add_initial_playground_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playground',
            name='type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='playgrounds',
                to='playgrounds.playgroundtype',
                verbose_name='Тип поля'
            ),
        ),
        migrations.RunPython(convert_type_to_foreign_key),
    ] 