from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0013_alter_user_first_name'),
        ('markup', '0006_reverse_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markup',
            name='created_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user'),
        ),
        migrations.AlterField(
            model_name='markup',
            name='updated_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user'),
        ),
    ]
