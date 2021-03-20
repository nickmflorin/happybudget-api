from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('subaccount', '0003_subaccount_group'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subaccountgroup',
            unique_together={('object_id', 'content_type', 'name')},
        ),
    ]
