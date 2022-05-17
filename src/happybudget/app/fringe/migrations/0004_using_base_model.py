from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_has_password'),
        ('fringe', '0003_fringe_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fringe',
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
            model_name='fringe',
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
