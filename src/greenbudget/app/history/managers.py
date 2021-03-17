from polymorphic.managers import PolymorphicManager
from django.contrib.contenttypes.models import ContentType


class EventManager(PolymorphicManager):

    def get_for_model(self, object):
        content_type = ContentType.objects.get_for_model(object)
        return self.filter(
            object_id=object.pk,
            content_type=content_type
        )


class FieldAlterationManager(EventManager):

    def get_for_model_and_field(self, object, field):
        return self.get_for_model(object).filter(field=field)
