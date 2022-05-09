from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('markup', '0001_initial'),
        ('group', '0002_group_color_group_content_type_group_created_by_and_more'),
        ('subaccount', '0002_subaccount_fringes_subaccountunit_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)ss', to='group.group'),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='markups',
            field=models.ManyToManyField(related_name='%(class)ss', to='markup.Markup'),
        ),
    ]
