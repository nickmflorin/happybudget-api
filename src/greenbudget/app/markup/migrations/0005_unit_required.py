from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0004_move_markups_to_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markup',
            name='unit',
            field=models.IntegerField(choices=[(0, 'Percent'), (1, 'Flat')], default=0),
        ),
    ]
