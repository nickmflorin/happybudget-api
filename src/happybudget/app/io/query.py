from happybudget.app import query
from happybudget.app.user.query import ModelOwnershipQuerier


class AttachmentQuerier(ModelOwnershipQuerier):
    def empty(self):
        m2m_related_fields = [
            related.get_accessor_name()
            for related in self.model._meta.related_objects
        ]
        return self.filter(**{name: None for name in m2m_related_fields})


class AttachmentQuerySet(query.QuerySet, AttachmentQuerier):
    pass
