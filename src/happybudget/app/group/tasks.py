import logging
from celery import current_app

from .models import Group


logger = logging.getLogger('greenbudget')


@current_app.task
def find_and_delete_empty_groups():
    logger.info("Searching for empty groups that were not previously deleted.")
    if Group.objects.empty().count() != 0:
        logger.warning(
            f"Found {Group.objects.empty().count()} empty Group(s) in DB, "
            "they will be deleted."
        )
        Group.objects.empty().delete(force_ignore_signal_user=True)
    else:
        logger.info("No empty groups to delete.")
