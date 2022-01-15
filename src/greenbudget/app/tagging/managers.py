from django.contrib.contenttypes.models import ContentType
from django.db import models


class ColorQuerier(object):

    def for_model(self, model):
        content_type = ContentType.objects.get_for_model(model)
        return self.filter(content_types=content_type)

    def for_instance(self, instance):
        return self.for_model(type(instance))


class ColorQuery(ColorQuerier, models.QuerySet):
    pass


class ColorManager(ColorQuerier, models.Manager):
    queryset_class = ColorQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
