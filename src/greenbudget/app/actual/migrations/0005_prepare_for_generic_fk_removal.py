from django.db import migrations
from django.contrib.contenttypes.models import ContentType


def reverse_func(apps, schema_editor):
    Actual = apps.get_model("actual", "Actual")
    BudgetSubAccount = apps.get_model("subaccount", "BudgetSubAccount")

    content_type = ContentType.objects.get_for_model(BudgetSubAccount)
    for actual in Actual.objects.all():
        if actual.subaccount is not None:
            actual.content_type = content_type
            actual.object_id = actual.subaccount.pk
            actual.save()


def forwards_func(apps, schema_editor):
    Actual = apps.get_model("actual", "Actual")
    BudgetSubAccount = apps.get_model("subaccount", "BudgetSubAccount")

    content_type = ContentType.objects.get_for_model(BudgetSubAccount)
    for actual in Actual.objects.all():
        if actual.object_id is not None:
            if actual.content_type_id == content_type.pk:
                actual.subaccount = BudgetSubAccount.objects.get(
                    pk=actual.object_id)
                actual.save()
            else:
                print(
                    "Deleting Actual %s as it Relates to An Account"
                    % actual.pk
                )
                actual.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0004_actual_subaccount'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]