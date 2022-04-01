from rest_framework import serializers


class SerializerMixin:
    @property
    def request(self):
        assert 'request' in self.context, \
            "The request must be provided in context when using the " \
            f"{self.__class__.__name__} serializer class."
        return self.context['request']

    @property
    def user(self):
        return self.request.user


class Serializer(SerializerMixin, serializers.Serializer):
    pass


class ModelSerializer(SerializerMixin, serializers.ModelSerializer):
    pass
