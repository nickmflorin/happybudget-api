from django.db import migrations

def group_names_to_polymorphic_base(apps, schema_editor):
    BudgetAccountGroup = apps.get_model('group', 'BudgetAccountGroup')
    TemplateAccountGroup = apps.get_model('group', 'TemplateAccountGroup')
    BudgetSubAccountGroup = apps.get_model('group', 'BudgetSubAccountGroup')
    TemplateSubAccountGroup = apps.get_model('group', 'TemplateSubAccountGroup')

    for model in [
        BudgetAccountGroup,
        TemplateAccountGroup,
        BudgetSubAccountGroup,
        TemplateSubAccountGroup
    ]:
        for instance in model.objects.all():
            instance.new_name = instance.name
            instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ('group', '0007_group_new_name'),
    ]

    operations = [
        migrations.RunPython(group_names_to_polymorphic_base),
    ]