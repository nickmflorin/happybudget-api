from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError


def get_instance_cls(obj, obj_type, as_content_type=False):
    from greenbudget.app.account.models import BudgetAccount, TemplateAccount
    from greenbudget.app.budget.models import Budget
    from greenbudget.app.subaccount.models import (
        BudgetSubAccount, TemplateSubAccount)
    from greenbudget.app.template.models import Template

    mapping = {
        (Budget, BudgetAccount, BudgetSubAccount): {
            'budget': Budget,
            'account': BudgetAccount,
            'subaccount': BudgetSubAccount
        },
        (Template, TemplateAccount, TemplateSubAccount): {
            'budget': Template,
            'account': TemplateAccount,
            'subaccount': TemplateSubAccount
        },
    }
    related_obj = None
    for k, v in mapping.items():
        if isinstance(obj, type) and obj in k:
            related_obj = v[obj_type]
            break
        elif not isinstance(obj, type) and isinstance(obj, k):
            related_obj = v[obj_type]
            break
    if related_obj is None:
        obj_name = related_obj.__name__ if isinstance(related_obj, type) \
            else related_obj.__class__.__name__
        raise IntegrityError(
            "Unexpected instance %s - could not determine %s model."
            % (obj_name, obj_type)
        )
    if as_content_type:
        return ContentType.objects.get_for_model(related_obj)
    return obj


def get_budget_instance_cls(obj, as_content_type=False):
    return get_instance_cls(
        obj=obj,
        obj_type='budget',
        as_content_type=as_content_type
    )


def get_account_instance_cls(obj, as_content_type=False):
    return get_instance_cls(
        obj=obj,
        obj_type='account',
        as_content_type=as_content_type
    )


def get_subaccount_instance_cls(obj, as_content_type=False):
    return get_instance_cls(
        obj=obj,
        obj_type='subaccount',
        as_content_type=as_content_type
    )
