from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_has_password'),
        ('io', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='created_by',
            field=models.ForeignKey(
                editable=False,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_%(class)ss',
                to='user.user'
            ),
        ),
    ]
