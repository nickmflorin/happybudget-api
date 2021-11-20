from greenbudget.lib.django_utils.cache import instance_cache, invariant_cache
from greenbudget.app.budget.cache import budget_actuals_owner_tree_cache


subaccount_subaccounts_cache = instance_cache(
    id='subaccount-subaccounts',
    entity='children',
    method='list',
    dependencies=[budget_actuals_owner_tree_cache]
)

subaccount_markups_cache = instance_cache(
    id='subaccount-markups',
    entity='markup',
    method='list',
    dependencies=[budget_actuals_owner_tree_cache]
)

subaccount_groups_cache = instance_cache(
    id='subaccount-groups',
    entity='group',
    method='list'
)

subaccount_units_cache = invariant_cache(method='list')

subaccount_instance_cache = instance_cache(
    id='subaccount-detail',
    entity='detail',
    method='retrieve',
    dependencies=[budget_actuals_owner_tree_cache]
)
