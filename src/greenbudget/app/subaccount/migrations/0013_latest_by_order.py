from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0012_order_by_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subaccount',
            options={'get_latest_by': 'order', 'ordering': ('order',), 'verbose_name': 'Sub Account', 'verbose_name_plural': 'Sub Accounts'},
        ),
    ]
