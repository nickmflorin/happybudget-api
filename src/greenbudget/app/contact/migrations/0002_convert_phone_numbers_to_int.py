import re
from django.db import migrations


def forwards_func(apps, schema_editor):
    Contact = apps.get_model("contact", "Contact")

    for obj in Contact.objects.all():
        obj.phone_number = re.sub("[^0-9]", "", obj.phone_number)
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func)
    ]