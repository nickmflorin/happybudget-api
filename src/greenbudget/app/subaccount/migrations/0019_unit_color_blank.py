from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0007_tag_plural_title'),
        ('subaccount', '0018_budgetsubaccount_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccountunit',
            name='color',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(('content_types__app_label', 'subaccount'), ('content_types__model', 'subaccountunit')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color'),
        ),
    ]
