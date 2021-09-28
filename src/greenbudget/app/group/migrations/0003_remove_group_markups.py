from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0002_add_relations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='markups',
        ),
    ]
