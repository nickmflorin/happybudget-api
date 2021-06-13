from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0003_budgetfringe_templatefringe'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fringe',
            name='name',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
