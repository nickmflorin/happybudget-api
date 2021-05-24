from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0007_subaccountunit'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='unit_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='subaccount.subaccountunit'
            ),
        ),
    ]
