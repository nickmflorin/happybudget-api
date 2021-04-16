import importlib

from rest_framework import serializers


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


class CannotExpandField(Exception):
    def __init__(self, field):
        message = "The field %s cannot be expanded" % field
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

    def _import_serializer_cls(self, module_path):
        module_name = ".".join(module_path.split(".")[:-1])
        class_name = module_path.split(".")[-1]
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def _configure_serializer_cls(self, value):
        if isinstance(value, str):
            cls = self._import_serializer_cls(value)
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
        instance_type = getattr(instance, "type", None)
        if isinstance(config, (list, tuple)):
            if len(config) != 1 and len(config) != 2 and len(config) != 3:
                raise Exception("Invalid choice provided.")
            serializer_cls = self._configure_serializer_cls(config[0])
            if len(config) == 2:
                if type(config[1]) is dict:
                    options = config[1]
                else:
                    assert type(config[1]) is str, "Invalid choice."
                    instance_type = config[1]
            elif len(config) == 3:
                assert type(config[1]) is str, "Invalid choice."
                assert type(config[2]) is dict, \
                    "Serializer keyword arguments must be a dict."
                instance_type = config[1]
                options = config[2]
        else:
            serializer_cls = self._configure_serializer_cls(config[0])

        data = serializer_cls(instance, **options).data
        data["type"] = instance_type
        return data


