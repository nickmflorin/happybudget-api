from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='color_new',
            field=models.ForeignKey(limit_choices_to=models.Q(('content_types__app_label', 'group'), ('content_types__model', 'group')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color'),
        ),
    ]
