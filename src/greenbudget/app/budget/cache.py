from greenbudget.lib.django_utils.cache import instance_cache


budget_accounts_cache = instance_cache(
    entity='children',
    method='list'
)

budget_groups_cache = instance_cache(
    entity='group',
    method='list'
)

budget_actuals_cache = instance_cache(
    entity='actual',
    method='list'
)

budget_actuals_owner_tree_cache = instance_cache(
    entity='actuals-owner',
    method='tree'
)

budget_markups_cache = instance_cache(
    entity='markup',
    method='list'
)

budget_fringes_cache = instance_cache(
    entity='fringe',
    method='list'
)

budget_instance_cache = instance_cache(
    entity='detail',
    method='retrieve'
)
