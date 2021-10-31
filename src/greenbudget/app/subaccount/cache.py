from greenbudget.lib.django_utils.cache import detail_cache


subaccount_subaccounts_cache = detail_cache(
    id='subaccount-subaccounts',
    entity='children',
    prefix='subaccount-subaccounts',
    method='list'
)

subaccount_markups_cache = detail_cache(
    id='subaccount-markups',
    entity='markup',
    prefix='subaccount-markups',
    method='list'
)

subaccount_groups_cache = detail_cache(
    id='subaccount-groups',
    entity='group',
    prefix='subaccount-groups',
    method='list'
)

subaccount_detail_cache = detail_cache(
    id='subaccount-detail',
    entity='detail',
    prefix='subaccount-detail',
    method='retrieve'
)
