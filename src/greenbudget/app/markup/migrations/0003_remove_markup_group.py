from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0002_add_relations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='markup',
            name='group',
        ),
    ]
