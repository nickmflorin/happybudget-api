from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0013_order_by_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actual',
            options={'get_latest_by': 'order', 'ordering': ('order',), 'verbose_name': 'Actual', 'verbose_name_plural': 'Actual'},
        ),
    ]
