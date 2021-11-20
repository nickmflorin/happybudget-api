from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0011_order_non_null'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subaccount',
            options={'get_latest_by': 'updated_at', 'ordering': ('order',), 'verbose_name': 'Sub Account', 'verbose_name_plural': 'Sub Accounts'},
        ),
    ]
