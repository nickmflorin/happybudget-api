from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0018_django_4'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='notes',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
