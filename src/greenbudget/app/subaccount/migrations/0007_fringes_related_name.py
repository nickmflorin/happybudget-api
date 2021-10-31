from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0003_reverse_ordering'),
        ('subaccount', '0006_attachments_related_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='fringes',
            field=models.ManyToManyField(related_name='subaccounts', to='fringe.Fringe'),
        ),
    ]
