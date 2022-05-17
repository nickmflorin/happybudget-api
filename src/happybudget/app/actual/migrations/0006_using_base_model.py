from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_has_password'),
        ('actual', '0005_alter_actualtype_plaid_transaction_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='created_by',
            field=models.ForeignKey(
                editable=False,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_%(class)ss',
                to='user.user'
            ),
        ),
        migrations.AlterField(
            model_name='actual',
            name='updated_by',
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='updated_%(class)ss',
                to='user.user'
            ),
        ),
    ]
