from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_django_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='description',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='identifier',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
