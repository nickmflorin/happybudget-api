from django.db import models

from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer as create_generic_bulk_create_serializer,
    create_bulk_update_serializer as create_generic_bulk_update_serializer,
    create_bulk_delete_serializer as create_generic_bulk_delete_serializer
)
from .models import Contact
from .serializers import ContactSerializer


def create_bulk_delete_serializer(user):
    generic_serializer_cls = create_generic_bulk_delete_serializer(
        child_cls=Contact,
        filter_qs=models.Q(user=user)
    )

    class BulkDeleteSerializer(generic_serializer_cls):
        # Note: We have to use the .save() method instead of .update() or
        # .create() because this is not a ModelSerializer - the .update() or
        # .create() methods must return an instance, which is not applicable
        # here.
        def save(self):
            for child in self.validated_data['ids']:
                child.delete()

    return BulkDeleteSerializer


def create_bulk_create_serializer():
    generic_serializer_cls = create_generic_bulk_create_serializer(
        serializer_cls=ContactSerializer,
        child_cls=Contact
    )

    class BulkCreateSerializer(generic_serializer_cls):
        # Note: We have to use the .save() method instead of .update() or
        # .create() because this is not a ModelSerializer - the .update() or
        # .create() methods must return an instance, which is not applicable
        # here.
        def save(self, **kwargs):
            data = [payload for payload in self.validated_data.pop('data', [])]
            children = self.perform_children_write(data, **kwargs)
            return children

    return BulkCreateSerializer


def create_bulk_update_serializer(user):
    generic_serializer_cls = create_generic_bulk_update_serializer(
        child_cls=Contact,
        serializer_cls=ContactSerializer,
        filter_qs=models.Q(user=user)
    )

    class BulkUpdateSerializer(generic_serializer_cls):
        # Note: We have to use the .save() method instead of .update() or
        # .create() because this is not a ModelSerializer - the .update() or
        # .create() methods must return an instance, which is not applicable
        # here.
        def save(self):
            data = self.validated_data.pop('data', [])
            for child, change in data:
                # At this point, the change already represents the
                # validated data for that specific serializer.  So we do
                # not need to pass in the validated data on __init__
                # and rerun validation.
                serializer = ContactSerializer(partial=True)
                serializer.update(child, {**self.validated_data, **change})

    return BulkUpdateSerializer
