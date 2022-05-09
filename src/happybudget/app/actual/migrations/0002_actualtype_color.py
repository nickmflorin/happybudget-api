from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
        ('actual', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualtype',
            name='color',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(('content_types__app_label', 'actual'), ('content_types__model', 'actualtype')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color'),
        ),
    ]
