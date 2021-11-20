from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_default_order_null'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetaccount',
            name='access',
        ),
    ]
