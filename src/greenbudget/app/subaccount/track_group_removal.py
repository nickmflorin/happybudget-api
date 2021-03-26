import logging

from django.db.models.signals import post_init


logger = logging.getLogger('greenbudget')


def track_group_removal(field_name='group'):
    """
    Tracks the removal of a field on a :obj:`django.db.models.Model`
    corresponding to a :obj:`SubAccountGroup` so that the :obj:`SubAccountGroup`
    can be deleted if it is disassociated from the instance and has no other
    children.

    Usage:
    -----

    >>> @track_group_removal()
    >>> class SubAccount(db.Model):
    >>>     group = models.ForeignKey(to='subaccount.SubAccountGroup')

    >>> group = SubAccountGroup.objects.create()
    >>> subaccount = SubAccount.objects.create(group=group)
    >>> subaccount.group = None
    >>> subaccount.save()
    >>> SubAccountGroup.objects.first()
    >>> None

    Note:
    ----
    IMPORTANT: Since the Django `save` method is not called when a model
    is updated (i.e. Model.objects.filter().update()) - this will not work.
    Unfortunately, since the .update() method is so close to the SQL layer,
    there really isn't a way in Django to avoid this.
    """

    def _store(self):
        if self.id:
            self.__previous_group = getattr(self, field_name)

    def inner(cls):
        # Contains a local copy of the previous group.
        cls.__previous_group = None

        def save(self, *args, **kwargs):
            """
            Overrides the :obj:`django.db.models.Model` save behavior to
            remove the :obj:`SubAccountGroup` if it is disassociated from
            the instance and does not have any children after the
            disassociation.
            """
            if self.__previous_group is not None and self.group is None:
                lookup = {field_name: self.__previous_group}
                if cls.objects.filter(**lookup).count() == 1:
                    logger.info(
                        "Deleting group %s after it was removed from %s %s "
                        "because the group has no other children."
                        % (self.__previous_group.id, cls.__name__, self.id)
                    )
                    self.__previous_group.delete()

            save._original(self, *args, **kwargs)
            _store(self)

        def _post_init(sender, instance, **kwargs):
            _store(instance)

        post_init.connect(_post_init, sender=cls, weak=False)

        # Replace the model save method with the overridden one, but keep track
        # of the original save method so it can be reapplied.
        save._original = cls.save
        cls.save = save
        return cls

    return inner
