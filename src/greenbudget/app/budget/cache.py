from django.urls import reverse

from greenbudget.app import cache


budget_children_cache = cache.endpoint_cache(
    id='budget-children',
    path=cache.ConditionalPath(conditions=[
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'template',
            path=lambda instance: reverse(
                'template:child-list', kwargs={'template_pk': instance.pk})
        ),
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'budget',
            path=lambda instance: reverse(
                'budget:child-list', kwargs={'budget_pk': instance.pk})
        )
    ])
)


budget_groups_cache = cache.endpoint_cache(
    id='budget-group',
    path=cache.ConditionalPath(conditions=[
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'template',
            path=lambda instance: reverse(
                'template:group-list', kwargs={'template_pk': instance.pk})
        ),
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'budget',
            path=lambda instance: reverse(
                'budget:group-list', kwargs={'budget_pk': instance.pk})
        )
    ])
)

budget_markups_cache = cache.endpoint_cache(
    id='budget-markup',
    path=cache.ConditionalPath(conditions=[
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'template',
            path=lambda instance: reverse(
                'template:markup-list', kwargs={'template_pk': instance.pk})
        ),
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'budget',
            path=lambda instance: reverse(
                'budget:markup-list', kwargs={'budget_pk': instance.pk})
        )
    ])
)

budget_fringes_cache = cache.endpoint_cache(
    id='budget-fringe',
    path=cache.ConditionalPath(conditions=[
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'template',
            path=lambda instance: reverse(
                'template:fringe-list', kwargs={'template_pk': instance.pk})
        ),
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'budget',
            path=lambda instance: reverse(
                'budget:fringe-list', kwargs={'budget_pk': instance.pk})
        )
    ])
)

budget_actuals_cache = cache.endpoint_cache(
    id='budget-actual',
    path=lambda instance: reverse(
        'budget:actual-list', kwargs={'budget_pk': instance.pk})
)

budget_actuals_owners_cache = cache.endpoint_cache(
    id='budget-actuals-owners',
    path=lambda instance: reverse(
        'budget:actual-owner-list', kwargs={'budget_pk': instance.pk})
)

budget_instance_cache = cache.endpoint_cache(
    id='budget-detail',
    path=cache.ConditionalPath(conditions=[
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'template',
            path=lambda instance: reverse(
                'template:template-detail', kwargs={'pk': instance.pk})
        ),
        cache.PathConditional(
            condition=lambda instance: instance.domain == 'budget',
            path=lambda instance: reverse(
                'budget:budget-detail', kwargs={'pk': instance.pk})
        )
    ])
)
