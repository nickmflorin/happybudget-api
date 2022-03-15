from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Template',
            fields=[
                ('basebudget_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget.basebudget')),
                ('community', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Template',
                'verbose_name_plural': 'Templates',
                'abstract': False,
            },
            bases=('budget.basebudget',),
        ),
        migrations.AddConstraint(
            model_name='template',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('community', True), ('hidden', False)), models.Q(('community', True), ('hidden', True)), models.Q(('community', False), ('hidden', False)), _connector='OR'), name='template_template_hidden_only_for_community'),
        ),
    ]
