from greenbudget.lib.utils import concat


def combine_routers(*routers):
    return concat([router.urls for router in routers])
