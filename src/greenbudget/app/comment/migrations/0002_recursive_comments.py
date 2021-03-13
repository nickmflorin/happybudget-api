from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('comment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'Account')), models.Q(('app_label', 'subaccount'), ('model', 'SubAccount')), models.Q(('app_label', 'budget'), ('model', 'Budget')), models.Q(('app_label', 'comment'), ('model', 'Comment')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
    ]
