from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0002_actualtype_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='date',
            field=models.DateField(null=True),
        ),
    ]
