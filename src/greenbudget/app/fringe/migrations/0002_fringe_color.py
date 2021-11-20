from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
        ('fringe', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fringe',
            name='color',
            field=models.ForeignKey(limit_choices_to=models.Q(('content_types__app_label', 'fringe'), ('content_types__model', 'fringe')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color'),
        ),
    ]
