from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0003_alter_created_updated_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
