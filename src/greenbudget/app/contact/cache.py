from greenbudget.lib.django_utils.cache import detail_cache


user_contacts_cache = detail_cache(
    id='user-contacts',
    entity='contact',
    prefix='user-contacts',
    method='list'
)
