from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0003_reverse_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='fringe',
            name='order',
            field=models.CharField(default='', max_length=1024, null=True),
        ),
    ]
