from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0003_alter_actual_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualtype',
            name='plaid_transaction_type',
            field=models.IntegerField(choices=[(0, 'Credit Card')], help_text='Designates which Plaid transaction type should be mapped to this actual type.', null=True, unique=True),
        ),
    ]
