from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='name',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='subaccount',
            unique_together=set(),
        ),
    ]
