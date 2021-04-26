from django.apps import apps


class AbstractManagerOperationMixin:

    def _get_model_definition_cls(self, attr):
        assert getattr(self, attr, None) is not None, \
            "The manager %s must define the `%s` attribute if "\
            "using the %s mixin." % (
                self.__class__.__name__,
                attr,
                AbstractManagerOperationMixin.__name__
        )
        model_cls = getattr(self, attr)
        if isinstance(model_cls, str):
            try:
                return apps.get_model(
                    app_label=model_cls.split('.')[0],
                    model_name=model_cls.split('.')[1]
                )
            except IndexError:
                raise LookupError('Invalid `%s`: %s.' % (attr, model_cls))
        return model_cls


def ModelTemplateManager(*bases):
    class FromTemplateManager(*bases, AbstractManagerOperationMixin):
        def create_from_template(self, template, *args, **kwargs):
            assert hasattr(self.model, 'MAP_FIELDS_FROM_TEMPLATE'), \
                "The model %s must define the `MAP_FIELDS_FROM_TEMPLATE`." \
                % self.model.__name__

            for field in getattr(self.model, 'MAP_FIELDS_FROM_TEMPLATE'):
                if field not in kwargs:
                    kwargs[field] = getattr(template, field)
            return super().create(*args, **kwargs)

        def create(self, *args, **kwargs):
            if 'template' in kwargs:
                template = kwargs.pop('template')
                template_cls = self._get_model_definition_cls('template_cls')
                assert isinstance(template, template_cls), \
                    "When creating %s from a template model, the template " \
                    "model must be of type %s." \
                    % (self.model.__name__, type(template_cls))
                return self.create_from_template(template, *args, **kwargs)
            return super().create(*args, **kwargs)

    return FromTemplateManager


def ModelDuplicateManager(*bases):
    class FromCopyManager(*bases, AbstractManagerOperationMixin):
        def create_duplicate(self, original, *args, **kwargs):
            assert hasattr(self.model, 'MAP_FIELDS_FROM_ORIGINAL'), \
                "The model %s must define the `MAP_FIELDS_FROM_ORIGINAL`." \
                % self.model.__name__

            for field in getattr(self.model, 'MAP_FIELDS_FROM_ORIGINAL'):
                if field not in kwargs:
                    kwargs[field] = getattr(original, field)
            return super().create(*args, **kwargs)

        def create(self, *args, **kwargs):
            if 'original' in kwargs:
                original = kwargs.pop('original')
                assert isinstance(original, self.model), \
                    "When duplicating %s from an original, the original model" \
                    "must be of type %s." \
                    % (self.model.__name__, type(self.model))
                return self.create_duplicate(original, *args, **kwargs)
            return super().create(*args, **kwargs)

    return FromCopyManager
