from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0012_order_non_null'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actual',
            options={'get_latest_by': 'updated_at', 'ordering': ('order',), 'verbose_name': 'Actual', 'verbose_name_plural': 'Actual'},
        ),
    ]
