from greenbudget.lib.django_utils.cache import detail_cache


budget_accounts_cache = detail_cache(
    id='budget-accounts',
    entity='children',
    prefix='budget-accounts',
    method='list'
)

budget_markups_cache = detail_cache(
    id='budget-markups',
    entity='markup',
    prefix='budget-markups',
    method='list'
)

budget_groups_cache = detail_cache(
    id='budget-groups',
    entity='group',
    prefix='budget-groups',
    method='list'
)

budget_actuals_cache = detail_cache(
    id='budget-actuals',
    entity='actual',
    prefix='budget-actuals',
    method='list'
)

budget_fringes_cache = detail_cache(
    id='budget-fringes',
    entity='fringe',
    prefix='budget-fringes',
    method='list'
)

budget_detail_cache = detail_cache(
    id='budget-detail',
    entity='detail',
    prefix='budget-detail',
    method='retrieve'
)
