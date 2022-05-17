from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_has_password'),
        ('account', '0002_account_group_account_markups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
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
            model_name='account',
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
