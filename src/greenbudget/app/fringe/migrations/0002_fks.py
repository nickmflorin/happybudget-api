from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
        ('user', '0001_initial'),
        ('fringe', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fringe',
            name='budget',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='fringes', to='budget.basebudget'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='fringe',
            name='created_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='fringe',
            name='updated_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='fringe',
            unique_together={('budget', 'order')},
        ),
    ]
