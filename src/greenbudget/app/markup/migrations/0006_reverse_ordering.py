from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0005_unit_required'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='markup',
            options={'get_latest_by': 'updated_at', 'ordering': ('created_at',), 'verbose_name': 'Markup', 'verbose_name_plural': 'Markups'},
        ),
    ]
