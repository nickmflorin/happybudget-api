from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse


def test_view(request):
    print('in view')
    return HttpResponse("Hello!")


class HarryAdminSite(admin.AdminSite):
    site_url = settings.FRONTEND_URL


site = HarryAdminSite()
