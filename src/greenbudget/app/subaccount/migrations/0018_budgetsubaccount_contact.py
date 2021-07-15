from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0009_contact_image'),
        ('subaccount', '0017_updated_by_non_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetsubaccount',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_subaccounts', to='contact.contact'),
        ),
    ]
