from django.contrib.admin.apps import AdminConfig


class HarryAdminConfig(AdminConfig):
    default_site = 'happybudget.harry.site.HarryAdminSite'
