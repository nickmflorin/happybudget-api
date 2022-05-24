import datetime
import logging
from celery import current_app

from .models import Group


logger = logging.getLogger('greenbudget')


@current_app.task
def find_and_delete_empty_groups():
    """
    Removes any any stale :obj:`Group`(s) that are still lingering in the
    database but do not have any associated children.

    When the children of a :obj:`Group` are altered, any :obj:`Group`(s) that
    are siblings of the altered :obj:`Group` (i.e. :obj:`Group`(s) that have
    the same parent) that no longer have any children as a result of the
    alteration are deleted.

    Example
    -------
    For example, if we have Group A with children Account 1 and Account 2, and
    Group B with children Account 3, the action of moving Account 3 into
    Group A means that Group B no longer has children, and should be deleted.

    While this behavior is encapsulated via signals and manager methods, if
    there was ever an error there may be a stale empty :obj:`Group` floating
    around - which is handled by this task.

    Note:
    ----
    Due to ForeignKey relationships pointing to a :obj:`Group`, whenever a
    new :obj:`Group` is created the :obj:`Group` must first be created without
    children before it can be assigned children.

    This means that there is a small window of time where a newly created
    :obj:`Group` will not have any children, but should not be deleted by this
    task.  For this reason, we only remove empty :obj:`Group`(s) that were
    created some time ago (5 minutes).
    """
    logger.info("Searching for empty groups that were not previously deleted.")

    cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=5)
    group_qs = Group.objects.empty().filter(created_at__lt=cutoff_time)
    if group_qs.count() != 0:
        logger.warning(
            f"Found {group_qs.count()} empty Group(s) in DB, "
            "they will be deleted."
        )
        group_qs.delete(force_ignore_signal_user=True)
    else:
        logger.info("No empty groups to delete.")
