from django.contrib.contenttypes.models import ContentType

from happybudget.app import managers, query


class ColorQuerier:
    def for_model(self, model):
        content_type = ContentType.objects.get_for_model(model)
        return self.filter(content_types=content_type)

    def for_instance(self, instance):
        return self.for_model(type(instance))


class ColorQuery(ColorQuerier, query.QuerySet):
    pass


class ColorManager(ColorQuerier, managers.Manager):
    queryset_class = ColorQuery
