from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_user_approval'),
        ('fringe', '0010_default_order_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fringe',
            name='created_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user'),
        ),
        migrations.AlterField(
            model_name='fringe',
            name='updated_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user'),
        ),
    ]
