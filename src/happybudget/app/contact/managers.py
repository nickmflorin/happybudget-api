from happybudget.app import signals
from happybudget.app.tabling.managers import OrderedRowManager

from .cache import user_contacts_cache
from .query import ContactQuerySet


class ContactManager(OrderedRowManager):
    queryset_class = ContactQuerySet

    @signals.disable()
    def bulk_delete(self, instances, request=None):
        for obj in instances:
            obj.delete()
        user_contacts_cache.invalidate()

    @signals.disable()
    def bulk_save(self, instances, update_fields, request=None):
        updated = self.bulk_update(instances, tuple(update_fields))
        user_contacts_cache.invalidate()
        return updated

    @signals.disable()
    def bulk_add(self, instances, request=None):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)
        user_contacts_cache.invalidate()
        return created
