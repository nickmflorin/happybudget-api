from greenbudget.lib.django_utils.cache import instance_cache


account_subaccounts_cache = instance_cache(
    entity='children',
    method='list'
)

account_markups_cache = instance_cache(
    entity="markup",
    method='list'
)

account_groups_cache = instance_cache(
    entity='group',
    method='list'
)

account_instance_cache = instance_cache(
    entity='detail',
    method='retrieve'
)
