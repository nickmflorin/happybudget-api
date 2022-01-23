from greenbudget.lib.django_utils.urls import lazy_reverse
from greenbudget.app import cache


user_contacts_cache = cache.endpoint_cache(
    id='contact',
    path=lazy_reverse('contact:contact-list')
)
