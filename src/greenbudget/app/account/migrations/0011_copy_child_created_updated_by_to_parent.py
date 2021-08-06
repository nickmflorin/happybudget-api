from django.db import migrations


def reverse_func(apps, schema_editor):
    BudgetAccount = apps.get_model("account", "BudgetAccount")
    for account in BudgetAccount.objects.all():
        account.updated_by = account.updated_by_new
        account.created_by = account.created_by_new
        account.save()

    TemplateAccount = apps.get_model("account", "TemplateAccount")
    for account in TemplateAccount.objects.all():
        account.updated_by = account.updated_by_new
        account.created_by = account.created_by_new
        account.save()


def forwards_func(apps, schema_editor):
    BudgetAccount = apps.get_model("account", "BudgetAccount")
    for account in BudgetAccount.objects.all():
        account.updated_by_new = account.updated_by
        account.created_by_new = account.created_by
        account.save()

    TemplateAccount = apps.get_model("account", "TemplateAccount")
    for account in TemplateAccount.objects.all():
        account.updated_by_new = account.updated_by
        account.created_by_new = account.created_by
        account.save()


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_created_by_updated_by_to_parent'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]