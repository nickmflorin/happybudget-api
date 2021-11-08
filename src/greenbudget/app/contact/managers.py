from django.db import models

from greenbudget.lib.django_utils.models import PrePKBulkCreateQuerySet

from greenbudget.app import signals

from .cache import user_contacts_cache


class ContactQuerySet(PrePKBulkCreateQuerySet):
    pass


class ContactManager(models.Manager):
    queryset_class = ContactQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)

    @signals.disable()
    def bulk_delete(self, instances):
        users = set([obj.user for obj in instances])
        for obj in instances:
            obj.delete()
        for user in users:
            user_contacts_cache.invalidate(user)

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        users = set([obj.user for obj in instances])
        updated = self.bulk_update(instances, tuple(update_fields))
        for user in users:
            user_contacts_cache.invalidate(user)
        return updated

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)
        users = set([obj.user for obj in created])
        for user in users:
            user_contacts_cache.invalidate(user)
        return created
