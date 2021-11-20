from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0008_quantity_to_float'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='order',
            field=models.CharField(default='', max_length=1024, null=True),
        ),
    ]
