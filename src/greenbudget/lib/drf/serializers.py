import collections
from rest_framework import serializers

from greenbudget.lib.utils import import_at_module_path


class LazyContext(collections.abc.Mapping):
    """
    A mapping object that wraps a serializer's context such that a more helpful
    error is raised when accessing an element of the context that is required
    but does not exist.

    This is useful for including serializer context in callback functions
    where we expect the values to be in the context but if they are not we
    need to be aware of that.
    """

    def __init__(self, obj, ref=None):
        self._ref = ref
        self._data = obj
        if isinstance(obj, (serializers.Serializer, serializers.Field)):
            self._data = getattr(obj, 'context')
            self._ref = self._ref or type(obj).__name__

    def __iter__(self):
        return self._data.__iter__()

    def field_missing_message(self, field):
        if self._ref is not None:
            return (
                "The field `%s` must be provided in context when using %s."
                % (field, self._ref)
            )
        return "The field `%s` must be provided in context." % field

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise Exception(self.field_missing_message(attr))

    def __getitem__(self, attr):
        return self._data.__getitem__(attr)

    def __setitem__(self, k, v):
        raise Exception("Cannot set a value on LazyContext.")

    def __len__(self):
        return self._data.__len__()

    def __delitem__(self, k):
        return self._data.__delitem__(k)


class InvalidValue(Exception):
    def __init__(self, ref, expected_type=None):
        message = "The value for %s is invalid." % ref
        if expected_type is not None:
            message += " Expected type or types %s." % expected_type
        super().__init__(message)


class InvalidMetaValue(Exception):
    def __init__(self, value, expected_type=None):
        message = "Invalid value for %s on the serializer's Meta class." % value
        if expected_type is not None:
            message += " Expected type or types %s." % expected_type
        super().__init__(message)


class MissingSerializerField(Exception):
    def __init__(self, field):
        message = (
            "The field %s does not exist in the list of fields available "
            "on the serializer." % field)
        super().__init__(message)


class PolymorphicNonPolymorphicSerializer(serializers.Serializer):
    """
    A :obj:`rest_framework.serializers.Serializer` uses different serializers
    depending on the instance being serialized.

    The name of this :obj:`rest_framework.serializers.Serializer` is not a joke.
    Typically, with Polymorphic serializers, the serializer will serialize
    based on the type of instance where each instance that it can serialize
    must be a child of a PolymorphicModel.  Here, we loosen that requirement,
    and allow the serializer to conditionally serialize an instance where that
    instance need not be a child of a Polymorphic model.
    """

    def _configure_serializer_cls(self, value):
        if isinstance(value, str):
            cls = import_at_module_path(value)
            return self._configure_serializer_cls(cls)
        assert issubclass(value, serializers.BaseSerializer), (
            "%s is not a serializer class or a module path to a serializer "
            "class." % value)
        return value

    def _find_config_for_instance(self, instance):
        if not hasattr(self, "choices"):
            raise Exception(
                "Extensions of PolymorphicNonPolymorphicSerializer must define "
                "a Meta attribute on the serializer with a `choices` attribute."
            )
        for k, v in self.choices.items():
            if isinstance(instance, k):
                return v
        raise Exception(
            "PolymorphicNonPolymorphicSerializer not configured to "
            "serialize type %s." % type(instance)
        )

    def to_representation(self, instance):
        config = self._find_config_for_instance(instance)

        options = {}
        if isinstance(config, (list, tuple)):
            if len(config) not in (1, 2):
                raise Exception("Invalid choice provided.")
            serializer_cls = self._configure_serializer_cls(config[0])
            if len(config) == 2:
                assert type(config[1]) is dict, \
                    "Serializer keyword arguments must be a dict."
                options = config[1]
        else:
            serializer_cls = self._configure_serializer_cls(config)

        data = serializer_cls(instance, **options).data
        return data


