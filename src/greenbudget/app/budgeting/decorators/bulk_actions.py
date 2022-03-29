from typing import Any

from greenbudget.app.constants import ActionName


class BaseBulkAction:
    """
    Abstract base class for the configuration of a bulk operation, whether it
    be the configuration of bulk create behavior, bulk delete beahvior or bulk
    update behavior.
    """
    def __init__(self, url_path: str, filter_qs: Any = None,
            name: Any = None, entity: Any = None):
        self._url_path = url_path
        self.filter_qs = filter_qs
        self._name = name
        self.entity = entity

    def url_path(self, registrar):
        url_path = self._url_path
        if '{action_name}' in url_path and '{entity}' in url_path:
            url_path = url_path.format(
                action_name=registrar.action_name,
                entity=self.entity
            )
        elif '{action_name}' in url_path:
            url_path = url_path.format(action_name=registrar.action_name)
        elif '{entity}' in url_path and self.entity is not None:
            url_path = url_path.format(entity=self.entity)
        return url_path

    def name(self, registrar):
        return self._name or self.url_path(registrar).replace('-', '_')


class BulkDeleteAction(BaseBulkAction):
    """
    Configuration for bulk delete behavior.
    """
    action_names = [ActionName.DELETE]

    def __init__(self, url_path: str, child_cls: type, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        self._init(child_cls, **kwargs)

    def _init(self, child_cls: type, **kwargs):
        self.child_cls = child_cls
        self.perform_destroy = kwargs.get('perform_destroy', None)


class BulkCreateAction(BaseBulkAction):
    """
    Configuration for bulk create behavior.
    """
    action_names = [ActionName.CREATE]

    def __init__(self, url_path, child_serializer_cls, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        self._init(child_serializer_cls, **kwargs)

    def _init(self, child_serializer_cls, **kwargs):
        self.child_serializer_cls = child_serializer_cls
        self.child_context = kwargs.get('child_context')
        self.perform_create = kwargs.get('perform_create', None)


class BulkUpdateAction(BaseBulkAction):
    """
    Configuration for bulk update behavior.
    """
    action_names = [ActionName.UPDATE]

    def __init__(self, url_path, child_serializer_cls, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        self._init(child_serializer_cls, **kwargs)

    def _init(self, child_serializer_cls, **kwargs):
        self.child_serializer_cls = child_serializer_cls
        self.child_context = kwargs.get('child_context')
        self.perform_update = kwargs.get('perform_update', None)


class BulkAction(BaseBulkAction):
    """
    Configuration for multiple bulk behaviors.
    """
    action_names = ActionName.__all__

    def __init__(self, url_path, child_cls, child_serializer_cls, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        BulkDeleteAction._init(self, child_cls, **kwargs)
        BulkCreateAction._init(self, child_serializer_cls, **kwargs)
        BulkUpdateAction._init(self, child_serializer_cls, **kwargs)
