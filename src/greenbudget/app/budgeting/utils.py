from django.contrib.contenttypes.models import ContentType
from django.apps import apps


def import_model_at_path(path):
    return apps.get_model(
        app_label=path.split('.')[0],
        model_name=path.split('.')[1]
    )


def get_from_instance_mapping(mapping, obj):
    def normalize(o):
        if isinstance(o, str):
            return import_model_at_path(o)
        return o
    for k, v in mapping.items():
        normalized = tuple([normalize(ki) for ki in k]) \
            if isinstance(k, tuple) else normalize(k)
        if isinstance(obj, type):
            if isinstance(normalized, tuple) and obj in normalized:
                return v
            elif not isinstance(normalized, tuple) and obj is normalized:
                return v
        elif not isinstance(obj, type) and isinstance(obj, normalized):
            return v
    obj_name = obj.__name__ if isinstance(obj, type) else obj.__class__.__name__
    raise ValueError("Unexpected instance %s." % obj_name)


def get_instance_cls(obj, obj_type, as_content_type=False):
    mapping = {
        (
            'budget.Budget',
            'account.BudgetAccount',
            'subaccount.BudgetSubAccount',
        ): {
            'budget': 'budget.Budget',
            'account': 'account.BudgetAccount',
            'subaccount': 'subaccount.BudgetSubAccount'
        },
        (
            'template.Template',
            'account.TemplateAccount',
            'subaccount.TemplateSubAccount',
        ): {
            'budget': 'template.Template',
            'account': 'account.TemplateAccount',
            'subaccount': 'subaccount.TemplateSubAccount',  # noqa
        },
    }
    subset = get_from_instance_mapping(mapping, obj)
    if obj_type not in subset:
        raise ValueError("Invalid object type %s." % obj_type)
    related_obj = import_model_at_path(subset[obj_type])
    if as_content_type:
        return ContentType.objects.get_for_model(related_obj)
    return related_obj


def get_child_instance_cls(obj, as_content_type=False):
    mapping = {
        'budget.Budget': 'account.BudgetAccount',
        'template.Template': 'account.TemplateAccount',
        ('account.BudgetAccount', 'subaccount.BudgetSubAccount'):
            'subaccount.BudgetSubAccount',
        ('account.TemplateAccount', 'subaccount.TemplateSubAccount'):
            'subaccount.TemplateSubAccount'  # noqa
    }
    obj_cls = get_from_instance_mapping(mapping, obj)
    related_obj = import_model_at_path(obj_cls)
    if as_content_type:
        return ContentType.objects.get_for_model(related_obj)
    return related_obj