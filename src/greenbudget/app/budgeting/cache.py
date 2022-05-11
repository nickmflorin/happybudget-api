from happybudget.lib.django_utils.models import group_models_by_type, ModelMap

from happybudget.app.account.cache import (
    account_groups_cache, account_markups_cache)
from happybudget.app.budget.cache import (
    budget_groups_cache, budget_markups_cache)
from happybudget.app.subaccount.cache import (
    subaccount_groups_cache, subaccount_markups_cache)


groups_cache_map = ModelMap({
    'budget.BaseBudget': budget_groups_cache,
    'account.Account': account_groups_cache,
    'subaccount.SubAccount': subaccount_groups_cache
})


def get_group_cache(instance_or_type):
    return groups_cache_map.get(instance_or_type, strict=True)


def invalidate_groups_cache(instances):
    grouped_instances = group_models_by_type(
        instances=instances,
        types=list(groups_cache_map.keys())
    )
    for grouped_type, type_instances in grouped_instances.items():
        get_group_cache(grouped_type).invalidate(type_instances)


markups_cache_map = ModelMap({
    'budget.BaseBudget': budget_markups_cache,
    'account.Account': account_markups_cache,
    'subaccount.SubAccount': subaccount_markups_cache
})


def get_markup_cache(instance_or_type):
    return markups_cache_map.get(instance_or_type, strict=True)


def invalidate_markups_cache(instances):
    grouped_instances = group_models_by_type(
        instances=instances,
        types=list(markups_cache_map.keys())
    )
    for grouped_type, type_instances in grouped_instances.items():
        get_markup_cache(grouped_type).invalidate(type_instances)
