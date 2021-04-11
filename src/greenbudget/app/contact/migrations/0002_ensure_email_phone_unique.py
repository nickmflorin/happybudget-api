from django.conf import settings
from django.db import migrations


def ensure_unique(apps, schema_editor):
    Contact = apps.get_model('contact', 'Contact')

    processed_emails = {}
    processed_phone_numbers = {}
    unique_generated_emails = {}
    unique_generated_phone_numbers = {}
    for contact in Contact.objects.all():
        altered = False

        unique_generated_phone_numbers.setdefault(contact.user.id, 1)
        processed_phone_numbers.setdefault(contact.user.id, [])

        if contact.phone_number in processed_phone_numbers[contact.user.id]:
            base_phone_number = 15555555555 + unique_generated_phone_numbers[contact.user.id]  # noqa
            contact.phone_number = "+%s" % base_phone_number
            unique_generated_phone_numbers[contact.user.id] += 1
            altered = True
        else:
            processed_phone_numbers[contact.user.id].append(contact.phone_number)

        processed_emails.setdefault(contact.user.id, [])
        unique_generated_emails.setdefault(contact.user.id, 1)

        if contact.email in processed_emails[contact.user.id]:
            base_email = "notunique-%s" % unique_generated_emails[contact.user.id]  # noqa
            contact.email = "%s@unsupported.com" % base_email
            unique_generated_emails[contact.user.id] += 1
            altered = True
        else:
            processed_emails[contact.user.id].append(contact.email)

        if altered:
            print("Updating contact...")
            contact.save()



class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_unique),
    ]
