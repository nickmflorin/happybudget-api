from django.urls import reverse

from greenbudget.app import cache
from greenbudget.app.budget.cache import budget_instance_cache


account_subaccounts_cache = cache.endpoint_cache(
    id='children',
    path=lambda instance: reverse(
        'account:subaccount-list', kwargs={'account_pk': instance.pk})
)

account_markups_cache = cache.endpoint_cache(
    id="markup",
    path=lambda instance: reverse(
        'account:markup-list', kwargs={'account_pk': instance.pk})
)

account_groups_cache = cache.endpoint_cache(
    id='group',
    path=lambda instance: reverse(
        'account:group-list', kwargs={'account_pk': instance.pk})
)


def account_instance_cache_dependency(instance):
    account_subaccounts_cache.invalidate(instance)
    budget_instance_cache.invalidate(instance.budget)


account_instance_cache = cache.endpoint_cache(
    id='detail',
    dependency=account_instance_cache_dependency,
    path=lambda instance: reverse(
        'account:account-detail', kwargs={'pk': instance.pk})
)
