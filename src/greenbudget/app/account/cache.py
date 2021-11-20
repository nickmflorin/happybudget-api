from greenbudget.lib.django_utils.cache import instance_cache
from greenbudget.app.budget.cache import budget_actuals_owner_tree_cache

account_subaccounts_cache = instance_cache(
    id='account-subaccounts',
    entity='children',
    method='list'
)

account_markups_cache = instance_cache(
    id='account-markups',
    entity="markup",
    method='list',
    dependencies=[budget_actuals_owner_tree_cache]
)

account_groups_cache = instance_cache(
    id='account-groups',
    entity='group',
    method='list'
)

account_instance_cache = instance_cache(
    id='account-detail',
    entity='detail',
    method='retrieve'
)
