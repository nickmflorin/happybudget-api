from greenbudget.lib.django_utils.cache import instance_cache


user_contacts_cache = instance_cache(
    id='user-contacts',
    entity='contact',
    method='list'
)
