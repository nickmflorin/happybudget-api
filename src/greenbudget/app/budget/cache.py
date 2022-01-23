from django.urls import reverse

from greenbudget.lib.utils import ensure_iterable
from greenbudget.app import cache
from greenbudget.app.template.cache import (
    template_instance_cache,
    template_fringes_cache,
    template_markups_cache,
    template_groups_cache,
    template_accounts_cache
)


budget_accounts_cache = cache.endpoint_cache(
    id='children',
    path=lambda instance: reverse(
        'budget:account-list', kwargs={'budget_pk': instance.pk})
)

budget_groups_cache = cache.endpoint_cache(
    id='group',
    path=lambda instance: reverse(
        'budget:group-list', kwargs={'budget_pk': instance.pk})
)

budget_actuals_cache = cache.endpoint_cache(
    id='actual',
    path=lambda instance: reverse(
        'budget:actual-list', kwargs={'budget_pk': instance.pk})
)

budget_actuals_owners_cache = cache.endpoint_cache(
    id='actuals-owners',
    path=lambda instance: reverse(
        'budget:actual-owner-list', kwargs={'budget_pk': instance.pk})
)

budget_markups_cache = cache.endpoint_cache(
    id='markup',
    path=lambda instance: reverse(
        'budget:markup-list', kwargs={'budget_pk': instance.pk})
)

budget_fringes_cache = cache.endpoint_cache(
    id='fringe',
    path=lambda instance: reverse(
        'budget:fringe-list', kwargs={'budget_pk': instance.pk})
)


def invalidate_budget_groups_cache(instances, **kwargs):
    instances = ensure_iterable(instances)
    template_groups_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'template'],
        **kwargs
    )
    budget_groups_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'budget'],
        **kwargs
    )


def invalidate_budget_markups_cache(instances, **kwargs):
    instances = ensure_iterable(instances)
    template_markups_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'template'],
        **kwargs
    )
    budget_markups_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'budget'],
        **kwargs
    )


def invalidate_budget_accounts_cache(instances, **kwargs):
    instances = ensure_iterable(instances)
    template_accounts_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'template'],
        **kwargs
    )
    budget_accounts_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'budget'],
        **kwargs
    )


def invalidate_fringes_cache(instances, **kwargs):
    instances = ensure_iterable(instances)
    template_fringes_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'template'],
        **kwargs
    )
    budget_fringes_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'budget'],
        **kwargs
    )


def budget_instance_cache_dependency(instance):
    budget_accounts_cache.invalidate(instance)


budget_instance_cache = cache.endpoint_cache(
    id='detail',
    dependency=budget_instance_cache_dependency,
    path=lambda instance: reverse(
        'budget:budget-detail', kwargs={'pk': instance.pk})
)


def invalidate_budget_instance_cache(instances, **kwargs):
    instances = ensure_iterable(instances)
    template_instance_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'template'],
        **kwargs
    )
    budget_instance_cache.invalidate(
        instance=[bi for bi in instances if bi.domain == 'budget'],
        **kwargs
    )
