from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0006_make_trash_db_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='basebudget',
            name='estimated',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='budget',
            name='actual',
            field=models.FloatField(default=0.0),
        ),
    ]