class EnhancedModelSerializer(serializers.ModelSerializer):
    """
    An extremely powerful extension of Django REST Framework's
    :obj:`serializers.ModelSerializer` that provides additional useful behavior
    for constructing tailored responses to fit the needs of the application.

    The :obj:`EnhancedModelSerializer` provides (4) implementations that can
    be used to fine tune the behavior of a single serializer to fit multiple
    different use cases.  These implementations are:

    (1) HTTP Field Toggling
    -----------------------
    This implementation allows the definitions of already defined fields on
    the serializer to change depending on the context's HTTP request method
    that the serializer is being used for.

    This is extremely important when we want to use the same serializer for
    both read/write operations where the serializer has foreign key or M2M
    relationships.

    The behavior toggling can be defined by including a `http_toggle`
    :obj:`dict` on the serializer's Meta class which instructs the serializer
    how to change field behavior for the provided HTTP methods.

    Example:
    ~~~~~~~
    Let's assume with have a model `Child` and a model `Parent`, where `Child`
    points to `Parent` by the means of a `ForeignKey` relationship:

        class Child(db.Model):
            name = models.CharField()
            parent = models.ForeignKey(to=Parent, reverse_name="children")

        class Parent(db.Model):
            name = models.CharField()

    Now, when we are sending PATCH/POST requests to either update a `Child`
    instance or create a new `Child` instance, it is useful to specify the
    `Parent` instance by it's Primary Key:

        Request: POST "/children" { "parent": 1, "name": "Jack" }
        Response: 201 {"parent": 1, "name": "Jack"}

    However, when we want to send a GET request to either list all the instances
    of `Child` or a single instance of `Child`, we want the parent to be
    represented by a nested serializer.

    This toggling can be accomplished by specifying the `http_toggle` attribute
    on the associated serializer's Meta class to toggle the field to another
    definition on specific HTTP requests:

        class ParentSerializer(serializers.Serializer):
            name = serializers.CharField()

            class Meta:
                model = Parent
                fields = ('id', 'name')

        class ChildSerializer(EnhancedModelSerializer):
            name = serializers.CharField()
            parent = ParentSerializer()

            class Meta:
                model = Child
                http_toggle = {
                    'parent': {
                        ('POST', 'PATCH'):  (
                            serializers.PrimaryKeyRelatedField,
                            {"queryset": Parent.objects.all()}'
                        )
                    }
                }

    Now, when we send a POST/PATCH request to the endpoints associated with
    the `Child` model, we can specify the `Parent` by it's primary key - but
    still get the full serialized `Parent` on GET requests.

    (2) Explicit Field Expansion
    ----------------------------
    This implementation allows fields to be toggled in the presence of an
    `expand` argument supplied to the serializer's __init__ method.

    Example:
    ~~~~~~~
    Returning to the above example, suppose that we want the default field
    definition for `parent` on the `ChildSerializer` to be a
    :obj:`serializers.PrimaryKeyRelatedField`, but want to use the nested
    `ParentSerializer` in certain situations.

    This toggling can be accomplished by specifying the `expand` attribute on
    the associated serializer's Meta class to expand the field by using a new
    field definition when the `expand=True` argument is supplied to the
    serializer.

        class ParentSerializer(serializers.Serializer):
            name = serializers.CharField()

            class Meta:
                model = Parent
                fields = ('id', 'name')

        class ChildSerializer(EnhancedModelSerializer):
            name = serializers.CharField()
            parent = serializers.PrimaryKeyRelatedField(
                queryset=Parent.objects.all(),
            )

            class Meta:
                model = Child
                expand = {
                    'parent': ParentSerializer
                }

    Now, when we reference the serializer as `ChildSerializer(expand=True)`,
    the expanded fields will be used in place of the default fields.

        class SchoolSerializer(serializers.ModelSerializer):
            children = ChildSerializer(many=True, expand=True)

            class Meta:
                model = School

    Note that we can also expand explicit fields, as shown here:

        class SchoolSerializer(serializers.ModelSerializer):
            children = ChildSerializer(many=True, expand=['parent'])

            class Meta:
                model = School

    (3) Field Response Rendering
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

        class ChildSerializer(EnhancedModelSerializer):
            name = serializers.CharField()
            parent = ParentSerializer()

            class Meta:
                model = Child
                http_toggle = {
                    'parent': {
                        ('POST', 'PATCH'):  (
                            serializers.PrimaryKeyRelatedField,
                            {"queryset": Parent.objects.all()}'
                        )
                    }
                }
                response = {
                    'parent': ParentSerializer
                }

    Now, all responses will include the full serialized `Parent` instance, while
    we can still reference the `Parent` instance by PK for POST and PATCH
    requests.

    (4) Explicit Field Nesting
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

        class ChildSerializer(EnhancedModelSerializer):
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

    TODO:
    ----
    While this serializer class is wildly useful, it's API can be improved
    substantially.
    """

    def __init__(self, *args, **kwargs):
        self._response = kwargs.pop('response', False)
        self._nested = kwargs.pop('nested', False)

        self._expand = kwargs.pop('expand', [])
        if not isinstance(self._expand, (bool, list, tuple)):
            raise InvalidValue('expand', expected_type=(bool, list, tuple))

        super().__init__(*args, **kwargs)

        # Fields that depend on HTTP methods have the lowest precedence.
        toggle_when_nested = getattr(
            self.Meta, 'http_toggle_when_nested', False)
        if (hasattr(self.Meta, 'http_toggle')
                and (self._nested is False or toggle_when_nested)):
            if not isinstance(self.Meta.http_toggle, dict):
                raise InvalidMetaValue('http_toggle', expected_type=dict)

            for field, config in self.Meta.http_toggle.items():
                if not isinstance(config, dict):
                    raise InvalidMetaValue(
                        'http_toggle.<value>', expected_type=dict)

                if field not in self.fields:
                    raise MissingSerializerField(field)

                if self.context_request_method is not None:
                    definition = None
                    for k, v in config.items():
                        if isinstance(k, tuple):
                            if self.context_request_method.lower() in [
                                    n.lower() for n in k]:
                                definition = v
                                break
                        elif isinstance(k, str):
                            if self.context_request_method.lower() == k.lower():
                                definition = v
                                break
                        else:
                            raise InvalidValue(
                                'http_toggle.<field>.<key>',
                                expected_type=(tuple, str)
                            )
                    if definition is not None:
                        self.fields[field] = self._instantiate_field(definition)

        # Fields that are explicitly used to render responses take precedence
        # over HTTP toggled field behaviors - but not behaviors that are
        # controlled on instantiation of the serializer (collapsing, expanding,
        # nesting).
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

        # If fields are explicitly expanded, they take precedence over the
        # field behavior defined that is dependent on the HTTP request
        # method and field behavior that is defined from nesting.
        expandable = getattr(self.Meta, 'expand', {})
        if not isinstance(expandable, dict):
            raise InvalidMetaValue('expand', expected_type=dict)

        if (self._expand is True
                or (isinstance(self._expand, (tuple, list))
                    and len(self._expand) != 0)):
            for k, v in expandable.items():
                if k not in self.fields:
                    raise MissingSerializerField(k)
                if isinstance(self._expand, bool):
                    if self._expand is True:
                        self.fields[k] = self._instantiate_field(v)
                elif k in self._expand:
                    self.fields[k] = self._instantiate_field(v)

    def _import_serializer_cls(self, module_path):
        module_name = ".".join(module_path.split(".")[:-1])
        class_name = module_path.split(".")[-1]
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def _instantiate_field(self, definition):
        # In the case that the serializer is provided by it's module path,
        # to avoid circular imports, this method will dynamically import that
        # serializer.
        if not isinstance(definition, (list, tuple)):
            serializer_cls = definition
            if isinstance(definition, str):
                serializer_cls = self._import_serializer_cls(definition)
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
                serializer_cls = self._import_serializer_cls(definition[0])
            return serializer_cls(**definition[1])

    @property
    def context_request_method(self):
        if 'request' in self.context:
            return self.context['request'].method
        return None

    def to_representation(self, instance):
        if not self._response and getattr(self.Meta, 'response', {}):
            serializer = self.__class__(
                instance,
                response=True,
                nested=self._nested,
                expand=self._expand,
                context=self.context,
            )
            return serializer.data
        return super().to_representation(instance)
