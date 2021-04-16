import logging

from .models import Group


logger = logging.getLogger('greenbudget')


def on_group_removal(instance, data):
    if instance.__class__.objects.filter(
            group_id=data['previous_value']).count() == 0:
        logger.info(
            "Deleting group %s after it was removed from %s %s "
            "because the group has no other children."
            % (
                data['previous_value'],
                instance.__class__.__name__,
                instance.id
            )
        )
        group = Group.objects.get(pk=data['previous_value'])
        group.delete()
