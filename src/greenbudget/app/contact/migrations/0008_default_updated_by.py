from django.conf import settings
from django.db import migrations


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Contact = apps.get_model("contact", "Contact")

    db_alias = schema_editor.connection.alias
    updated = []
    for obj in Contact.objects.using(db_alias).all():
        if obj.updated_by is None:
            obj.updated_by = obj.created_by
            updated.append(obj)
    Contact.objects.using(db_alias).bulk_update(updated, ['updated_by'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0007_contact_updated_by'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
