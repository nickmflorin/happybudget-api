from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0007_django_4'),
    ]

    operations = [
        migrations.AddField(
            model_name='basebudget',
            name='is_deleting',
            field=models.BooleanField(default=False),
        ),
    ]
