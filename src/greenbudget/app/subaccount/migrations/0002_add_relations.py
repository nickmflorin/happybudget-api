from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0002_add_relations'),
        ('group', '0002_add_relations'),
        ('subaccount', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subaccounts', to='group.group'),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='markups',
            field=models.ManyToManyField(related_name='subaccounts', to='markup.Markup'),
        ),
    ]
