from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0005_remove_unique_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basebudget',
            name='trash',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
