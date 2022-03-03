from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0006_row_model_inheritance'),
        ('markup', '0007_row_model_inheritance'),
        ('account', '0015_blank_fields_for_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='actual',
            field=models.FloatField(blank=True, default=0.0),
        ),
        migrations.AlterField(
            model_name='account',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)ss', to='group.group'),
        ),
        migrations.AlterField(
            model_name='account',
            name='markups',
            field=models.ManyToManyField(related_name='%(class)ss', to='markup.Markup'),
        ),
    ]
