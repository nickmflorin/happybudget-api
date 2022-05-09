from happybudget.lib.django_utils.urls import lazy_reverse
from happybudget.app import cache


user_contacts_cache = cache.endpoint_cache(
    cache_id='contact',
    disabled=True,
    path=lazy_reverse('contact:contact-list')
)
