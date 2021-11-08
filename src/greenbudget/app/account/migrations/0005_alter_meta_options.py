from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_rethinking_calculations'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budgetaccount',
            options={'verbose_name': 'Account', 'verbose_name_plural': 'Accounts'},
        ),
        migrations.AlterModelOptions(
            name='templateaccount',
            options={'verbose_name': 'Account', 'verbose_name_plural': 'Accounts'},
        ),
    ]
