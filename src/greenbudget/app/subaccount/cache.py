from django.urls import reverse

from greenbudget.lib.django_utils.models import ModelMap, group_models_by_type
from greenbudget.lib.django_utils.urls import lazy_reverse

from greenbudget.app import cache
from greenbudget.app.account.cache import (
    account_instance_cache, account_children_cache, account_groups_cache)


subaccount_children_cache = cache.endpoint_cache(
    id='children',
    path=lambda instance: reverse(
        'subaccount:child-list', kwargs={'subaccount_pk': instance.pk})
)

subaccount_markups_cache = cache.endpoint_cache(
    id='markup',
    path=lambda instance: reverse(
        'subaccount:markup-list', kwargs={'subaccount_pk': instance.pk})
)

subaccount_groups_cache = cache.endpoint_cache(
    id='group',
    path=lambda instance: reverse(
        'subaccount:group-list', kwargs={'subaccount_pk': instance.pk})
)

subaccount_units_cache = cache.endpoint_cache(
    id='subaccount-units',
    path=lazy_reverse('subaccount:unit-list')
)


def invalidate_parent_instance_cache(instances, **kwargs):
    grouped_instances = group_models_by_type(
        instances=instances,
        types=list(parent_instance_cache_map.keys())
    )
    for grouped_type, type_instances in grouped_instances.items():
        get_parent_instance_cache(grouped_type).invalidate(
            type_instances, **kwargs)


def invalidate_parent_children_cache(instances, **kwargs):
    grouped_instances = group_models_by_type(
        instances=instances,
        types=list(parent_children_cache_map.keys())
    )
    for grouped_type, type_instances in grouped_instances.items():
        get_parent_children_cache(grouped_type).invalidate(
            type_instances, **kwargs)


def invalidate_parent_groups_cache(instances, **kwargs):
    grouped_instances = group_models_by_type(
        instances=instances,
        types=list(parent_group_cache_map.keys())
    )
    for grouped_type, type_instances in grouped_instances.items():
        get_parent_group_cache(grouped_type).invalidate(
            type_instances, **kwargs)


subaccount_instance_cache = cache.endpoint_cache(
    id='detail',
    dependency=[
        lambda instance: invalidate_parent_instance_cache(
            instance.parent),
        lambda instance: invalidate_parent_children_cache(
            instance.parent),
    ],
    path=lambda instance: reverse(
        'subaccount:subaccount-detail', kwargs={'pk': instance.pk})
)


parent_instance_cache_map = ModelMap({
    'account.Account': account_instance_cache,
    'subaccount.SubAccount': subaccount_instance_cache
})


def get_parent_instance_cache(instance_or_type):
    return parent_instance_cache_map.get(instance_or_type, strict=True)


parent_children_cache_map = ModelMap({
    'account.Account': account_children_cache,
    'subaccount.SubAccount': subaccount_children_cache
})


def get_parent_children_cache(instance_or_type):
    return parent_children_cache_map.get(instance_or_type, strict=True)


parent_group_cache_map = ModelMap({
    'account.Account': account_groups_cache,
    'subaccount.SubAccount': subaccount_groups_cache
})


def get_parent_group_cache(instance_or_type):
    return parent_group_cache_map.get(instance_or_type, strict=True)
