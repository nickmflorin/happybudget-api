from greenbudget.lib.django_utils.cache import instance_cache


budget_accounts_cache = instance_cache(
    id='budget-accounts',
    entity='children',
    method='list'
)

budget_groups_cache = instance_cache(
    id='budget-groups',
    entity='group',
    method='list'
)

budget_actuals_cache = instance_cache(
    id='budget-actuals',
    entity='actual',
    method='list'
)

budget_actuals_owner_tree_cache = instance_cache(
    id='budget-actuals-owner-tree',
    entity='actuals-owner',
    method='tree'
)

budget_markups_cache = instance_cache(
    id='budget-markups',
    entity='markup',
    method='list',
    dependencies=[budget_actuals_owner_tree_cache]
)

budget_fringes_cache = instance_cache(
    id='budget-fringes',
    entity='fringe',
    method='list'
)

budget_instance_cache = instance_cache(
    id='budget-detail',
    entity='detail',
    method='retrieve'
)
