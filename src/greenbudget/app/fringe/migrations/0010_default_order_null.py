from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0009_ordering_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fringe',
            name='order',
            field=models.CharField(default=None, editable=False, max_length=1024),
        ),
    ]
