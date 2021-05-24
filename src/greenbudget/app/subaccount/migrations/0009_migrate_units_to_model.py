from django.db import migrations
from django.contrib.contenttypes.models import ContentType


# These were pulled directly off the model at the time of this migration.
choices = [
    (0, 'Minutes'),
    (1, 'Hours'),
    (4, 'Days'),
    (5, 'Nights'),
    (2, 'Weeks'),
    (3, 'Months'),
    (6, 'Allow'),
    (7, 'Flat'),
    (8, 'Feet'),
    (9, 'Fare'),
    (10, 'Units'),
    (11, 'Person'),
    (12, 'Each'),
]


def reverse_func(apps, schema_editor):
    SubAccount = apps.get_model("subaccount", "SubAccount")
    SubAccountUnit = apps.get_model("subaccount", "SubAccountUnit")

    for subaccount_unit in SubAccountUnit.objects.all():
        subaccount_unit.delete()

    for subaccount in SubAccount.objects.all():
        if subaccount.unit_new is not None:
            unit_choice = iter([
                choice for choice in choices
                if choice[1] == subaccount.unit_new.title
            ])
            unit_choice = next(unit_choice)
            if unit_choice is None:
                print(
                    "Warning: Could not map new SubAccount unit %s "
                    "to previous choice.  This will result in a loss of data"
                    % subaccount.unit_new.title
                )
            else:
                subaccount.unit = unit_choice[0]
                subaccount.save()


def forwards_func(apps, schema_editor):
    SubAccountUnit = apps.get_model("subaccount", "SubAccountUnit")
    SubAccount = apps.get_model("subaccount", "SubAccount")

    content_type = ContentType.objects.get_for_model(SubAccountUnit)
    for i, (_, name) in enumerate(choices):
        SubAccountUnit.objects.get_or_create(
            # Required for Django-Polymorphic when creating models in migration
            # context.
            polymorphic_ctype_id=content_type.id,
            title=name,
            defaults={"order": i}
        )

    for subaccount in SubAccount.objects.all():
        if subaccount.unit is not None:
            unit_title = iter([
                choice[1] for choice in choices
                if choice[0] == subaccount.unit
            ])
            unit_title = next(unit_title)
            if unit_title is None:
                print(
                    "Warning: Could not map existing SubAccount unit %s "
                    "to choice.  This will result in a loss of data"
                    % subaccount.unit
                )
            else:
                # This should not fail because we created the SubAccountUnit
                # models in the previous step, and we already checked if the
                # unit_title is in the data used to create them, so we don't
                # need to wrap in a try/except around SubAccountUnit.DoesNotExist.
                # Also, the title needs to be unique for this to work.
                subaccount.unit_new = SubAccountUnit.objects.get(title=unit_title)
                subaccount.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0008_subaccount_unit_new'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]