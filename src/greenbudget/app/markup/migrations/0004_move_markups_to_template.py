from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('markup', '0003_remove_markup_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markup',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'account')), models.Q(('app_label', 'subaccount'), ('model', 'subaccount')), models.Q(('app_label', 'budget'), ('model', 'basebudget')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='markup',
            name='created_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_markups', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='markup',
            name='updated_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_markups', to=settings.AUTH_USER_MODEL),
        ),
    ]
