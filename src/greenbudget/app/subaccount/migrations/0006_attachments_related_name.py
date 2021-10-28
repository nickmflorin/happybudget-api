from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('io', '0001_initial'),
        ('subaccount', '0005_budgetsubaccount_attachments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetsubaccount',
            name='attachments',
            field=models.ManyToManyField(related_name='subaccounts', to='io.Attachment'),
        ),
    ]
