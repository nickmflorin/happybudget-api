from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='value',
            field=models.FloatField(null=True),
        ),
    ]
