from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0004_db_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='identifier',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='subaccount',
            unique_together=set(),
        ),
    ]
