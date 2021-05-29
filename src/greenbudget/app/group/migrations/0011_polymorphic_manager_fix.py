from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0010_new_name_back_to_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'base_manager_name': 'non_polymorphic', 'get_latest_by': 'created_at', 'ordering': ('created_at',), 'verbose_name': 'Group', 'verbose_name_plural': 'Groups'},
        ),
        migrations.AlterModelManagers(
            name='group',
            managers=[
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
    ]
