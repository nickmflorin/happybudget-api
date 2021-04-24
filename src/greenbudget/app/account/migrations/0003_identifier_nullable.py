from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_account_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='identifier',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='account',
            unique_together=set(),
        ),
    ]
