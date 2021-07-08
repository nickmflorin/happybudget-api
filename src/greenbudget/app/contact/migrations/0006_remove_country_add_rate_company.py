from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0005_first_name_nullable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='country',
        ),
        migrations.AddField(
            model_name='contact',
            name='company',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='rate',
            field=models.IntegerField(null=True),
        ),
    ]
