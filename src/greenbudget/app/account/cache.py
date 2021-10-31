from greenbudget.lib.django_utils.cache import detail_cache


account_subaccounts_cache = detail_cache(
    id='account-subaccounts',
    entity='children',
    prefix='account-subaccounts',
    method='list'
)

account_markups_cache = detail_cache(
    id='account-markups',
    entity="markup",
    prefix='account-markups',
    method='list'
)

account_groups_cache = detail_cache(
    id='account-groups',
    entity='groups',
    prefix='account-groups',
    method='list'
)

account_detail_cache = detail_cache(
    id='account-detail',
    entity='detail',
    prefix='account-detail',
    method='retrieve'
)
