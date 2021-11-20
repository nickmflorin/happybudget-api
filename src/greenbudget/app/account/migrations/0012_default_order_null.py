from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_ordering_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='order',
            field=models.CharField(default=None, editable=False, max_length=1024),
        ),
    ]
