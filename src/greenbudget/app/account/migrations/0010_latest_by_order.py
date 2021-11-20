from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0009_order_by_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'get_latest_by': 'order', 'ordering': ('order',), 'verbose_name': 'Account', 'verbose_name_plural': 'Accounts'},
        ),
    ]
