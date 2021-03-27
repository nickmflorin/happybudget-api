from django.db import migrations, models
import django.db.models.deletion



def default_budgetitemgroup_ptr(apps, schema_editor):
    SubAccountGroup = apps.get_model("subaccount", "SubAccountGroup")
    # Unfortunately, I do not know if there is a way around this other than
    # deleting the previous groups.  The issue has to do with the non-nullable
    # budgetitemgroup_ptr field which we cannot allow the default=1 to take
    # place.
    for group in SubAccountGroup.objects.all():
        group.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('budget_item', '0003_budgetitem_group'),
        ('subaccount', '0006_remove_subaccount_group'),
    ]

    operations = [
        migrations.RunPython(default_budgetitemgroup_ptr),
        migrations.RemoveField(
            model_name='subaccountgroup',
            name='id',
        ),
        migrations.AddField(
            model_name='subaccountgroup',
            name='budgetitemgroup_ptr',
            field=models.OneToOneField(auto_created=True, default=1, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget_item.budgetitemgroup'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='subaccountgroup',
            name='color',
        ),
        migrations.RemoveField(
            model_name='subaccountgroup',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='subaccountgroup',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='subaccountgroup',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='subaccountgroup',
            name='updated_by',
        ),
    ]
