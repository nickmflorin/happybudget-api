from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0001_initial'),
        ('group', '0001_initial'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accounts', to='group.group'),
        ),
        migrations.AddField(
            model_name='account',
            name='markups',
            field=models.ManyToManyField(related_name='accounts', to='markup.Markup'),
        ),
    ]
