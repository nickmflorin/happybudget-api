from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='createevent',
            options={'get_latest_by': 'created_at', 'ordering': ('created_at',), 'verbose_name': 'Create Event', 'verbose_name_plural': 'Create Events'},
        ),
        migrations.AlterModelOptions(
            name='event',
            options={'base_manager_name': 'non_polymorphic', 'get_latest_by': 'created_at', 'ordering': ('created_at',), 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AlterModelOptions(
            name='fieldalterationevent',
            options={'get_latest_by': 'created_at', 'ordering': ('created_at',), 'verbose_name': 'Field Alteration Event', 'verbose_name_plural': 'Field Alteration Events'},
        ),
    ]
