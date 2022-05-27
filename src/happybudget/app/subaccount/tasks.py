import logging
from celery import current_app

from happybudget.lib.utils import humanize_list
from .models import SubAccount


logger = logging.getLogger('greenbudget')


@current_app.task
def fix_corrupted_fringe_relationships():
    """
    Looks for and fixes relationships between a :obj:`Fringe` and
    :obj:`SubAccount` that may have been corrupted and for whatever reason
    missed the validation that is performed in the related signal,
    :obj:`validate_fringes`.

    When a :obj:`Fringe` is associated with an :obj:`SubAccount`, the
    :obj:`Budget` that the :obj:`Fringe` belongs to and the :obj:`Budget`
    that the :obj:`SubAccount` belongs to must be consistent.  If they are
    not, this task will remove the association.
    """
    subaccounts = SubAccount.objects.exclude(fringes=None)
    disassociation_occurred = False
    for subaccount in subaccounts:
        fringes_to_remove = ()
        for fringe in subaccount.fringes.all():
            if subaccount.budget != fringe.budget:
                logger.error(
                    f"Found Fringe {fringe.pk} that belongs to Budget "
                    f"{fringe.budget.pk} - {fringe.budget.name} but also "
                    f"belongs to SubAccount {subaccount.pk} that belongs to "
                    f"Budget {fringe.budget.pk} - {fringe.budget.name}. This "
                    "relationship is corrupted, and the Fringe must be "
                    "disassociated from the SubAccount.", extra={
                        'subaccount': subaccount.pk,
                        'budget': subaccount.budget.pk,
                        'fringe': fringe.pk,
                        'fringe_budget': fringe.budget.pk
                    }
                )
                fringes_to_remove = fringes_to_remove + (fringe, )
        if fringes_to_remove:
            humanized = humanize_list(
                [fringe.pk for fringe in fringes_to_remove])
            logger.warning(
                f"Disassociating Fringes {humanized} from SubAccount "
                f"{subaccount.pk}."
            )
            disassociation_occurred = True
            subaccount.fringes.remove(*fringes_to_remove)
    if not disassociation_occurred:
        logger.info("Found no corrupted Fringe - SubAccount relationships.")
