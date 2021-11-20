from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0006_order_non_null'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fringe',
            options={'get_latest_by': 'updated_at', 'ordering': ('order',), 'verbose_name': 'Fringe', 'verbose_name_plural': 'Fringes'},
        ),
    ]
