from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markup',
            name='unit',
            field=models.IntegerField(choices=[(0, 'Percent'), (1, 'Flat')], default=0, null=True),
        ),
    ]
