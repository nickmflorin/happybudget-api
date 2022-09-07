from happybudget.app import managers
from .query import AttachmentQuerier, AttachmentQuerySet


class AttachmentManager(AttachmentQuerier, managers.Manager):
    queryset_class = AttachmentQuerySet
