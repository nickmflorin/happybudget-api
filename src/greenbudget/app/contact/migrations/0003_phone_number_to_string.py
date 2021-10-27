from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_type_to_contact_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='phone_number',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
