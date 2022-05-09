from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='publictoken',
            name='content_type',
            field=models.ForeignKey(default=1, limit_choices_to=models.Q(('app_label', 'budget'), ('model', 'Budget')), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publictoken',
            name='created_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='publictoken',
            unique_together={('content_type', 'object_id')},
        ),
    ]
