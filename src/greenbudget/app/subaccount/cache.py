from greenbudget.lib.django_utils.cache import instance_cache, invariant_cache


subaccount_subaccounts_cache = instance_cache(
    entity='children',
    method='list',
)

subaccount_markups_cache = instance_cache(
    entity='markup',
    method='list',
)

subaccount_groups_cache = instance_cache(
    entity='group',
    method='list'
)

subaccount_units_cache = invariant_cache(method='list')

subaccount_instance_cache = instance_cache(
    entity='detail',
    method='retrieve',
)
