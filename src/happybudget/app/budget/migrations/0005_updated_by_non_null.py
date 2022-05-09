from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_has_password'),
        ('budget', '0004_set_updated_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basebudget',
            name='updated_by',
            field=models.ForeignKey(
                default=1,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='updated_budgets',
                to='user.user'
            ),
            preserve_default=False,
        ),
    ]
