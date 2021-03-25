from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'base_manager_name': 'non_polymorphic', 'get_latest_by': 'created_at', 'ordering': ('-created_at',), 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AlterModelManagers(
            name='createevent',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='event',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='fieldalterationevent',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
    ]
