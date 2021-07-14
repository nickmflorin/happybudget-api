from django.db import migrations, models
import greenbudget.app.contact.models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0008_remove_contact_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='image',
            field=models.ImageField(null=True, upload_to=greenbudget.app.contact.models.upload_to),
        ),
    ]
