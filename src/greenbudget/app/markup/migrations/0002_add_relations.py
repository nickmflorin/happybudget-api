from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('group', '0002_add_relations'),
        ('markup', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='markup',
            name='content_type',
            field=models.ForeignKey(default=1, limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'budgetaccount')), models.Q(('app_label', 'subaccount'), ('model', 'budgetsubaccount')), models.Q(('app_label', 'budget'), ('model', 'budget')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='markup',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children_markups', to='group.group'),
        ),
        migrations.AddField(
            model_name='markup',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, default=1),
            preserve_default=False,
        ),
    ]
