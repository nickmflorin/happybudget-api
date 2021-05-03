from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='color',
            name='name',
            field=models.CharField(max_length=32, null=True, unique=True),
        ),
    ]
