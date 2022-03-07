from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('authentication', '0003_delete_share_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publictoken',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(('app_label', 'budget'), ('model', 'Budget')), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
    ]
