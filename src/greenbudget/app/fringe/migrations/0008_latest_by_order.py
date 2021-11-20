from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0007_order_by_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fringe',
            options={'get_latest_by': 'order', 'ordering': ('order',), 'verbose_name': 'Fringe', 'verbose_name_plural': 'Fringes'},
        ),
    ]
