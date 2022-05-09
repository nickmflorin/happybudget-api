from django.conf import settings
from django.contrib import admin


class HarryAdminSite(admin.AdminSite):
    site_url = settings.FRONTEND_URL


site = HarryAdminSite()
