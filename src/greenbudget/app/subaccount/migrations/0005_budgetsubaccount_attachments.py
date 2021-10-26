from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('io', '0001_initial'),
        ('subaccount', '0004_rethinking_calculations'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetsubaccount',
            name='attachments',
            field=models.ManyToManyField(to='io.Attachment'),
        ),
    ]
