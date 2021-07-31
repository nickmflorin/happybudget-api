from django.db import migrations


def reverse_func(apps, schema_editor):
    Contact = apps.get_model("contact", "Contact")
    for contact in Contact.objects.all():
        contact.phone_number = contact.phone_number2
        contact.save()


def forwards_func(apps, schema_editor):
    Contact = apps.get_model("contact", "Contact")
    for contact in Contact.objects.all():
        contact.phone_number2 = contact.phone_number
        contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0011_contact_phone_number2'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]