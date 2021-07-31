from django.db import migrations, models


# At the time of this migration, the phone number field was already nullable.
# However, something seemed to have gotten misaligned with the database, and
# it thought it was non-nullable, so we created this additional migration to try
# to force it into a nullable state.
class Migration(migrations.Migration):
    dependencies = [
        ('contact', '0009_contact_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='phone_number',
            field=models.BigIntegerField(null=True),
        ),
    ]
