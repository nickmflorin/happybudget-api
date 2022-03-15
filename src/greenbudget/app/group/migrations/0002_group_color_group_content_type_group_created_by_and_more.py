from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('tagging', '0001_initial'),
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='color',
            field=models.ForeignKey(limit_choices_to=models.Q(('content_types__app_label', 'group'), ('content_types__model', 'group')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color'),
        ),
        migrations.AddField(
            model_name='group',
            name='content_type',
            field=models.ForeignKey(default=1, limit_choices_to=models.Q(models.Q(('app_label', 'subaccount'), ('model', 'subaccount')), models.Q(('app_label', 'account'), ('model', 'account')), models.Q(('app_label', 'budget'), ('model', 'basebudget')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='group',
            name='created_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='group',
            name='updated_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user'),
            preserve_default=False,
        ),
    ]