class ModelSerializer(serializers.ModelSerializer):
    """
    An extremely powerful extension of Django REST Framework's
    :obj:`serializers.ModelSerializer` that provides additional useful behavior
    for constructing tailored responses to fit the needs of the application.

    The :obj:`ModelSerializer` provides implementations that can
    be used to fine tune the behavior of a single serializer to fit multiple
    different use cases.  These implementations are:

    (1) Field Response Rendering
    ----------------------------
    This implementation is critically important to developing an API response
    contract that is consistent for a frontend client to use.

    Returning to the example from implementation (1), we are using a
    :obj:`serializers.PrimaryKeyRelatedField` to allow the creation/updating
    of `Child` instances referencing a `Parent` instance by it's PK.
    Implementation (1) allows us to toggle the field for read/write HTTP
    methods, but it does not allow us to render a consistent response between
    the two.

    For example, if we send a POST request to "/children" with the JSON body
    { "parent": 1, "name": "Jack" }, the response of the POST request will
    still reference the serialized form of the created `Child` as
    { "parent": 1, "name": "Jack" }.

        Request: POST "/children" { "parent": 1, "name": "Jack" }
        Response: 201 {"parent": 1, "name": "Jack"}

    If we want the full serialized parent, we have to send a GET request to
    "/children/<pk>".

    In order to render consistent responses between the GET and POST/PATCH
    methods, we can use this implementation to render the full serialized
    `Parent` on responses of POST and PATCH methods:

        Request: POST "/children" { "parent": 1, "name": "Jack" }
        Response: 201 {"parent": {"id": 1, "name": "Jack Sr." }, "name": "Jack"}

    This can be done by identifying how fields should be handled for responses
    of ALL request types by including `response` attribute on the serializer's
    Meta class.

    Example:
    ~~~~~~~
    To achieve the Request/Response pattern shown above, we can do the
    following:

        class ParentSerializer(serializers.Serializer):
            name = serializers.CharField()

            class Meta:
                model = Parent
                fields = ('id', 'name')

        class ChildSerializer(ModelSerializer):
            name = serializers.CharField()
            parent = ParentSerializer()

            class Meta:
                model = Child
                response = {
                    'parent': ParentSerializer
                }

    Now, all responses will include the full serialized `Parent` instance, while
    we can still reference the `Parent` instance by PK for POST and PATCH
    requests.

    (2) Explicit Field Nesting
    --------------------------
    This implementation allows fields to be included or excluded based on
    whether or not the serializer is nested inside of another serializer.

    With this implementation, fields that are listed by the `nested_fields`
    attribute of the serializer's Meta class will be the only fields included
    if `nested=True` is provided to the serializer on initialization.

    Example:
    ~~~~~~~
    Returning to the above example, suppose that when we send a GET to either
    "/children" or "/children/<pk>" that we want to include the full serialized
    child.  However, when we send a request to "/schools/<pk>/" or "/schools"
    we want the serialized `School` to include a condensed version of the nested
    `ChildSerializer`.

    We can accomplish this by specifying the fields that we want to use in
    a condensed form of the `ChildSerializer` by the `nested_fields` attribute
    on the serializer's Meta class:

        class ChildSerializer(ModelSerializer):
            id = serializers.IntegerField()
            first_name = serializers.CharField()
            last_name = serializers.CharField()
            email = serializers.EmailField()

            class Meta:
                model = Child
                fields = ('id', 'first_name', 'last_name', 'email')
                nested_fields = ('id', 'email')

        class ParentSerializer(serializers.ModelSerializer):
            child = ChildSerializer(nested=True)
            id = serializers.IntegerField()

            class Meta:
            fields = ('id', 'child')
    """

    def __init__(self, *args, **kwargs):
        self._response = kwargs.pop('response', False)
        self._nested = kwargs.pop('nested', False)

        super().__init__(*args, **kwargs)

        # Fields that are explicitly used to render responses take precedence
        # over HTTP toggled field behaviors - but not behaviors that are
        # controlled on instantiation of the serializer (collapsing/nesting).
        response_fields = getattr(self.Meta, 'response', {})
        if not isinstance(response_fields, dict):
            raise InvalidMetaValue('response', expected_type=dict)

        if self._response is True:
            for k, v in response_fields.items():
                if k not in self.fields:
                    raise MissingSerializerField(k)
                self.fields[k] = self._instantiate_field(v)

        # Fields that are included/excluded based on the nesting of the
        # serializer take precedence over all.
        nested_fields = getattr(self.Meta, 'nested_fields', [])
        if not isinstance(nested_fields, (list, tuple)):
            raise InvalidMetaValue(
                'nested_fields', expected_type=(list, tuple))

        if len(nested_fields) != 0 and self._nested is True:
            new_fields = {}
            for field_name in nested_fields:
                if field_name not in self.fields:
                    raise MissingSerializerField(field_name)
                new_fields[field_name] = self.fields[field_name]
            self.fields = new_fields

    def _instantiate_field(self, definition):
        # In the case that the serializer is provided by it's module path,
        # to avoid circular imports, this method will dynamically import that
        # serializer.
        if not isinstance(definition, (list, tuple)):
            serializer_cls = definition
            if isinstance(definition, str):
                serializer_cls = import_at_module_path(definition)
            return serializer_cls()
        else:
            if (len(definition) != 2
                    or not isinstance(definition[1], dict)):
                raise Exception(
                    "Could not instantiate a serializer from the provided "
                    "definition."
                )
            serializer_cls = definition[0]
            if isinstance(definition[0], str):
                serializer_cls = import_at_module_path(definition[0])
            return serializer_cls(**definition[1])

    def to_representation(self, instance):
        if not self._response and getattr(self.Meta, 'response', {}):
            serializer = self.__class__(
                instance,
                response=True,
                nested=self._nested,
                context=self.context,
            )
            return serializer.data
        return super().to_representation(instance)
