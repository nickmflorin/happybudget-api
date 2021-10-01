import datetime
import logging

from django import dispatch

from greenbudget.app import signals

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.actual.models import Actual
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import Budget


logger = logging.getLogger('signals')


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True
)
def mark_budget_updated(instance):
    logger.info(
        "Marking Budget %s Updated at %s"
        % (instance.pk, datetime.datetime.now())
    )
    instance.save(update_fields=['updated_at'])
    instance.clear_flag('suppress_budget_update')


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True
)
def estimate_budget(instance):
    instance.estimate()
    instance.save(
        update_fields=list(instance.CALCULATED_FIELDS),
        suppress_budget_update=True
    )


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True
)
def actualize_budget(instance):
    instance.actualize()
    logger.info(
        "Updating %s %s -> Actual: %s"
        % (type(instance).__name__, instance.pk, instance.actual)
    )
    instance.save(update_fields=['actual'], suppress_budget_update=True)


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    side_effect=lambda instance: [
        signals.SideEffect(
            func=estimate_budget,
            args=(instance, )
        ),
        signals.SideEffect(
            func=actualize_budget,
            args=(instance, ),
            conditional=isinstance(instance, Budget)
        )
    ]
)
def calculate_budget(instance):
    pass


@dispatch.receiver(signals.post_save, sender=BudgetAccount)
@dispatch.receiver(signals.post_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_save, sender=TemplateAccount)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccount)
@dispatch.receiver(signals.post_save, sender=Fringe)
@dispatch.receiver(signals.post_save, sender=Actual)
@dispatch.receiver(signals.post_save, sender=Group)
@dispatch.receiver(signals.post_save, sender=Markup)
@signals.suppress_signal('suppress_budget_update')
def update_budget_updated_at(instance, **kwargs):
    mark_budget_updated(instance.budget)
