from django.urls import reverse

from greenbudget.app import cache
from greenbudget.app.budget.cache import (
    budget_instance_cache, budget_children_cache)


account_children_cache = cache.endpoint_cache(
    id='account-children',
    path=lambda instance: reverse(
        'account:child-list', kwargs={'account_pk': instance.pk})
)

account_markups_cache = cache.endpoint_cache(
    id="account-markup",
    path=lambda instance: reverse(
        'account:markup-list', kwargs={'account_pk': instance.pk})
)

account_groups_cache = cache.endpoint_cache(
    id='account-group',
    path=lambda instance: reverse(
        'account:group-list', kwargs={'account_pk': instance.pk})
)

account_instance_cache = cache.endpoint_cache(
    id='account-detail',
    dependency=[
        lambda instance: budget_instance_cache.invalidate(
            instance.budget),
        lambda instance: budget_children_cache.invalidate(instance.budget)
    ],
    path=lambda instance: reverse(
        'account:account-detail', kwargs={'pk': instance.pk})
)
