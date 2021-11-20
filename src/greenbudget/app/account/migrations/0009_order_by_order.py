from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_order_non_null'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'get_latest_by': 'updated_at', 'ordering': ('order',), 'verbose_name': 'Account', 'verbose_name_plural': 'Accounts'},
        ),
    ]
