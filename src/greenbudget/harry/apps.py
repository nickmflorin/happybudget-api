from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


# class HarryConfig(AppConfig):
#     name = 'greenbudget.harry'
#     verbose_name = "Harry"
#     default_auto_field = 'django.db.models.AutoField'


class HarryAdminConfig(AdminConfig):
    default_site = 'greenbudget.harry.site.HarryAdminSite'
