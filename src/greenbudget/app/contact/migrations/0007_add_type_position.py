from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0006_remove_country_add_rate_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='position',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='type',
            field=models.IntegerField(choices=[(0, 'Contractor'), (1, 'Employee'), (2, 'Vendor')], null=True),
        ),
    ]
