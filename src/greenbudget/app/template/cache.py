from django.urls import reverse

from greenbudget.app import cache


template_accounts_cache = cache.endpoint_cache(
    id='children',
    path=lambda instance: reverse(
        'template:account-list', kwargs={'template_pk': instance.pk})
)

template_groups_cache = cache.endpoint_cache(
    id='group',
    path=lambda instance: reverse(
        'template:group-list', kwargs={'template_pk': instance.pk})
)

template_markups_cache = cache.endpoint_cache(
    id='markup',
    path=lambda instance: reverse(
        'template:markup-list', kwargs={'template_pk': instance.pk})
)

template_fringes_cache = cache.endpoint_cache(
    id='fringe',
    path=lambda instance: reverse(
        'template:fringe-list', kwargs={'template_pk': instance.pk})
)


def template_instance_cache_dependency(instance):
    template_accounts_cache.invalidate(instance)


template_instance_cache = cache.endpoint_cache(
    id='detail',
    dependency=template_instance_cache_dependency,
    path=lambda instance: reverse(
        'template:template-detail', kwargs={'pk': instance.pk})
)
