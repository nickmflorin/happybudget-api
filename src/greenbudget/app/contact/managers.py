from greenbudget.app import signals
from greenbudget.app.tabling.managers import RowManager

from .cache import user_contacts_cache


class ContactManager(RowManager):
    @signals.disable()
    def bulk_delete(self, instances):
        users = set([obj.created_by for obj in instances])
        for obj in instances:
            obj.delete()
        for user in users:
            user_contacts_cache.invalidate(user)

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        users = set([obj.created_by for obj in instances])
        updated = self.bulk_update(instances, tuple(update_fields))
        for user in users:
            user_contacts_cache.invalidate(user)
        return updated

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)
        users = set([obj.created_by for obj in created])
        for user in users:
            user_contacts_cache.invalidate(user)
        return created
