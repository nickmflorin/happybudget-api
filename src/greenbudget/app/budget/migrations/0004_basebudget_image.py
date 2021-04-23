from django.db import migrations, models
import greenbudget.app.budget.models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0003_unique_with_trash'),
    ]

    operations = [
        migrations.AddField(
            model_name='basebudget',
            name='image',
            field=models.ImageField(null=True, upload_to=greenbudget.app.budget.models.upload_to),
        ),
    ]
