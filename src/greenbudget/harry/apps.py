from django.contrib.admin.apps import AdminConfig


class HarryAdminConfig(AdminConfig):
    default_site = 'greenbudget.harry.site.HarryAdminSite'
