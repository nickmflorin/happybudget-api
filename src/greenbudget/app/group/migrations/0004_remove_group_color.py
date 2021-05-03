from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0003_map_group_colors'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='color',
        ),
    ]
