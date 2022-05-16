from django.db import migrations, models
import happybudget.app.budget.models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0005_updated_by_non_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basebudget',
            name='image',
            field=models.ImageField(
                max_length=256,
                null=True,
                upload_to=happybudget.app.budget.models.upload_to
            ),
        ),
    ]
