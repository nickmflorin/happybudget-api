from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_has_password'),
        ('budget', '0006_image_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basebudget',
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
            model_name='basebudget',
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
