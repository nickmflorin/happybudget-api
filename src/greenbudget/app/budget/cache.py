from django.urls import reverse

from greenbudget.app import cache


budget_children_cache = cache.endpoint_cache(
    id='budget-children',
    path=lambda instance: reverse(
        'budget:child-list', kwargs={'pk': instance.pk})
)

budget_groups_cache = cache.endpoint_cache(
    id='budget-group',
    path=lambda instance: reverse(
        'budget:group-list', kwargs={'pk': instance.pk})
)

budget_markups_cache = cache.endpoint_cache(
    id='budget-markup',
    path=lambda instance: reverse(
        'budget:markup-list', kwargs={'pk': instance.pk})
)

budget_fringes_cache = cache.endpoint_cache(
    id='budget-fringe',
    path=lambda instance: reverse(
        'budget:fringe-list', kwargs={'pk': instance.pk}),
)

budget_actuals_cache = cache.endpoint_cache(
    id='budget-actual',
    path=lambda instance: reverse(
        'budget:actual-list', kwargs={'pk': instance.pk})
)

budget_actuals_owners_cache = cache.endpoint_cache(
    id='budget-actuals-owners',
    path=lambda instance: reverse(
        'budget:actual-owner-list', kwargs={'pk': instance.pk})
)

budget_instance_cache = cache.endpoint_cache(
    id='budget-detail',
    path=lambda instance: reverse(
        'budget:budget-detail', kwargs={'pk': instance.pk})
)
