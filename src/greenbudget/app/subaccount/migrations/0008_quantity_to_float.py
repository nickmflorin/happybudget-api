from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0007_fringes_related_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budgetsubaccount',
            options={'verbose_name': 'Budget Sub Account', 'verbose_name_plural': 'Budget Sub Accounts'},
        ),
        migrations.AlterModelOptions(
            name='templatesubaccount',
            options={'verbose_name': 'Template Sub Account', 'verbose_name_plural': 'Template Sub Accounts'},
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='quantity',
            field=models.FloatField(null=True),
        ),
    ]
