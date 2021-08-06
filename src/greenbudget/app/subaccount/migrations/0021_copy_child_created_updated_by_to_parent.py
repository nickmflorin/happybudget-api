from django.db import migrations


def reverse_func(apps, schema_editor):
    BudgetSubAccount = apps.get_model("subaccount", "BudgetSubAccount")
    for account in BudgetSubAccount.objects.all():
        account.updated_by = account.updated_by_new
        account.created_by = account.created_by_new
        account.save()

    TemplateSubAccount = apps.get_model("subaccount", "TemplateSubAccount")
    for account in TemplateSubAccount.objects.all():
        account.updated_by = account.updated_by_new
        account.created_by = account.created_by_new
        account.save()


def forwards_func(apps, schema_editor):
    BudgetSubAccount = apps.get_model("subaccount", "BudgetSubAccount")
    for account in BudgetSubAccount.objects.all():
        account.updated_by_new = account.updated_by
        account.created_by_new = account.created_by
        account.save()

    TemplateSubAccount = apps.get_model("subaccount", "TemplateSubAccount")
    for account in TemplateSubAccount.objects.all():
        account.updated_by_new = account.updated_by
        account.created_by_new = account.created_by
        account.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0020_created_by_updated_by_to_parent'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]