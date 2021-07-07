from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0004_remove_unique_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='first_name',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
