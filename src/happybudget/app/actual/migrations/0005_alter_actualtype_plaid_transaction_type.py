from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0004_actualtype_plaid_transaction_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actualtype',
            name='plaid_transaction_type',
            field=models.IntegerField(choices=[(0, 'Credit Card'), (1, 'Check'), (2, 'Wire'), (3, 'ACH')], help_text='Designates which Plaid transaction type should be mapped to this actual type.', null=True, unique=True),
        ),
    ]
