import datetime
import logging
from celery import current_app

from .models import Attachment


logger = logging.getLogger('greenbudget')


@current_app.task
def find_and_delete_empty_attachments():
    """
    Removes any any stale :obj:`Attachment`(s) that are still lingering in the
    database that are not related to a :obj:`Contact`, :obj:`Actual` or
    :obj:`BudgetSubAccount` anymore.

    When the :obj:`Attachment`(s) associated with a :obj:`Contact`,
    :obj:`Actual` or :obj:`BudgetSubAccount` are altered, it may lead to
    a :obj:`Attachment` no longer being associated with any of the related
    models.

    While this behavior is encapsulated via signals and manager methods, if
    there was ever an error there may be a stale empty :obj:`Attachment`
    floating around - which is handled by this task.

    Note:
    ----
    Due to ManyToMany relationships pointing to an :obj:`Attachment`, whenever
    a :obj:`Attachment` is uploaded for a :obj:`Contact`, :obj:`Actual` or
    :obj:`BudgetSubAccount` the :obj:`Attachment` must first be created without
    any relationships before it is assigned.

    This means that there is a small window of time where the :obj:`Attachment`
    is not related to another model, but should not be deleted by this task.
    For this reason, we only remove lingering :obj:`Attachment`(s) that were
    created some time ago (5 minutes).
    """
    logger.info(
        "Searching for empty attachments that were not previously deleted.")

    attachment_qs = Attachment.objects.empty().filter(
        created_at__gt=datetime.datetime.now() - datetime.timedelta(minutes=5))
    if attachment_qs.count() != 0:
        logger.warning(
            f"Found {attachment_qs.count()} empty Attachment(s) in DB, "
            "they will be deleted."
        )
        attachment_qs.delete(force_ignore_signal_user=True)
    else:
        logger.info("No empty attachments to delete.")
