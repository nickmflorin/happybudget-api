from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0014_ordering_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='order',
            field=models.CharField(default=None, editable=False, max_length=1024),
        ),
    ]
