from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
        ('actual', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='actual',
            name='budget',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='actuals', to='budget.budget'),
            preserve_default=False,
        ),
    ]
