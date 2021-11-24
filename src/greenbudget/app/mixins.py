from rest_framework import mixins
from rest_framework.mixins import (  # noqa
    ListModelMixin, DestroyModelMixin, RetrieveModelMixin)


class UpdateModelMixin(mixins.UpdateModelMixin):
    def perform_update(self, serializer, **kwargs):
        return serializer.save(**self.update_kwargs(serializer), **kwargs)


class CreateModelMixin(mixins.CreateModelMixin):
    def perform_create(self, serializer, **kwargs):
        return serializer.save(**self.create_kwargs(serializer), **kwargs)
