from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0001_initial'),
        ('group', '0002_group_color_group_content_type_group_created_by_and_more'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)ss', to='group.group'),
        ),
        migrations.AddField(
            model_name='account',
            name='markups',
            field=models.ManyToManyField(related_name='%(class)ss', to='markup.Markup'),
        ),
    ]
