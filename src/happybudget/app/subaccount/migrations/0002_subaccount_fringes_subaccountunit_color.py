from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
        ('fringe', '0003_fringe_color'),
        ('subaccount', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='fringes',
            field=models.ManyToManyField(related_name='subaccounts', to='fringe.Fringe'),
        ),
        migrations.AddField(
            model_name='subaccountunit',
            name='color',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(('content_types__app_label', 'subaccount'), ('content_types__model', 'subaccountunit')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color'),
        ),
    ]
