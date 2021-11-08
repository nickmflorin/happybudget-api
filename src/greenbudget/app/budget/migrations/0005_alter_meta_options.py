from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0004_rethinking_calculations'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budget',
            options={'verbose_name': 'Budget', 'verbose_name_plural': 'Budgets'},
        ),
    ]
