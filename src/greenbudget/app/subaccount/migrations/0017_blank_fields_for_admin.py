from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0016_django_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='actual',
            field=models.FloatField(blank=True, default=0.0),
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='description',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='identifier',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='multiplier',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='quantity',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='rate',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
